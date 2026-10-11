import re
import smtplib

import pytest
from mcp.server.mcpserver.exceptions import ToolError
from PIL import Image

from mcp_servers import mailer
from mcp_servers.mailer import MailerError, parse_login, prepare_letter, send_complaint_email, send_letter

SUBJECT = "Request to check and correct electricity bill, Consumer No. 123456789"
LETTER = """To,
The Assistant Engineer (O&M),
MSEDCL

Respected Sir/Madam,

The bill shows Rs 1800.0, which is Rs 305.84 higher than the tariff amount.

Yours faithfully,
Asha Patil"""
PASSWORD = "abcdefghijklmnop"
LOGIN = f"smtps://asha.patil@gmail.com:{PASSWORD}@smtp.gmail.com"


class FakeSMTP:
    """Records what would have been sent instead of opening a connection."""

    instances = []

    def __init__(self, host, port, timeout=None, context=None):
        self.host, self.port = host, port
        self.calls, self.messages = [], []
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self, context=None):
        self.calls.append("starttls")

    def login(self, user, password):
        self.calls.append(("login", user, password))

    def send_message(self, message):
        self.calls.append("send")
        self.messages.append(message)


@pytest.fixture(autouse=True)
def smtp(monkeypatch):
    FakeSMTP.instances = []
    mailer.sent_letters.clear()
    monkeypatch.setattr(mailer.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(mailer.smtplib, "SMTP_SSL", FakeSMTP)
    monkeypatch.setenv("SMTP_URL", LOGIN)
    monkeypatch.delenv("AUTHORITY_EMAIL", raising=False)
    return FakeSMTP


@pytest.fixture
def photo(tmp_path):
    path = tmp_path / "bill.jpg"
    Image.new("RGB", (10, 10), "white").save(path)
    return path


def sent_message():
    assert len(FakeSMTP.instances) == 1
    return FakeSMTP.instances[0].messages[0]


def test_sends_from_user_login_to_default_authority():
    result = send_letter(SUBJECT, LETTER)
    message = sent_message()
    assert message["To"] == "wadhvaniakash0@gmail.com"
    assert message["From"] == "asha.patil@gmail.com"
    assert message["Subject"] == SUBJECT
    assert message.get_content().strip() == LETTER
    assert result.startswith("SENT:") and "wadhvaniakash0@gmail.com" in result


def test_smtps_login_uses_ssl_without_starttls():
    send_letter(SUBJECT, LETTER)
    smtp = FakeSMTP.instances[0]
    assert (smtp.host, smtp.port) == ("smtp.gmail.com", 465)
    assert smtp.calls == [("login", "asha.patil@gmail.com", PASSWORD), "send"]


def test_smtp_login_uses_starttls(monkeypatch):
    monkeypatch.setenv("SMTP_URL", f"smtp://asha.patil@gmail.com:{PASSWORD}@smtp.gmail.com:2525")
    monkeypatch.setenv("AUTHORITY_EMAIL", "complaints@discom.example")
    send_letter(SUBJECT, LETTER)
    smtp = FakeSMTP.instances[0]
    assert (smtp.host, smtp.port) == ("smtp.gmail.com", 2525)
    assert smtp.calls == ["starttls", ("login", "asha.patil@gmail.com", PASSWORD), "send"]
    assert sent_message()["To"] == "complaints@discom.example"


@pytest.mark.parametrize(
    "url, expected",
    [
        (LOGIN, ("smtp.gmail.com", 465, True, "asha.patil@gmail.com", PASSWORD)),
        ("smtp://asha:pw@mail.example.com", ("mail.example.com", 587, False, "asha", "pw")),
        ("smtps://asha%40gmail.com:p%40ss@smtp.gmail.com:587", ("smtp.gmail.com", 587, True, "asha@gmail.com", "p@ss")),
        ("  smtps://a@b.com:pw:with:colons@smtp.b.com  ", ("smtp.b.com", 465, True, "a@b.com", "pw:with:colons")),
    ],
)
def test_parse_login(url, expected):
    config = parse_login(url)
    assert (config["host"], config["port"], config["ssl"], config["user"], config["password"]) == expected


@pytest.mark.parametrize(
    "url",
    [
        "https://asha@gmail.com:secretpw@smtp.gmail.com",
        "smtps://asha@gmail.com@smtp.gmail.com",
        "smtps://:secretpw@smtp.gmail.com",
        "smtps://asha@gmail.com:secretpw@smtp.gmail.com:port",
        "smtps://asha@gmail.com:secretpw@",
    ],
)
def test_invalid_login_is_rejected_without_repeating_it(url):
    with pytest.raises(MailerError, match="not valid") as exc:
        parse_login(url)
    assert "secretpw" not in str(exc.value) and "asha" not in str(exc.value)


def test_attaches_bill_photo(photo):
    result = send_letter(SUBJECT, LETTER, str(photo))
    attachments = list(sent_message().iter_attachments())
    assert len(attachments) == 1
    assert attachments[0].get_filename() == "bill.jpg"
    assert attachments[0].get_content_type() == "image/jpeg"
    assert attachments[0].get_content() == photo.read_bytes()
    assert "bill.jpg attached" in result


@pytest.mark.parametrize("image_path", [None, "", "   "])
def test_no_attachment_when_path_empty(image_path):
    result = send_letter(SUBJECT, LETTER, image_path)
    assert list(sent_message().iter_attachments()) == []
    assert "without an attachment" in result


def test_fills_date_and_drops_unused_optional_lines(monkeypatch):
    monkeypatch.setattr(mailer, "today", lambda: "11 October 2026")
    letter = LETTER.replace("MSEDCL", "MSEDCL\n[Sub-division office]") + "\n[Address]\n  [phone]  \nDate: [Date]"
    subject, prepared, dropped = prepare_letter(SUBJECT, letter)
    assert subject == SUBJECT
    assert prepared == LETTER + "\nDate: 11 October 2026"
    assert dropped == 0


def test_keeps_optional_details_the_user_gave():
    letter = LETTER + "\n12 MG Road, Pune\n9876543210"
    assert prepare_letter(SUBJECT, letter)[1:] == (letter, 0)


def test_today_is_a_readable_date():
    assert re.fullmatch(r"\d{2} [A-Z][a-z]+ \d{4}", mailer.today())


@pytest.mark.parametrize(
    "subject, letter, missing",
    [
        (SUBJECT, LETTER.replace("Asha Patil", "[Your Name]"), "[Your Name]"),
        (SUBJECT, LETTER.replace("Asha Patil", "[your name]"), "[Your Name]"),
        ("Bill complaint, Consumer No. [Consumer Number]", LETTER, "[Consumer Number]"),
    ],
)
def test_rejects_missing_name_or_consumer_number(subject, letter, missing):
    with pytest.raises(MailerError, match="never invent") as exc:
        send_letter(subject, letter)
    assert missing in str(exc.value)
    assert FakeSMTP.instances == []


def test_drops_sentences_with_values_not_read_from_bill():
    # As the model wrote it for a bill whose units could not be read.
    letter = LETTER.replace(
        "The bill shows Rs 1800.0, which is Rs 305.84 higher than the tariff amount.",
        "The meter readings on the bill are: previous reading null, current reading null, units consumed null.\n\n"
        "As per the Maharashtra domestic tariff, the amount for null units comes to Rs null (fixed charge Rs null, "
        "energy charge Rs null, electricity duty Rs null). The bill shows Rs 800589850, which is far higher than "
        "any tariff charge for this connection.",
    )
    _, prepared, dropped = prepare_letter(SUBJECT, letter)
    assert dropped == 2
    assert prepared == LETTER.replace(
        "The bill shows Rs 1800.0, which is Rs 305.84 higher than the tariff amount.",
        "The bill shows Rs 800589850, which is far higher than any tariff charge for this connection.",
    )


@pytest.mark.parametrize("line", ["The amount for None units comes to Rs 0.", "units consumed NaN"])
def test_drops_line_when_every_sentence_has_missing_value(line):
    _, prepared, dropped = prepare_letter(SUBJECT, LETTER.replace("Respected Sir/Madam,", f"Respected Sir/Madam,\n\n{line}"))
    assert (prepared, dropped) == (LETTER, 1)


def test_sent_result_says_sentences_were_left_out():
    result = send_letter(SUBJECT, LETTER + "\nPrevious reading null.")
    assert "1 sentence(s) with values not read from the bill were left out" in result
    assert "null" not in sent_message().get_content()


def test_rejects_missing_value_in_subject():
    with pytest.raises(MailerError, match="subject"):
        send_letter("Bill for null units", LETTER)


def test_none_of_is_ordinary_english():
    letter = LETTER + "\nNone of these charges were explained."
    assert prepare_letter(SUBJECT, letter)[1:] == (letter, 0)


@pytest.mark.parametrize(
    "letter, placeholder",
    [
        (LETTER.replace("Rs 1800.0", "Rs {bill_total}"), "{bill_total}"),
        (LETTER + "\n[Email]", "[Email]"),
        (LETTER + "\nAddress: [Address]", "[Address]"),  # not alone on its line, so not dropped
    ],
)
def test_rejects_other_placeholders(letter, placeholder):
    with pytest.raises(MailerError, match="placeholders") as exc:
        send_letter(SUBJECT, letter)
    assert placeholder in str(exc.value)
    assert FakeSMTP.instances == []


@pytest.mark.parametrize(
    "subject, letter, message",
    [
        ("", LETTER, "Subject is empty"),
        ("   ", LETTER, "Subject is empty"),
        ("Line one\nLine two", LETTER, "one line"),
        ("x" * 201, LETTER, "one line"),
        (SUBJECT, "", "Letter is empty"),
        (SUBJECT, "a" * 10_001, "too long"),
    ],
)
def test_rejects_bad_subject_or_letter(subject, letter, message):
    with pytest.raises(MailerError, match=message):
        send_letter(subject, letter)
    assert FakeSMTP.instances == []


def test_rejects_non_image_attachment(tmp_path):
    secret = tmp_path / ".env"
    secret.write_text("SMTP_PASSWORD=app-password")
    with pytest.raises(MailerError, match="Only the bill photo"):
        send_letter(SUBJECT, LETTER, str(secret))
    assert FakeSMTP.instances == []


def test_rejects_missing_photo(tmp_path):
    with pytest.raises(MailerError, match="not found"):
        send_letter(SUBJECT, LETTER, str(tmp_path / "missing.jpg"))


def test_rejects_large_photo(tmp_path, monkeypatch):
    monkeypatch.setattr(mailer, "MAX_ATTACHMENT_BYTES", 10)
    path = tmp_path / "big.png"
    path.write_bytes(b"x" * 11)
    with pytest.raises(MailerError, match="larger than"):
        send_letter(SUBJECT, LETTER, str(path))


def test_missing_login_asks_user_for_it(monkeypatch):
    monkeypatch.delenv("SMTP_URL")
    with pytest.raises(MailerError, match="login is missing. Ask the user") as exc:
        send_letter(SUBJECT, LETTER)
    assert "smtps://you@gmail.com:APP-PASSWORD@smtp.gmail.com" in str(exc.value)
    assert FakeSMTP.instances == []


def test_same_letter_is_sent_once():
    send_letter(SUBJECT, LETTER)
    with pytest.raises(MailerError, match="already sent"):
        send_letter(SUBJECT, LETTER + "\n")
    assert len(FakeSMTP.instances) == 1


def test_failed_send_can_be_retried(monkeypatch):
    class DownSMTP(FakeSMTP):
        def send_message(self, message):
            raise smtplib.SMTPServerDisconnected("connection lost")

    monkeypatch.setattr(mailer.smtplib, "SMTP_SSL", DownSMTP)
    with pytest.raises(MailerError, match="connection lost"):
        send_letter(SUBJECT, LETTER)
    monkeypatch.setattr(mailer.smtplib, "SMTP_SSL", FakeSMTP)
    assert send_letter(SUBJECT, LETTER).startswith("SENT:")


def test_wrong_password_message(monkeypatch):
    class LockedSMTP(FakeSMTP):
        def login(self, user, password):
            raise smtplib.SMTPAuthenticationError(535, b"Username and Password not accepted")

    monkeypatch.setattr(mailer.smtplib, "SMTP_SSL", LockedSMTP)
    with pytest.raises(MailerError, match="App Password") as exc:
        send_letter(SUBJECT, LETTER)
    assert PASSWORD not in str(exc.value)


def test_unreachable_server(monkeypatch):
    def refuse(*args, **kwargs):
        raise ConnectionRefusedError("Connection refused")

    monkeypatch.setattr(mailer.smtplib, "SMTP_SSL", refuse)
    with pytest.raises(MailerError, match="Could not send"):
        send_letter(SUBJECT, LETTER)


def test_tool_returns_confirmation(photo):
    result = send_complaint_email(SUBJECT, LETTER, str(photo))
    assert result.startswith("SENT:")


def test_tool_raises_readable_error():
    with pytest.raises(ToolError, match=r"^NOT SENT: .*\[Your Name\]"):
        send_complaint_email(SUBJECT, LETTER.replace("Asha Patil", "[Your Name]"))
    assert FakeSMTP.instances == []
