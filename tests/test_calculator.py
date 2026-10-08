import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mcp_servers.calculator import CalculatorError, calculate, evaluate


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("2 + 3", 5.0),
        ("10 - 4", 6.0),
        ("6 * 7", 42.0),
        ("9 / 2", 4.5),
        ("-5 + 2", -3.0),
    ],
)
def test_normal_arithmetic(expression, expected):
    assert evaluate(expression) == expected


def test_decimals():
    assert evaluate("410*6.5") == 2665.0


def test_result_is_float():
    assert isinstance(evaluate("2 + 2"), float)


def test_operator_precedence():
    assert evaluate("2 + 3 * 4") == 14.0
    assert evaluate("(2 + 3) * 4") == 20.0
    assert evaluate("10 - 4 / 2") == 8.0


def test_round():
    assert evaluate("round(2665.456, 2)") == 2665.46
    assert evaluate("round(7.6)") == 8.0


def test_division_by_zero():
    with pytest.raises(CalculatorError, match="Division by zero"):
        evaluate("1 / 0")


@pytest.mark.parametrize("expression", ["", "   "])
def test_empty_input(expression):
    with pytest.raises(CalculatorError, match="empty"):
        evaluate(expression)


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os')",
        "__import__('os').system('ls')",
        "(1).__class__",
        "open('secrets.txt')",
        "abs(-1)",
        "'a' * 3",
        "True + 1",
        "2 ** 8",
        "[1, 2]",
        "x + 1",
        "lambda: 1",
    ],
)
def test_unsafe_or_unsupported_input(expression):
    with pytest.raises(CalculatorError):
        evaluate(expression)


def test_invalid_syntax():
    with pytest.raises(CalculatorError, match="Invalid expression"):
        evaluate("2 +* 3")


def test_too_long():
    with pytest.raises(CalculatorError, match="too long"):
        evaluate("1+" * 600 + "1")


def test_overflow():
    with pytest.raises(CalculatorError, match="too large"):
        evaluate("1e308 * 10")


def test_calculate_tool_returns_float():
    assert calculate("410*6.5") == 2665.0


def test_calculate_tool_reports_errors_instead_of_crashing():
    with pytest.raises(ToolError, match="Division by zero"):
        calculate("1 / 0")
