"""Independent arithmetic checking.

The brief's rule: *do not trust the same generation process to validate its own
calculation.* A model that produced "3/4 + 1/6 = 11/12" is exactly the wrong
thing to ask whether that is right — it will agree with itself, confidently,
including when it is wrong.

So this evaluates the arithmetic itself. No model, no network: the expression is
parsed to an AST, walked with a whitelist of nodes, and computed in exact
`Fraction` arithmetic so 1/3 stays a third rather than becoming 0.333…

Deliberately small. It handles the arithmetic a school maths worksheet contains
and refuses everything else rather than guessing — a checker that quietly
returns "cannot verify" for half the exercises would be worse than none, so it
says which it could not check.
"""

from __future__ import annotations

import ast
from fractions import Fraction


class CannotVerify(ValueError):
    """The expression is outside what this checker can evaluate exactly."""


_ALLOWED_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Pow: lambda a, b: a**b,
    ast.Mod: lambda a, b: a % b,
    ast.FloorDiv: lambda a, b: a // b,
}


def _eval(node: ast.AST) -> Fraction:
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise CannotVerify(f"unsupported constant: {node.value!r}")
        # str() first: Fraction(0.1) is not one tenth, Fraction("0.1") is.
        return Fraction(str(node.value))
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.USub):
            return -_eval(node.operand)
        if isinstance(node.op, ast.UAdd):
            return _eval(node.operand)
        raise CannotVerify("unsupported unary operator")
    if isinstance(node, ast.BinOp):
        op = _ALLOWED_BINOPS.get(type(node.op))
        if op is None:
            raise CannotVerify(f"unsupported operator: {type(node.op).__name__}")
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)) and right == 0:
            raise CannotVerify("division by zero")
        if isinstance(node.op, ast.Pow):
            if right.denominator != 1:
                raise CannotVerify("fractional exponents are not exact")
            if abs(right) > 64:
                raise CannotVerify("exponent too large to evaluate")
        return op(left, right)
    raise CannotVerify(f"unsupported expression: {type(node).__name__}")


def evaluate(expression: str) -> Fraction:
    """Evaluate an arithmetic expression exactly. Raises CannotVerify otherwise."""
    text = (expression or "").strip().replace("×", "*").replace("÷", "/").replace("−", "-")
    text = text.replace("^", "**").rstrip("=").strip()
    if not text:
        raise CannotVerify("empty expression")
    if len(text) > 200:
        raise CannotVerify("expression too long")
    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError as exc:
        raise CannotVerify(f"could not parse: {exc.msg}") from exc
    return _eval(tree)


def _as_fraction(value: str | int | float) -> Fraction:
    if isinstance(value, bool):
        raise CannotVerify("boolean is not a number")
    if isinstance(value, (int, float)):
        return Fraction(str(value))
    return evaluate(str(value))


def check(expression: str, claimed_answer: str | int | float) -> dict:
    """Is `claimed_answer` actually the value of `expression`?

    Returns a verdict of "correct", "incorrect" or "unverifiable", the computed
    value when there is one, and why it could not be checked when there is not.
    Unverifiable is reported honestly rather than being folded into "correct".
    """
    try:
        actual = evaluate(expression)
    except CannotVerify as exc:
        return {"verdict": "unverifiable", "expression": expression,
                "claimed": str(claimed_answer), "reason": str(exc)}
    try:
        claimed = _as_fraction(claimed_answer)
    except CannotVerify as exc:
        return {"verdict": "unverifiable", "expression": expression,
                "claimed": str(claimed_answer),
                "computed": _pretty(actual), "reason": f"claimed answer: {exc}"}

    return {
        "verdict": "correct" if actual == claimed else "incorrect",
        "expression": expression,
        "claimed": str(claimed_answer),
        "computed": _pretty(actual),
    }


def _pretty(value: Fraction) -> str:
    """Whole numbers as integers, thirds as thirds, the rest as decimals."""
    if value.denominator == 1:
        return str(value.numerator)
    as_decimal = float(value)
    if Fraction(str(as_decimal)) == value:
        return str(as_decimal)
    return f"{value.numerator}/{value.denominator}"
