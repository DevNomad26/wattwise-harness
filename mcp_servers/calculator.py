"""Calculator MCP server: the only place the harness does arithmetic.

Allows numbers, + - * / ( ) and round(). Everything else is rejected.
"""

import ast
import math

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from simpleeval import SimpleEval

MAX_EXPRESSION_LENGTH = 1000

OPERATORS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.USub: lambda a: -a,
    ast.UAdd: lambda a: +a,
}
FUNCTIONS = {"round": round}

# Every AST node type an allowed expression can contain.
ALLOWED_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.Call,
    ast.Name,
    ast.Load,
    *OPERATORS,
)


class CalculatorError(ValueError):
    """Raised for invalid or unsafe expressions, with a message the model can read."""


def _check_syntax(expression: str) -> None:
    """Reject anything outside numbers, + - * / ( ) and round() before evaluating."""
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        raise CalculatorError(f"Invalid expression: {expression!r}") from None

    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_NODES):
            raise CalculatorError(
                f"Unsupported syntax ({type(node).__name__}). "
                "Use only numbers, + - * / ( ) and round()."
            )
        if isinstance(node, ast.Constant) and (
            isinstance(node.value, bool) or not isinstance(node.value, (int, float))
        ):
            raise CalculatorError(f"Only numbers are allowed, got {node.value!r}.")
        if isinstance(node, ast.Name) and node.id not in FUNCTIONS:
            raise CalculatorError(f"Unknown name {node.id!r}. Only round() is allowed.")
        if isinstance(node, ast.Call) and (
            not isinstance(node.func, ast.Name) or node.keywords
        ):
            raise CalculatorError("Only plain round(x) or round(x, digits) calls are allowed.")


def evaluate(expression: str) -> float:
    """Safely evaluate an arithmetic expression and return the result as a float."""
    if not isinstance(expression, str) or not expression.strip():
        raise CalculatorError("Expression is empty.")
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise CalculatorError(
            f"Expression is too long (max {MAX_EXPRESSION_LENGTH} characters)."
        )
    expression = expression.strip()
    _check_syntax(expression)

    evaluator = SimpleEval(operators=OPERATORS, functions=FUNCTIONS, names={})
    try:
        result = evaluator.eval(expression)
    except ZeroDivisionError:
        raise CalculatorError("Division by zero.") from None
    except Exception as exc:
        raise CalculatorError(f"Could not evaluate {expression!r}: {exc}") from None

    if isinstance(result, bool) or not isinstance(result, (int, float)):
        raise CalculatorError(f"Result is not a number: {result!r}")
    try:
        result = float(result)
    except OverflowError:
        raise CalculatorError("Result is too large.") from None
    if not math.isfinite(result):
        raise CalculatorError("Result is too large.")
    return result


mcp = MCPServer("calculator")


@mcp.tool()
def calculate(expression: str) -> float:
    """Evaluate an arithmetic expression using numbers, + - * / ( ) and round().

    Example: "round(410 * 6.5 + 120, 2)"
    """
    try:
        return evaluate(expression)
    except CalculatorError as exc:
        raise ToolError(str(exc)) from None


if __name__ == "__main__":
    mcp.run(transport="stdio")
