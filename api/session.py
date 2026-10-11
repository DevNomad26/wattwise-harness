"""A conversation with the WattWise agent, shared by cli.py and the HTTP backend.

Keeps the last few turns (including tool results) so follow-ups such as "write a
complaint letter" reuse the bill data instead of reading the photo again.

An email login typed in chat (smtps://you@gmail.com:APP-PASSWORD@smtp.gmail.com) is cut
out of the question before the model sees it, so it never reaches the model server, the
history or the trace. It is kept only in this process's memory (SMTP_URL), which the
mailer server inherits, and is forgotten once a letter is sent or the process stops.
"""

import json
import os
import re
import time
from pathlib import Path

from mcp_servers.mailer import LOGIN_ENV, LOGIN_EXAMPLE
from wattwise.loop import AgentLoop
from wattwise.schemas import Step

ROOT = Path(__file__).resolve().parent.parent
MCP_SCRIPTS = [
    str(ROOT / "mcp_servers" / "calculator.py"),
    str(ROOT / "mcp_servers" / "tariff.py"),
    str(ROOT / "mcp_servers" / "vision.py"),
    str(ROOT / "mcp_servers" / "mailer.py"),
]
MAX_TURNS = 2  # each turn can be ~4k tokens; the model has a 16k context
MAX_RESULT_CHARS = 1500
SEND_RESULT = "Tool 'send_complaint_email' returned:\n"
EXTRACT_RESULT = "Tool 'extract_bill_data' returned:\n"
LOOP_FAILED = "Failed to reach final answer"  # what AgentLoop returns when it runs out of steps
# "I have sent", "has been emailed", "was successfully dispatched", ...
SEND_CLAIM = re.compile(
    r"\b(?:I|has|have|had|was|were|been|successfully)\s+(?:been\s+)?(?:successfully\s+)?"
    r"(?:sent|e-?mailed|mailed|dispatched|submitted)\b",
    re.IGNORECASE,
)
# smtps://user:password@host[:port]. The password may be pasted with spaces ("abcd efgh ijkl mnop").
EMAIL_LOGIN = re.compile(r"\bsmtps?://\S+?:[^@\n]*@[A-Za-z0-9.-]+(?::\d+)?", re.IGNORECASE)
LOGIN_LEFTOVER = re.compile(r"\bsmtps?://[^\n]*", re.IGNORECASE)  # a login in another form: hide the rest of the line
LOGIN_RECEIVED = "[email login received]"
LOGIN_HIDDEN = f"[email login hidden: it was not written as {LOGIN_EXAMPLE}]"
ASK_AGAIN = ("consumer number", "login is missing")  # NOT SENT reasons the user fixes by replying
LETTER_SIGN_OFF = re.compile(r"\bYours (?:faithfully|sincerely|truly)\b", re.IGNORECASE)
SAYS_NOT_SENT = re.compile(r"\bnot\b[^.]{0,40}\b(?:sent|e-?mailed|send|email)\b", re.IGNORECASE)


def build_prompt(question: str, image: Path | None) -> str:
    if image is None:
        return question
    return f"{question}\nThe bill photo is at: {image.as_posix()}"



def root_cause(exc: BaseException) -> BaseException:
    """The first real error inside (possibly nested) exception groups."""
    while isinstance(exc, BaseExceptionGroup) and exc.exceptions:
        exc = exc.exceptions[0]
    return exc


def build_trace(messages: list[dict]) -> list[dict]:
    """Tool calls made in one turn, each with its (shortened) result, for the UI."""
    trace = []
    for message in messages:
        if message["role"] == "assistant":
            try:
                step = json.loads(message["content"])
            except (json.JSONDecodeError, TypeError):
                continue
            if isinstance(step, dict) and step.get("action") == "tool":
                trace.append({"tool": step.get("tool_name"), "args": step.get("tool_args") or {}, "thought": step.get("thought")})
        elif message["role"] == "user" and trace and "result" not in trace[-1]:
            trace[-1]["result"] = message["content"][:MAX_RESULT_CHARS]
    return trace


def loop_failed_answer(answer: str, turn: list[dict]) -> str:
    """When the loop runs out of steps, tell the user what reading the bill found instead of nothing."""
    if not isinstance(answer, str) or not answer.startswith(LOOP_FAILED):
        return answer
    for m in reversed(turn):
        if m["role"] == "user" and m["content"].startswith(EXTRACT_RESULT):
            try:
                data = json.loads(m["content"][len(EXTRACT_RESULT):])
            except json.JSONDecodeError:
                return answer
            findings = list(data.get("warnings") or []) + ([data["error"]] if data.get("error") else [])
            if not findings:
                return answer
            return "I could not finish checking the bill, but reading it found:\n" + "\n".join(f"- {f}" for f in findings[:4])
    return answer


