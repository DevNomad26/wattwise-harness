import asyncio
import json
import os
from pathlib import Path

import pytest

from api import session as session_mod
from api.session import (
    LOGIN_RECEIVED,
    Session,
    add_send_offer,
    loop_failed_answer,
    build_prompt,
    build_trace,
    check_send_status,
    not_sent_answer,
    root_cause,
    take_email_login,
)
from mcp_servers.mailer import LOGIN_ENV

LOGIN = "smtps://asha@gmail.com:abcdefghijklmnop@smtp.gmail.com"


@pytest.fixture(autouse=True)
def no_email_login():
    """Session.ask keeps the login in os.environ; never let it leak between tests."""
    saved = os.environ.pop(LOGIN_ENV, None)
    yield
    os.environ.pop(LOGIN_ENV, None)
    if saved is not None:
        os.environ[LOGIN_ENV] = saved


class FakeAgent:
    """Mimics AgentLoop: records history, appends this turn's messages, returns an answer."""

    def __init__(self, answers=None, error=None):
        self.answers = list(answers or ["ok"])
        self.error = error
        self.calls = []

    async def run(self, prompt, scripts, history=None):
        self.calls.append({"prompt": prompt, "history": list(history or [])})
        if self.error:
            raise self.error
        answer = self.answers.pop(0)
        self.messages = [{"role": "system", "content": "sys"}, *(history or []), {"role": "user", "content": prompt},
                         {"role": "assistant", "content": json.dumps({"action": "final", "final_answer": answer})}]
        return answer


def ask(session, question, image=None):
    return asyncio.run(session.ask(question, image))


def test_build_prompt():
    assert build_prompt("Is it right?", None) == "Is it right?"
    assert build_prompt("Is it right?", Path("/b.jpg")) == "Is it right?\nThe bill photo is at: /b.jpg"


def test_root_cause_unwraps_nested_groups():
    inner = TimeoutError("read timed out")
    assert root_cause(ExceptionGroup("outer", [ExceptionGroup("inner", [inner])])) is inner
    assert root_cause(inner) is inner


def test_build_trace_pairs_tool_calls_with_results():
    messages = [
        {"role": "user", "content": "Is my bill correct?"},
        {"role": "assistant", "content": json.dumps({"action": "tool", "tool_name": "compute_bill",
                                                     "tool_args": {"units": 150, "state": "Gujarat"}, "thought": "t"})},
        {"role": "user", "content": "Tool 'compute_bill' returned:\nRs 655.25"},
        {"role": "assistant", "content": "not json"},
        {"role": "assistant", "content": json.dumps({"action": "final", "final_answer": "Correct"})},
    ]
    assert build_trace(messages) == [
        {"tool": "compute_bill", "args": {"units": 150, "state": "Gujarat"}, "thought": "t",
         "result": "Tool 'compute_bill' returned:\nRs 655.25"}
    ]


def test_follow_up_gets_previous_turn_as_history():
    agent = FakeAgent(["Bill is wrong.", "Dear Sir..."])
    s = Session(model="m", agent=agent)
    assert ask(s, "Is my bill correct?", Path("/b.jpg"))["answer"] == "Bill is wrong."
    result = ask(s, "Write a complaint letter")
    assert result["answer"] == "Dear Sir..." and result["error"] is False
    history = agent.calls[1]["history"]
    assert history[0]["content"] == "Is my bill correct?\nThe bill photo is at: /b.jpg"
    assert "Bill is wrong." in history[1]["content"]


def test_same_photo_is_not_sent_again():
    agent = FakeAgent(["a", "b"])
    s = Session(model="m", agent=agent)
    ask(s, "Check", Path("/b.jpg"))
    ask(s, "Letter please", Path("/b.jpg"))
    assert agent.calls[1]["prompt"] == "Letter please"


def test_history_keeps_only_last_turns(monkeypatch):
    monkeypatch.setattr(session_mod, "MAX_TURNS", 2)
    agent = FakeAgent(["1", "2", "3", "4"])
    s = Session(model="m", agent=agent)
    for q in ["q1", "q2", "q3", "q4"]:
        ask(s, q)
    assert [m["content"] for m in agent.calls[3]["history"] if m["role"] == "user"] == ["q2", "q3"]


def test_error_returns_short_message_and_keeps_history_clean():
    agent = FakeAgent(error=ExceptionGroup("tg", [ConnectionError("connection refused")]))
    s = Session(model="m", agent=agent)
    result = ask(s, "hi")
    assert result["error"] is True
    assert result["answer"].startswith("Error: no answer (ConnectionError: connection refused)")
    assert s.turns == []


def send_result(text):
    return {"role": "user", "content": f"Tool 'send_complaint_email' returned:\n{text}"}


