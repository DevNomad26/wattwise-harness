"""Vision MCP server: reads an electricity bill photo into BillData JSON.

One VISION_MODEL call reads the photo. For every number the model first names the label
it found on the bill, then copies the value printed next to it, so the model (not code)
maps labels to keys; labels differ between electricity companies. A second, text-only call
asks which state the city/company/address is in, since the state is rarely printed.

Code never chooses a value. It only flags values without a label, compares units with
current - previous and with the most the connected load can use (via the calculator),
and validates the result against BillData.
"""

import base64
import io
import json
import os
import re
import sys
import urllib.request

import json_repair
from dotenv import load_dotenv
from PIL import Image, ImageOps
from pydantic import ValidationError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)  # so imports work when run as `python mcp_servers/vision.py`

from mcp.server.mcpserver import MCPServer  # noqa: E402
from mcp_servers.calculator import CalculatorError, evaluate  # noqa: E402
from wattwise.schemas import BillData  # noqa: E402

load_dotenv(os.path.join(ROOT, ".env"))
OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
VISION_MODEL = os.getenv("VISION_MODEL")
TIMEOUT = 400
# Image tokens grow with pixels; a 12 MP phone photo would take minutes and overflow
# the context. 1.6 MP keeps a full A4 bill readable.
MAX_PIXELS = 1_600_000
TEXT_KEYS = ("discom", "city", "address", "state", "category", "due_date")
MAX_RS_PER_UNIT = 1000
NUMBER_KEYS = ("months", "previous_reading", "current_reading", "units", "total_amount_due", "load_kw")

mcp = MCPServer("Vision Server", log_level="WARNING")

PROMPT = """You are reading a photo of an Indian electricity bill. Labels differ between
electricity companies, so match by meaning, not by exact wording.

Return JSON with these text keys as plain strings:
- "discom": electricity company name (usually at the top).
- "city": city or town printed on the bill (company office or consumer address).
- "address": one short address line (at most 15 words) that names a town or city.
- "state": Indian state of the bill. It is rarely printed: work it out from the company
  name, city or address.
- "category": connection type, one word: domestic, commercial, industrial, agricultural or
  other (e.g. "Residential", "LT-I Domestic" = domestic; "Industrial", "LT-V" = industrial).
- "due_date": the date printed next to "Due Date", written as YYYY-MM-DD.

Use only this bill month. Ignore any billing history table of past months.

And these number keys as {"label": "<label as printed>", "value": <number>}. First find
the label on the bill, then copy the number printed next to it:
- "months": number of months this bill covers (e.g. "Billing Period"). Usually 1.
- "previous_reading": previous meter reading in kWh, from the meter that measures electricity
  taken from the grid. If a table has Export and Import columns, use the Import column, never
  Export. Never use a solar generation meter. Include the column name in "label",
  e.g. "Previous Reading KWH Import".
- "current_reading": present/current reading from that same meter and column.
  Readings are kWh numbers, never dates.
- "units": units billed on this bill (e.g. "Net Billed Units", "Units Consumed"). Copy the
  printed number; never subtract readings yourself. Use null if this bill month's units are
  not printed.
- "total_amount_due": the final amount the consumer must pay by the due date (e.g. "Net
  Payable", "Amount Payable", "Net Amount Payable by Due Date"). Not a subtotal, not a
  "Total Amount" line that is followed by more adjustments, not the amount after the due date.
  If amounts are listed for different payment dates ("If paid upto", "If paid after"), use the
  amount for the due date itself.
- "load_kw": sanctioned or connected load of the connection (e.g. "Sanctioned Load",
  "Connected Load", "Contract Demand"), in kW or kVA (HP is fine too).

Copy numbers digit by digit, without commas or currency symbols. Never calculate.
Use null for anything that is not printed."""

STATE_PROMPT = """Which Indian state is this electricity bill from?
Electricity company: <discom>
City: <city>
Addresses on the bill: <address>
Names may have small spelling mistakes or abbreviations (e.g. BLR for Bengaluru).
Reply only with JSON: {"state": "<state name>"}"""


