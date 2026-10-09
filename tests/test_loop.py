import pytest

from wattwise.loop import MISSING_TOOL_NAMES, skill_for_tool

TOOLS = ["calculate", "compute_bill", "get_tariff_info", "extract_bill_data"]
SKILLS = ["bill-checker", "explain-bill", "complaint-letter"]


@pytest.mark.parametrize(
    "tool_name, expected",
    [
        ("bill-checker", "bill-checker"),
        ("bill_checker", "bill-checker"),
        ("explain-bill", "explain-bill"),
        ("complaint_letter", "complaint-letter"),
    ],
)
def test_skill_called_as_tool_is_mapped_to_skill(tool_name, expected):
    assert skill_for_tool(tool_name, TOOLS, SKILLS) == expected


@pytest.mark.parametrize("tool_name", ["calculate", "compute_bill", "load_skill", None, "", "weather_lookup"])
def test_real_tools_and_unknown_names_are_not_skills(tool_name):
    assert skill_for_tool(tool_name, TOOLS, SKILLS) is None


@pytest.mark.parametrize("name", ["", "null", "none"])
def test_missing_tool_names(name):
    assert name in MISSING_TOOL_NAMES
