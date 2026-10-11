"""Mailer MCP server: emails a finished complaint letter to the electricity authority.

The recipient comes from .env (AUTHORITY_EMAIL), never from the model, so the model
cannot choose who gets mail. The sender is the user's own email: the user types the login
in chat as smtps://you@gmail.com:APP-PASSWORD@smtp.gmail.com, and api/session.py cuts it out
of the message before the model sees it and hands it to this server as SMTP_URL, kept only
in memory. No message from this server ever repeats the login.

Code only finishes what it knows for sure: it fills in today's date, drops address/phone/
office lines the user did not give, and drops sentences that copy a value the bill photo
did not give ("previous reading null"). It refuses a letter without the user's name and
consumer number or with any other placeholder, attaches only the bill photo, and sends
each letter once.
"""

import hashlib
import mimetypes
import os
import re
import smtplib
import ssl
from datetime import date
from email.message import EmailMessage
from urllib.parse import unquote, urlsplit

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))

DEFAULT_AUTHORITY_EMAIL = "wadhvaniakash0@gmail.com"  # demo inbox until real DISCOM addresses are added
LOGIN_ENV = "SMTP_URL"
LOGIN_EXAMPLE = "smtps://you@gmail.com:APP-PASSWORD@smtp.gmail.com"
TIMEOUT = 30
MAX_SUBJECT_LENGTH = 200
MAX_LETTER_LENGTH = 10_000
MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
ATTACHMENT_TYPES = {".jpg", ".jpeg", ".png", ".webp"}  # same photos the API accepts
# "[Your Name]" style placeholders from the letter template, and unfilled "{field}" markers.
PLACEHOLDER = re.compile(r"\[[^\[\]\n]{1,40}\]|\{[a-z_]+\}")
REQUIRED_DETAILS = ("[Your Name]", "[Consumer Number]")  # the authority cannot act without these
DATE_PLACEHOLDER = re.compile(r"\[Date\]", re.IGNORECASE)
# Values the bill photo did not give, copied into the letter as text ("previous reading null").
MISSING_VALUE = re.compile(r"\b(?:null|undefined|nan)\b|\bNone\b(?!\s+of\b)", re.IGNORECASE)
SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
# Template lines the user may leave out; a line holding only one of these is dropped.
OPTIONAL_LINE = re.compile(
    r"^[ \t]*\[(?:Address|Phone|Sub-division office)\][ \t]*(?:\n|$)", re.MULTILINE | re.IGNORECASE
)

sent_letters: set[str] = set()  # letters this server process already sent


class MailerError(ValueError):
    """Raised when the email cannot be sent, with a message the model can read."""


def parse_login(url: str) -> dict:
    """Split smtps://user:password@host[:port] into SMTP settings.

    smtps connects with SSL (port 465 by default), smtp with STARTTLS (port 587).
    """
    parts = urlsplit(str(url).strip())
    try:
        port = parts.port
    except ValueError:
        port = -1
    if parts.scheme not in ("smtp", "smtps") or not (parts.hostname and parts.username and parts.password) or port == -1:
        raise MailerError(f"The email login is not valid. It must look like {LOGIN_EXAMPLE}.")
    return {
        "host": parts.hostname,
        "port": port or (465 if parts.scheme == "smtps" else 587),
        "ssl": parts.scheme == "smtps",
        "user": unquote(parts.username),
        "password": unquote(parts.password),
    }


def load_config() -> dict:
    """The sender's login (given by the user in chat, kept only in memory) and the fixed recipient."""
    url = os.getenv(LOGIN_ENV)
    if not url:
        raise MailerError(
            f"The user's email login is missing. Ask the user for it, written as {LOGIN_EXAMPLE} "
            "(a Gmail app password, without spaces). It is hidden from you."
        )
    return {**parse_login(url), "to": os.getenv("AUTHORITY_EMAIL") or DEFAULT_AUTHORITY_EMAIL}


def today() -> str:
    return date.today().strftime("%d %B %Y")


def drop_missing_values(letter: str) -> tuple[str, int]:
    """Drop the sentences that hold a value the bill photo did not give. Returns the letter and how many."""
    lines, dropped = [], 0
    for line in letter.splitlines():
        if not MISSING_VALUE.search(line):
            lines.append(line)
            continue
        sentences = SENTENCE_BREAK.split(line.strip())
        kept = [sentence for sentence in sentences if not MISSING_VALUE.search(sentence)]
        dropped += len(sentences) - len(kept)
        if kept:
            lines.append(" ".join(kept))
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)), dropped


