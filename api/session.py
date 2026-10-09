"""A conversation with the WattWise agent, shared by cli.py and the HTTP backend.

Keeps the last few turns (including tool results) so follow-ups such as "write a
complaint letter" reuse the bill data instead of reading the photo again.
"""

import json
import time
from pathlib import Path

from wattwise.loop import AgentLoop

ROOT = Path(__file__).resolve().parent.parent
MCP_SCRIPTS = [
    str(ROOT / "mcp_servers" / "calculator.py"),
    str(ROOT / "mcp_servers" / "tariff.py"),
    str(ROOT / "mcp_servers" / "vision.py"),
]
MAX_TURNS = 2  # each turn can be ~4k tokens; the model has a 16k context
MAX_RESULT_CHARS = 1500


def build_prompt(question: str, image: Path | None) -> str:
    if image is None:
        return question
    return f"{question}\nThe bill photo is at: {image}"


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


class Session:
    def __init__(self, model: str, agent: AgentLoop | None = None):
        self.agent = agent or AgentLoop(model_name=model)
        self.turns: list[list[dict]] = []
        self.image: Path | None = None

    @property
    def history(self) -> list[dict]:
        return [message for turn in self.turns[-MAX_TURNS:] for message in turn]

    async def ask(self, question: str, image: Path | None = None) -> dict:
        """Ask one question. Returns {"answer", "trace", "seconds", "error"}."""
        start = time.time()
        if image is not None and image == self.image:
            image = None  # same bill as before: reuse the earlier reading instead of re-reading the photo
        history = self.history
        try:
            answer = await self.agent.run(build_prompt(question, image), MCP_SCRIPTS, history=history)
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
        self.turns = (self.turns + [turn])[-MAX_TURNS:]
        return {"answer": answer, "trace": build_trace(turn), "seconds": round(time.time() - start, 1), "error": False}