@pytest.mark.parametrize(
    "answer",
    [
        "I have sent the complaint letter to the electricity authority.",
        "The email has been dispatched with the bill attached.",
        "Your letter was successfully emailed.",
        "The complaint has been submitted.",
    ],
)
def test_send_claim_without_tool_call_is_replaced(answer):
    assert check_send_status(answer, [], [{"role": "user", "content": "Please email it"}]) == not_sent_answer()


def test_send_claim_after_sent_result_is_kept():
    answer = "I have sent the letter to wadhvaniakash0@gmail.com."
    messages = [send_result("SENT: email 'Bill complaint' was sent to wadhvaniakash0@gmail.com.")]
    assert check_send_status(answer, [], messages) == answer


def test_send_claim_after_failed_send_gives_reason():
    messages = [send_result("Error executing tool send_complaint_email: NOT SENT: Email is not set up: "
                            "SMTP_USER and SMTP_PASSWORD are missing in .env.")]
    answer = check_send_status("The letter has been sent.", [], messages)
    assert answer.startswith("Your complaint letter has NOT been emailed: Email is not set up")


def test_send_claim_after_missing_login_asks_for_it():
    messages = [send_result("Error executing tool send_complaint_email: NOT SENT: The user's email login is "
                            "missing. Ask the user for it.")]
    assert check_send_status("The letter has been emailed.", [], messages) == not_sent_answer()


def test_send_claim_after_missing_details_asks_for_them():
    messages = [send_result("Error executing tool send_complaint_email: NOT SENT: The letter still has "
                            "[Your Name]. Ask the user for their name and consumer number; never invent them.")]
    assert check_send_status("I have emailed the letter.", [], messages) == not_sent_answer()


@pytest.mark.parametrize(
    "answer",
    [
        "Your bill is higher than the tariff by Rs 305.84.",
        "The bill sent by MSEDCL shows 150.0 units.",
        "I need your name and consumer number before I can send the letter.",
        None,
    ],
)
def test_answers_without_send_claim_are_kept(answer):
    assert check_send_status(answer, [], []) == answer


def test_false_send_claim_is_corrected_in_answer_and_history():
    agent = FakeAgent(["I have sent the complaint letter.", "ok"])
    s = Session(model="m", agent=agent)
    assert ask(s, "Email the complaint")["answer"] == not_sent_answer()
    ask(s, "Did it go?")
    history = json.dumps(agent.calls[1]["history"])
    assert "I have sent" not in history and "NOT been emailed" in history


def test_not_sent_answer_asks_for_login_only_when_missing():
    assert "smtps://you@gmail.com:APP-PASSWORD@smtp.gmail.com" in not_sent_answer()
    os.environ[LOGIN_ENV] = LOGIN
    assert "smtps://" not in not_sent_answer()
    assert "name and consumer number" in not_sent_answer()


@pytest.mark.parametrize(
    "question, cleaned, login",
    [
        (f"Name Asha. {LOGIN}. Send it", f"Name Asha. {LOGIN_RECEIVED} Send it", LOGIN),
        ("smtps://asha@gmail.com:abcd efgh ijkl mnop@smtp.gmail.com send it",
         f"{LOGIN_RECEIVED} send it", LOGIN),
        ("smtp://asha%40gmail.com:pw@smtp.gmail.com:587, thanks",
         f"{LOGIN_RECEIVED}, thanks", "smtp://asha%40gmail.com:pw@smtp.gmail.com:587"),
        ("Is my bill correct? It came from smtp.gmail.com", "Is my bill correct? It came from smtp.gmail.com", None),
    ],
)
def test_take_email_login(question, cleaned, login):
    assert take_email_login(question) == (cleaned, login)


def test_login_in_another_form_is_hidden_not_kept():
    question, login = take_email_login("Send it\nmy login smtps://asha@gmail.com password abcd efgh\nthanks")
    assert login is None
    assert "abcd" not in question and "asha@gmail.com" not in question
    assert question.startswith("Send it\nmy login [email login hidden") and question.endswith("\nthanks")


def test_login_is_kept_in_memory_and_never_reaches_the_model():
    agent = FakeAgent(["Please share your consumer number.", "ok"])
    s = Session(model="m", agent=agent)
    ask(s, f"Send the letter. My login is {LOGIN}")
    ask(s, "My consumer number is 1700")
    assert os.environ[LOGIN_ENV] == LOGIN
    seen_by_model = json.dumps(agent.calls)
    assert "abcdefghijklmnop" not in seen_by_model and LOGIN_RECEIVED in seen_by_model


def test_login_is_forgotten_after_a_letter_is_sent():
    class SendingAgent(FakeAgent):
        async def run(self, prompt, scripts, history=None):
            answer = await super().run(prompt, scripts, history)
            self.messages.insert(-1, send_result("SENT: email 'Bill complaint' was sent to wadhvaniakash0@gmail.com."))
            return answer

    s = Session(model="m", agent=SendingAgent(["I have sent the letter."]))
    assert ask(s, f"Send it. {LOGIN}")["answer"] == "I have sent the letter."
    assert LOGIN_ENV not in os.environ