def prepare_letter(subject: str, letter: str) -> tuple[str, str, int]:
    """Reject an empty, oversized or unfinished letter; fill in the date and drop unused lines and
    sentences with values that were not read. Returns subject, letter and how many sentences were dropped."""
    if not isinstance(subject, str) or not subject.strip():
        raise MailerError("Subject is empty.")
    if "\n" in subject.strip() or len(subject) > MAX_SUBJECT_LENGTH:
        raise MailerError(f"Subject must be one line of at most {MAX_SUBJECT_LENGTH} characters.")
    if not isinstance(letter, str) or not letter.strip():
        raise MailerError("Letter is empty.")
    if len(letter) > MAX_LETTER_LENGTH:
        raise MailerError(f"Letter is too long (max {MAX_LETTER_LENGTH} characters).")
    missing = [p for p in REQUIRED_DETAILS if p.lower() in (subject + "\n" + letter).lower()]
    if missing:
        raise MailerError(
            f"The letter still has {' and '.join(missing)}. Ask the user for their name and consumer "
            "number; never invent them."
        )
    if MISSING_VALUE.search(subject):
        raise MailerError("The subject has a value that was not read from the bill (null or None). Remove it.")
    letter, dropped = drop_missing_values(letter)
    letter = OPTIONAL_LINE.sub("", DATE_PLACEHOLDER.sub(today(), letter))
    placeholders = sorted(set(PLACEHOLDER.findall(subject + "\n" + letter)))
    if placeholders:
        raise MailerError(
            f"The letter still has placeholders: {', '.join(placeholders)}. Fill them with details "
            "the user gave, or remove those lines, then call again."
        )
    return subject.strip(), letter.strip(), dropped


def check_attachment(image_path: str | None) -> str | None:
    """Return the bill photo path to attach, or None. Only image files can be attached."""
    if not image_path or not str(image_path).strip():
        return None
    image_path = str(image_path).strip()
    if os.path.splitext(image_path)[1].lower() not in ATTACHMENT_TYPES:
        raise MailerError(f"Only the bill photo can be attached ({', '.join(sorted(ATTACHMENT_TYPES))}).")
    if not os.path.isfile(image_path):
        raise MailerError(f"Bill photo not found at {image_path}.")
    if os.path.getsize(image_path) > MAX_ATTACHMENT_BYTES:
        raise MailerError(f"Bill photo is larger than {MAX_ATTACHMENT_BYTES // (1024 * 1024)} MB.")
    return image_path


def build_message(subject: str, letter: str, sender: str, recipient: str, image_path: str | None) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(letter + "\n")
    if image_path:
        maintype, subtype = (mimetypes.guess_type(image_path)[0] or "image/jpeg").split("/")
        with open(image_path, "rb") as f:
            message.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(image_path))
    return message


def send_letter(subject: str, letter: str, image_path: str | None = None) -> str:
    """Check, build and send the letter. Returns a confirmation; raises MailerError otherwise."""
    subject, letter, dropped = prepare_letter(subject, letter)
    attachment = check_attachment(image_path)
    config = load_config()
    key = hashlib.sha256(f"{subject}\n{letter}".encode("utf-8")).hexdigest()
    if key in sent_letters:
        raise MailerError(f"This letter was already sent to {config['to']}. It was not sent again.")

    message = build_message(subject, letter, config["user"], config["to"], attachment)
    context = ssl.create_default_context()
    try:
        if config["ssl"]:
            smtp = smtplib.SMTP_SSL(config["host"], config["port"], timeout=TIMEOUT, context=context)
        else:
            smtp = smtplib.SMTP(config["host"], config["port"], timeout=TIMEOUT)
        with smtp:
            if not config["ssl"]:
                smtp.starttls(context=context)
            smtp.login(config["user"], config["password"])
            smtp.send_message(message)
    except smtplib.SMTPAuthenticationError:
        raise MailerError(
            "Email login failed: the email address or app password is wrong (Gmail needs an App Password, "
            "not the normal password)."
        ) from None
    except (smtplib.SMTPException, OSError) as exc:
        raise MailerError(f"Could not send the email: {exc}") from None

    sent_letters.add(key)
    attached = f"with the bill photo {os.path.basename(attachment)} attached" if attachment else "without an attachment"
    removed = f" {dropped} sentence(s) with values not read from the bill were left out." if dropped else ""
    return f"SENT: email '{subject}' was sent to {config['to']} {attached}.{removed}"


mcp = MCPServer("Mailer Server", log_level="WARNING")


@mcp.tool()
def send_complaint_email(subject: str, letter: str, image_path: str | None = None) -> str:
    """Email a finished complaint letter to the electricity authority. The address is fixed.

    Nothing is emailed unless you call this tool and it returns "SENT:". Call it only after
    the user asks to send the letter. It sends from the email login the user gave, which is
    hidden from you; never ask for a password any other way. "letter" is only the letter text (no
    notes to the user), with [Your Name] and [Consumer Number] replaced by what the user gave.
    The date and unused address/phone lines are handled by the tool. "image_path" is the bill
    photo path (the one given to extract_bill_data) so the bill is attached.
    """
    try:
        return send_letter(subject, letter, image_path)
    except MailerError as exc:
        raise ToolError(f"NOT SENT: {exc}") from None


if __name__ == "__main__":
    mcp.run(transport="stdio")
