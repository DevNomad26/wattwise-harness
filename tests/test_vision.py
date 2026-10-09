import base64
import json

import pytest
from PIL import Image

from mcp_servers import vision


@pytest.fixture(autouse=True)
def vision_model(monkeypatch):
    """Tests must not depend on a local .env."""
    monkeypatch.setattr(vision, "VISION_MODEL", "test-model")

RAW = {
    "discom": {"label": "header", "value": "JAIPUR VIDYUT VITRAN NIGAM LIMITED"},
    "city": {"label": "Registered Office", "value": "Jaipur"},
    "address": {"label": "header", "value": "Vidyut Bhawan, Janpath, Jaipur | NAGAR HEERA PURA JPR"},
    "state": {"label": "city Jaipur", "value": "Rajasthan"},
    "months": {"label": "Billing Period", "value": 1},
    "previous_reading": {"label": "Previous Reading KWH Import", "value": 10432},
    "current_reading": {"label": "Present Reading KWH Import", "value": "11,234,473"},
    "units": {"label": "Net Billed Units", "value": 11223059},
    "total_amount_due": {"label": "Net Payable Amount up to Due Date", "value": "Rs 95,395,671"},
    "due_date": {"label": "Due Date", "value": "2024-04-29"},
}


def test_load_image_keeps_small_images(tmp_path):
    path = tmp_path / "bill.jpg"
    Image.new("RGB", (1080, 1432)).save(path)
    assert vision.load_image(str(path)).size == (1080, 1432)


def test_load_image_shrinks_large_photos(tmp_path):
    path = tmp_path / "phone.jpg"
    Image.new("RGB", (3000, 4000)).save(path)
    image = vision.load_image(str(path))
    assert image.width * image.height <= vision.MAX_PIXELS
    assert image.width / image.height == pytest.approx(0.75, abs=0.01)


def test_image_to_base64_returns_jpeg():
    assert base64.b64decode(vision.image_to_base64(Image.new("RGB", (10, 10))))[:2] == b"\xff\xd8"


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, None),
        (True, None),
        (7, 7.0),
        ("1,286 kWh", 1286.0),
        ("Rs -562.5", -562.5),
        ("NA", None),
        ("07-03-2024", None),
        ("10432 / 11234473", None),
    ],
)
def test_to_number(value, expected):
    assert vision.to_number(value) == expected


def test_split_fields_accepts_bare_values():
    values, sources = vision.split_fields({"units": 72, "state": {"label": "address", "value": "Gujarat"}})
    assert values["units"] == 72 and sources["units"] is None
    assert values["state"] == "Gujarat" and sources["state"] == "address"
    assert values["due_date"] is None


def test_check_keeps_model_values_and_flags_unit_gap():
    result = vision.check(RAW)
    assert result["state"] == "Rajasthan"
    assert result["current_reading"] == 11234473.0
    assert result["total_amount_due"] == 95395671.0
    assert result["sources"]["units"] == "Net Billed Units"
    assert "error" not in result
    assert len(result["warnings"]) == 1
    assert "11224041.0" in result["warnings"][0]  # 11234473 - 10432 via calculator


def test_check_flags_number_without_label():
    result = vision.check({**RAW, "units": {"label": None, "value": 655.5}})
    assert result["units"] == 655.5
    assert any("units=655.5 was read without a printed label" in w for w in result["warnings"])


def test_check_reports_missing_required_fields():
    result = vision.check({"units": {"label": "Units", "value": 5}})
    assert "state" in result["error"]
    assert "previous_reading" in result["error"]
    assert "Billing period not found; assumed 1 month." in result["warnings"]


def test_lookup_state_asks_text_only(monkeypatch):
    calls = []

    def fake_ollama(model, prompt, images=None):
        calls.append((prompt, images))
        return {"state": "Rajasthan"}

    monkeypatch.setattr(vision, "call_ollama", fake_ollama)
    assert vision.lookup_state("Jaipur", "JAIPLY VIDYUT VITRAN", "Janpath, Jaipur") == "Rajasthan"
    assert "City: Jaipur" in calls[0][0] and calls[0][1] is None
    assert "Addresses on the bill: Janpath, Jaipur" in calls[0][0]


def test_lookup_state_uses_address_alone(monkeypatch):
    monkeypatch.setattr(vision, "call_ollama", lambda model, prompt, images=None: {"state": "Rajasthan"})
    assert vision.lookup_state(None, None, "Janpath, Jaipur") == "Rajasthan"


def test_lookup_state_skips_without_city_or_discom(monkeypatch):
    monkeypatch.setattr(vision, "call_ollama", lambda *a, **k: pytest.fail("should not call model"))
    assert vision.lookup_state(None, None) is None


@pytest.mark.parametrize("answer", [{}, {"state": ""}, {"state": 5}])
def test_lookup_state_ignores_bad_answers(monkeypatch, answer):
    monkeypatch.setattr(vision, "call_ollama", lambda *a, **k: answer)
    assert vision.lookup_state("Jaipur", None) is None


def test_resolve_state_replaces_wrong_state(monkeypatch):
    monkeypatch.setattr(vision, "lookup_state", lambda city, discom, address=None: "Rajasthan")
    raw = {**RAW, "state": {"label": "Maharashtra", "value": "Maharashtra"}}
    warnings = vision.resolve_state(raw)
    assert raw["state"]["value"] == "Rajasthan"
    assert "city Jaipur" in raw["state"]["label"]
    assert warnings == ["Photo reading said state Maharashtra, but city/company point to Rajasthan; using Rajasthan."]


