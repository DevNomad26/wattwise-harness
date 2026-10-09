import asyncio
import json
from pathlib import Path

from api import session as session_mod
from api.session import Session, build_prompt, build_trace, root_cause


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