def load_image(image_path: str) -> Image.Image:
    """Open a photo upright and shrink it to at most MAX_PIXELS."""
    image = ImageOps.exif_transpose(Image.open(image_path)).convert("RGB")
    pixels = image.width * image.height
    if pixels > MAX_PIXELS:
        scale = (MAX_PIXELS / pixels) ** 0.5
        image = image.resize((int(image.width * scale), int(image.height * scale)), Image.LANCZOS)
    return image


def image_to_base64(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, "JPEG", quality=95)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def call_ollama(model: str, prompt: str, images: list[str] | None = None) -> dict:
    """Run one JSON-mode generation and return the parsed (repaired if needed) object."""
    payload = {
        "model": model,
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "think": False,
        "keep_alive": "30m",  # avoid reloading the model between questions
        "options": {"temperature": 0},
    }
    if images:
        payload["images"] = images
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        text = json.loads(response.read().decode()).get("response", "{}")
    data = json_repair.loads(text)
    return data if isinstance(data, dict) else {}


def to_number(value) -> float | None:
    """Parse a number the model copied, ignoring thousands separators and currency.

    Returns None unless the text holds exactly one number, so a date such as
    "07-03-2024" is never mistaken for a reading.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    numbers = re.findall(r"-?\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(numbers[0]) if len(numbers) == 1 else None


def split_fields(raw: dict) -> tuple[dict, dict]:
    """Split {"key": {"label": .., "value": ..}} into values and source labels.

    Text keys come back as bare values; any key may, so both shapes are accepted.
    """
    values, sources = {}, {}
    for key in TEXT_KEYS + NUMBER_KEYS:
        field = raw.get(key)
        if isinstance(field, dict):
            values[key], sources[key] = field.get("value"), field.get("label")
        else:
            values[key], sources[key] = field, None
    return values, sources


def lookup_state(city: str | None, discom: str | None, address: str | None = None) -> str | None:
    """Ask the model (text only, no image) which state the city/company/address is in."""
    if not city and not discom and not address:
        return None
    prompt = (
        STATE_PROMPT.replace("<discom>", str(discom or "unknown"))
        .replace("<city>", str(city or "unknown"))
        .replace("<address>", str(address or "unknown"))
    )
    state = call_ollama(VISION_MODEL, prompt).get("state")
    return state if isinstance(state, str) and state.strip() else None


def resolve_state(raw: dict) -> list[str]:
    """Replace the photo-read state with the one looked up from city/company/address. Returns warnings."""
    values, _ = split_fields(raw)
    state = lookup_state(values["city"], values["discom"], values["address"])
    if not state:
        return []
    raw["state"] = {"label": f"looked up from city {values['city']} / {values['discom']}", "value": state}
    if values["state"] and str(values["state"]).strip().lower() != state.strip().lower():
        return [f"Photo reading said state {values['state']}, but city/company point to {state}; using {state}."]
    return []


def check_load(units: float | None, load_kw: float | None, months: float | None) -> list[str]:
    """Flag units no connection of this size could use: load x 24 h x 31 days x months.

    kVA and HP values are treated as kW, which only raises the limit, so a normal bill
    is never flagged.
    """
    if units is None or not load_kw or load_kw <= 0 or not months or months <= 0:
        return []
    try:
        max_units = evaluate(f"{load_kw} * 24 * 31 * {months}")
    except CalculatorError:
        return []
    if units <= max_units:
        return []
    return [
        f"IMPOSSIBLE UNITS: billed units {units} are more than the most a {load_kw} kW connection "
        f"can use in {months} month(s): {max_units} units ({load_kw} kW x 24 h x 31 days x {months}). "
        "The meter reading or the bill is wrong."
    ]


def check_amount(
    total: float | None, units: float | None, load_kw: float | None = None, months: float | None = None
) -> list[str]:
    """Flag a total above Rs MAX_RS_PER_UNIT per unit; real tariffs are far below this.

    Without billed units, uses the most the connection could use (load x 24 h x 31 days x
    months), which gives the lowest possible price per unit.
    """
    if total is None:
        return []
    try:
        if units and units > 0:
            basis = f"{units} units"
            per_unit = evaluate(f"round({total} / {units}, 2)")
        elif load_kw and load_kw > 0 and months and months > 0:
            max_units = evaluate(f"{load_kw} * 24 * 31 * {months}")
            basis = f"even the most a {load_kw} kW connection can use ({max_units} units)"
            per_unit = evaluate(f"round({total} / {max_units}, 2)")
        else:
            return []
    except CalculatorError:
        return []
    if per_unit <= MAX_RS_PER_UNIT:
        return []
    return [
        f"UNUSUAL AMOUNT: Rs {total} for {basis} is Rs {per_unit} per unit; tariffs are far below "
        f"Rs {MAX_RS_PER_UNIT} per unit. The amount may be misread, include large arrears, or be wrong."
    ]


def check_category(category: str | None) -> list[str]:
    """Tariff data covers domestic connections only."""
    if not category or "domestic" in str(category).lower() or "residential" in str(category).lower():
        return []
    return [
        f"NON-DOMESTIC: this is a {category} connection. Tariff data covers domestic connections only, "
        "so the bill cannot be recomputed from the tariff."
    ]


def check(raw: dict) -> dict:
    """Validate the model's answer. Flags problems; never replaces a value with its own guess."""
    values, sources = split_fields(raw)
    result = {key: values[key] for key in TEXT_KEYS}
    warnings = []

    for key in NUMBER_KEYS:
        value = to_number(values[key])
        if value is None and values[key] not in (None, ""):
            warnings.append(f"{key}: {values[key]!r} is not a single number, so it was left empty.")
        if value is not None and key != "months" and not sources[key]:
            warnings.append(f"{key}={value} was read without a printed label; double-check it on the bill.")
        result[key] = value
    if result["months"] is None:
        result["months"] = 1.0
        warnings.append("Billing period not found; assumed 1 month.")

    prev, cur, units = result["previous_reading"], result["current_reading"], result["units"]
    if None not in (prev, cur, units):
        try:
            gap = evaluate(f"{cur} - {prev} - {units}")
            if gap > 1 or gap < -1:
                consumed = evaluate(f"{cur} - {prev}")
                warnings.append(
                    f"current_reading - previous_reading = {consumed}, but billed units = {units}. "
                    "This can be a misread, an export/solar adjustment, or a billing error."
                )
        except CalculatorError as exc:
            warnings.append(f"Could not check units: {exc}")

    serious = (
        check_load(units, result["load_kw"], result["months"])
        + check_amount(result["total_amount_due"], units, result["load_kw"], result["months"])
        + check_category(result["category"])
    )
    warnings = serious + warnings  # most serious first

    try:
        BillData(**{key: result[key] for key in BillData.model_fields})
    except ValidationError as exc:
        missing = sorted({str(err["loc"][0]) for err in exc.errors()})
        if set(missing) <= {"previous_reading", "current_reading"}:
            # Units, state and total are enough to check the bill against the tariff.
            warnings.append("Meter readings could not be read; skip the units check and use billed units.")
        else:
            result["error"] = f"Could not read these fields from the bill: {', '.join(missing)}."

    result["sources"] = {key: label for key, label in sources.items() if label}
    result["warnings"] = warnings
    return result


@mcp.tool()
def extract_bill_data(image_path: str) -> str:
    """Reads a photo of an electricity bill and returns its data as JSON.

    Keys: discom, city, address, state, category, months, previous_reading, current_reading, units,
    total_amount_due, due_date, load_kw, sources (bill label each value came from),
    warnings (read these first), and error if required fields could not be read.
    """
    if not VISION_MODEL:
        return json.dumps({"error": "VISION_MODEL is not set in .env."})
    if not os.path.isfile(image_path):
        return json.dumps({"error": f"Image not found at {image_path}"})
    try:
        image = load_image(image_path)
    except Exception as exc:
        return json.dumps({"error": f"Failed to read image: {exc}"})

    try:
        raw = call_ollama(VISION_MODEL, PROMPT, [image_to_base64(image)])
        state_warnings = resolve_state(raw)
    except Exception as exc:
        return json.dumps({"error": f"Failed to call vision model {VISION_MODEL}: {exc}"})

    result = check(raw)
    result["warnings"] = state_warnings + result["warnings"]
    return json.dumps(result)


if __name__ == "__main__":
    mcp.run(transport="stdio")