def test_resolve_state_no_warning_when_states_agree(monkeypatch):
    monkeypatch.setattr(vision, "lookup_state", lambda city, discom, address=None: "rajasthan ")
    assert vision.resolve_state(dict(RAW)) == []


def test_resolve_state_keeps_photo_state_when_lookup_fails(monkeypatch):
    monkeypatch.setattr(vision, "lookup_state", lambda city, discom, address=None: None)
    raw = dict(RAW)
    assert vision.resolve_state(raw) == []
    assert raw["state"] == RAW["state"]


def test_check_flags_date_as_reading_and_keeps_going():
    raw = {
        **RAW,
        "previous_reading": {"label": "Date of Previous reading", "value": "07-03-2024"},
        "current_reading": {"label": "Date of Current reading", "value": "07-04-2024"},
    }
    result = vision.check(raw)
    assert result["previous_reading"] is None and result["current_reading"] is None
    assert "error" not in result
    assert any("'07-03-2024' is not a single number" in w for w in result["warnings"])
    assert "Meter readings could not be read; skip the units check and use billed units." in result["warnings"]


@pytest.mark.parametrize(
    "units, load_kw, months",
    [(7440, 10, 1), (150, 2, 1), (None, 10, 1), (11223059, None, 1), (11223059, 0, 1), (11223059, 10, None)],
)
def test_check_load_no_warning(units, load_kw, months):
    assert vision.check_load(units, load_kw, months) == []


def test_check_load_flags_impossible_units():
    [warning] = vision.check_load(11223059, 10, 1)
    assert warning.startswith("IMPOSSIBLE UNITS")
    assert "7440.0 units" in warning  # 10 kW x 24 h x 31 days via calculator


def test_check_load_scales_with_months():
    assert vision.check_load(14000, 10, 2) == []  # limit is 14880 for two months


def test_check_puts_impossible_units_first():
    result = vision.check({**RAW, "load_kw": {"label": "Sanctioned Load", "value": "10(KW)"}})
    assert result["load_kw"] == 10.0
    assert result["warnings"][0].startswith("IMPOSSIBLE UNITS")
    assert len(result["warnings"]) == 2


def test_check_amount_flags_absurd_rs_per_unit():
    [warning] = vision.check_amount(790706190, 7391)
    assert warning.startswith("UNUSUAL AMOUNT")
    assert "106982.3 per unit" in warning  # via calculator


@pytest.mark.parametrize("total, units", [(655.25, 150), (524.38, 50), (None, 100), (500, 0), (500, None)])
def test_check_amount_normal_bills(total, units):
    assert vision.check_amount(total, units) == []


def test_check_amount_uses_load_when_units_missing():
    [warning] = vision.check_amount(800589850, None, 200, 1)
    assert warning.startswith("UNUSUAL AMOUNT")
    assert "148800.0 units" in warning and "5380.31 per unit" in warning


def test_check_amount_load_fallback_normal_bill():
    assert vision.check_amount(655.25, None, 2, 1) == []
    assert vision.check_amount(655.25, None, None, 1) == []


@pytest.mark.parametrize("category", [None, "", "domestic", "Residential", "LT-I Domestic"])
def test_check_category_domestic(category):
    assert vision.check_category(category) == []


def test_check_category_flags_industrial():
    [warning] = vision.check_category("industrial")
    assert warning.startswith("NON-DOMESTIC: this is a industrial connection")


def test_check_lists_serious_warnings_first():
    raw = {**RAW, "category": "industrial", "total_amount_due": {"label": "Bill Amount", "value": 790706190},
           "units": {"label": "Units", "value": 7391}}
    result = vision.check(raw)
    assert result["category"] == "industrial"
    assert result["warnings"][0].startswith("UNUSUAL AMOUNT")
    assert result["warnings"][1].startswith("NON-DOMESTIC")


def test_extract_bill_data_without_vision_model(monkeypatch):
    monkeypatch.setattr(vision, "VISION_MODEL", None)
    assert json.loads(vision.extract_bill_data("/any.jpg")) == {"error": "VISION_MODEL is not set in .env."}


def test_extract_bill_data_missing_file():
    assert "Image not found" in json.loads(vision.extract_bill_data("/no/such/bill.jpg"))["error"]


def test_extract_bill_data_end_to_end(tmp_path, monkeypatch):
    path = tmp_path / "bill.jpg"
    Image.new("RGB", (200, 200), "white").save(path)
    photo = {**RAW, "state": {"label": "Maharashtra", "value": "Maharashtra"}}

    def fake_ollama(model, prompt, images=None):
        return dict(photo) if images else {"state": "Rajasthan"}

    monkeypatch.setattr(vision, "call_ollama", fake_ollama)
    result = json.loads(vision.extract_bill_data(str(path)))
    assert result["state"] == "Rajasthan"
    assert result["units"] == 11223059.0
    assert "error" not in result
    assert result["warnings"][0].startswith("Photo reading said state Maharashtra")


def test_extract_bill_data_reports_ollama_failure(tmp_path, monkeypatch):
    path = tmp_path / "bill.jpg"
    Image.new("RGB", (50, 50)).save(path)

    def fail(model, prompt, images=None):
        raise ConnectionError("connection refused")

    monkeypatch.setattr(vision, "call_ollama", fail)
    assert "connection refused" in json.loads(vision.extract_bill_data(str(path)))["error"]