def test_letter_after_failed_send_gets_not_sent_note():
    turn = [send_result("Error executing tool send_complaint_email: NOT SENT: Could not send the email: timed out")]
    answer = check_send_status("To,\nThe Assistant Engineer (O&M),\n...", [], turn)
    assert answer.startswith("Your complaint letter has NOT been emailed: Could not send the email: timed out")
    assert answer.endswith("To,\nThe Assistant Engineer (O&M),\n...")


def test_answer_that_already_says_not_sent_is_kept():
    turn = [send_result("Error executing tool send_complaint_email: NOT SENT: Could not send the email: timed out")]
    answer = "The letter could not be sent because the email server timed out."
    assert check_send_status(answer, [], turn) == answer


def test_retry_that_succeeds_is_kept():
    turn = [send_result("Error executing tool send_complaint_email: NOT SENT: The letter still has placeholders: [Email]."),
            send_result("SENT: email 'Bill complaint' was sent to wadhvaniakash0@gmail.com.")]
    assert check_send_status("Your letter was emailed.", [], turn) == "Your letter was emailed."


def test_old_failed_send_in_history_does_not_change_new_answers():
    history = [send_result("Error executing tool send_complaint_email: NOT SENT: Could not send the email: timed out")]
    assert check_send_status("Your bill is correct.", history, []) == "Your bill is correct."


def test_earlier_send_is_not_confused_with_failed_send_now():
    history = [send_result("SENT: email 'Bill complaint' was sent to wadhvaniakash0@gmail.com.")]
    assert check_send_status("Yes, it was sent earlier.", history, []) == "Yes, it was sent earlier."
    turn = [send_result("Error executing tool send_complaint_email: NOT SENT: Could not send the email: timed out")]
    assert check_send_status("To,\n...", history, turn).startswith("Your complaint letter has NOT been emailed")
    assert check_send_status("The letter has been sent.", history, turn).startswith("Your complaint letter has NOT been emailed")


LETTER_DRAFT = "To,\nMSEDCL\n\nSubject: Bill complaint, Consumer No. [Consumer Number]\n\nYours faithfully,\n[Your Name]"


def test_letter_gets_request_for_details_and_login():
    answer = add_send_offer(LETTER_DRAFT, [])
    assert answer.startswith(LETTER_DRAFT)
    assert answer.endswith(
        "reply with your name, your consumer number and your email login written as "
        "smtps://you@gmail.com:APP-PASSWORD@smtp.gmail.com (a Gmail app password; it is kept only in memory "
        "and never shown to the AI model), and ask me to send it."
    )


def test_letter_with_details_and_login_only_needs_send_it():
    os.environ[LOGIN_ENV] = LOGIN
    letter = LETTER_DRAFT.replace("[Consumer Number]", "1700").replace("[Your Name]", "Asha")
    assert add_send_offer(letter, []).endswith('reply "send it".')
    assert add_send_offer(LETTER_DRAFT.replace("[Your Name]", "Asha"), []).endswith(
        "reply with your consumer number, and ask me to send it.")


def test_send_offer_only_under_letters_not_after_a_send_attempt():
    assert add_send_offer("Your bill is very likely wrong.", []) == "Your bill is very likely wrong."
    turn = [send_result("SENT: email 'Bill complaint' was sent to wadhvaniakash0@gmail.com.")]
    assert add_send_offer(LETTER_DRAFT, turn) == LETTER_DRAFT


def test_session_adds_send_offer_to_letter_answer():
    s = Session(model="m", agent=FakeAgent([LETTER_DRAFT]))
    assert "reply with your name, your consumer number and your email login" in ask(s, "Write a complaint letter")["answer"]


def test_out_of_steps_answer_reports_what_the_bill_reading_found():
    extract = {"next_step": "...", "warnings": ["UNUSUAL AMOUNT: Rs 800589850.0 is far too high.", "NON-DOMESTIC: industrial."],
               "error": "Could not read these fields from the bill: units."}
    turn = [{"role": "user", "content": "Tool 'extract_bill_data' returned:\n" + json.dumps(extract)}]
    assert loop_failed_answer("Failed to reach final answer within 8 steps.", turn) == (
        "I could not finish checking the bill, but reading it found:\n"
        "- UNUSUAL AMOUNT: Rs 800589850.0 is far too high.\n- NON-DOMESTIC: industrial.\n"
        "- Could not read these fields from the bill: units."
    )


def test_out_of_steps_without_bill_reading_is_unchanged():
    failed = "Failed to reach final answer within 8 steps."
    assert loop_failed_answer(failed, [{"role": "user", "content": "hi"}]) == failed
    assert loop_failed_answer("Your bill is correct.", []) == "Your bill is correct."