def take_email_login(question: str) -> tuple[str, str | None]:
    """Cut any email login out of the question. Returns the question without it, and the login."""
    logins = [re.sub(r"\s+", "", match).rstrip(".") for match in EMAIL_LOGIN.findall(question)]
    question = LOGIN_LEFTOVER.sub(LOGIN_HIDDEN, EMAIL_LOGIN.sub(LOGIN_RECEIVED, question))
    return question, logins[-1] if logins else None


def was_sent(messages: list[dict]) -> bool:
    return any(m["role"] == "user" and m["content"].startswith(SEND_RESULT + "SENT:") for m in messages)


def login_request() -> str:
    return (
        f"your email login written as {LOGIN_EXAMPLE} (a Gmail app password; it is kept only "
        "in memory and never shown to the AI model)"
    )


def not_sent_answer() -> str:
    need = "your name and consumer number"
    if not os.getenv(LOGIN_ENV):
        need += f", and {login_request()}"
    return f"Your complaint letter has NOT been emailed yet. To send it, reply with {need}, and ask me to send the letter."


def add_send_offer(answer: str, turn: list[dict]) -> str:
    """Under a complaint letter, tell the user exactly what to reply to have it emailed.
    Small models offer to send it but forget to ask for the details the send needs."""
    if not isinstance(answer, str) or not LETTER_SIGN_OFF.search(answer):
        return answer
    if any(m["role"] == "user" and m["content"].startswith(SEND_RESULT) for m in turn):
        return answer  # a send was tried this turn; check_send_status reports it
    need = [label for placeholder, label in (("[your name]", "your name"), ("[consumer number]", "your consumer number"))
            if placeholder in answer.lower()]
    if not os.getenv(LOGIN_ENV):
        need.append(login_request())
    if not need:
        return f'{answer}\n\nTo email this letter to the electricity authority, reply "send it".'
    asked = need[0] if len(need) == 1 else ", ".join(need[:-1]) + " and " + need[-1]
    return f"{answer}\n\nTo email this letter to the electricity authority, reply with {asked}, and ask me to send it."


def not_sent_reasons(messages: list[dict]) -> list[str]:
    return [m["content"].split("NOT SENT: ", 1)[1] for m in messages
            if m["role"] == "user" and m["content"].startswith(SEND_RESULT) and "NOT SENT: " in m["content"]]


def not_sent_status(reasons: list[str]) -> str:
    if not reasons or any(marker in reasons[-1] for marker in ASK_AGAIN):
        return not_sent_answer()
    return f"Your complaint letter has NOT been emailed: {reasons[-1]} You can send the letter yourself."


def check_send_status(answer: str, history: list[dict], turn: list[dict]) -> str:
    """Make sure the user knows whether the letter was emailed. Small models sometimes say it was
    sent without calling the tool, or answer with the letter after a failed send without saying so."""
    if not isinstance(answer, str) or was_sent(turn):
        return answer
    reasons = not_sent_reasons(turn)
    if SEND_CLAIM.search(answer):
        if not reasons and was_sent(history):
            return answer  # talking about a letter sent in an earlier turn
        return not_sent_status(reasons)
    if reasons and not SAYS_NOT_SENT.search(answer):
        return f"{not_sent_status(reasons)}\n\n{answer}"
    return answer


class Session:
    def __init__(self, model: str, agent: AgentLoop | None = None):
        self.agent = agent or AgentLoop(model_name=model)
        self.turns: list[list[dict]] = []
        self.image: Path | None = None

    @property
    def history(self) -> list[dict]:
        return [message for turn in self.turns[-MAX_TURNS:] for message in turn]

    async def ask(self, question: str, image: Path | None = None, on_event = None) -> dict:
        """Ask one question. Returns {"answer", "trace", "seconds", "error"}."""
        start = time.time()
        question, login = take_email_login(question)
        if login:
            os.environ[LOGIN_ENV] = login
        if image is not None and image == self.image:
            image = None  # same bill as before: reuse the earlier reading instead of re-reading the photo
        history = self.history
        kwargs = {"on_event": on_event} if on_event is not None else {}
        try:
            answer = await self.agent.run(build_prompt(question, image), MCP_SCRIPTS, history=history, **kwargs)
        except Exception as exc:
            cause = root_cause(exc)
            return {
                "answer": f"Error: no answer ({type(cause).__name__}: {cause}). "
                "Check that Ollama is running (`ollama ps`) and try again.",
                "trace": [],
                "seconds": round(time.time() - start, 1),
                "error": True,
            }
        if image is not None:
            self.image = image
        turn = self.agent.messages[1 + len(history):]  # skip system prompt and old turns
        if was_sent(turn):
            os.environ.pop(LOGIN_ENV, None)  # the login is needed for one letter only
        checked = add_send_offer(check_send_status(loop_failed_answer(answer, turn), history, turn), turn)
        if checked != answer:  # keep the corrected answer in history too
            answer = checked
            turn = turn[:-1] + [{"role": "assistant", "content": Step(action="final", final_answer=answer).model_dump_json()}]
        self.turns = (self.turns + [turn])[-MAX_TURNS:]
        return {"answer": answer, "trace": build_trace(turn), "seconds": round(time.time() - start, 1), "error": False}
