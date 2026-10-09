"""Command-line entry point for the WattWise harness.

Usage:
    python cli.py "What is the electricity bill for 250 units in Rajasthan?"
    python cli.py "Is my bill correct?" --image bill_photos/may.jpg
    python cli.py "Is my bill correct?" --image "C:\\Users\\me\\Downloads\\bill.jpg"
    python cli.py --model qwen3.5:4b "Explain my bill" --image bill_photos/may.jpg
    python cli.py                      # interactive mode, type 'exit' to quit

Interactive mode remembers the conversation, so follow-ups like "write a complaint
letter" reuse the bill that was already checked.
Windows paths (C:\\..., \\\\wsl.localhost\\Ubuntu\\...) are converted automatically.
"""

import argparse
import asyncio
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

from api.session import Session


def to_wsl_path(path: str) -> str:
    """Convert a path pasted from Windows into a Linux path; other paths are unchanged."""
    path = path.strip().strip('"').strip("'")
    wsl_share = re.match(r"^\\\\wsl(?:\.localhost|\$)\\[^\\]+\\(.*)$", path, re.IGNORECASE)
    if wsl_share:
        return "/" + wsl_share.group(1).replace("\\", "/")
    drive = re.match(r"^([A-Za-z]):[\\/](.*)$", path)
    if drive:
        return f"/mnt/{drive.group(1).lower()}/" + drive.group(2).replace("\\", "/")
    return path


def image_path(path: str) -> Path:
    """Absolute path of a bill photo, accepting Windows-style paths."""
    return Path(to_wsl_path(path)).expanduser().resolve()


def print_answer(answer: str, seconds: float) -> None:
    print("=" * 60)
    print(answer)
    print("=" * 60)
    print(f"(answered in {seconds:.0f} s)")


def ask_and_print(session: Session, question: str, image: Path | None) -> None:
    result = asyncio.run(session.ask(question, image))
    print_answer(result["answer"], result["seconds"])


def interactive(session: Session) -> None:
    print("WattWise interactive mode. Type 'exit' to quit.")
    print("Follow-up questions remember the last bill; give a photo path only for a new bill.")
    try:
        while True:
            question = input("You: ").strip()
            if question.lower() == "exit":
                break
            if not question:
                continue
            path = input("Bill photo path (Enter to skip or keep the same bill): ").strip()
            image = image_path(path) if path else None
            if image and not image.is_file():
                print(f"Error: bill photo not found: {image}")
                continue
            ask_and_print(session, question, image)
    except (KeyboardInterrupt, EOFError):
        print()


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Check electricity bills with the WattWise harness.")
    parser.add_argument("question", nargs="?", help="Question to ask. Omit for interactive mode.")
    parser.add_argument("--image", help="Path to a bill photo (Linux or Windows path).")
    parser.add_argument(
        "--model",
        default=os.environ.get("MAIN_MODEL", "gemma4:e4b"),
        help="Ollama model to use (default: MAIN_MODEL from .env, else gemma4:e4b).",
    )
    args = parser.parse_args()

    image = image_path(args.image) if args.image else None
    if image and not image.is_file():
        sys.exit(f"Error: bill photo not found: {image}")
    session = Session(model=args.model)

    if args.question:
        ask_and_print(session, args.question, image)
    else:
        interactive(session)


if __name__ == "__main__":
    main()
