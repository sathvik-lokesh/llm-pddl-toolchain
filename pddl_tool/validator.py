"""
validator.py — Lightweight PDDL syntax fixer.
Corrects common LLM-generated PDDL mistakes before sending to Fast Downward.
"""

import re


def fix_pddl(pddl: str) -> str:
    """Apply common fixes to LLM-generated PDDL."""
    pddl = _fix_precondition_keyword(pddl)
    pddl = _balance_parentheses(pddl)
    return pddl


def _fix_precondition_keyword(pddl: str) -> str:
    """Replace :preconditions with :precondition (PDDL standard)."""
    return re.sub(r":preconditions\b", ":precondition", pddl)


def _balance_parentheses(pddl: str) -> str:
    """Append missing closing parentheses to balance the expression."""
    depth = 0
    for ch in pddl:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
    if depth > 0:
        pddl = pddl.rstrip() + ")" * depth
    return pddl


def check_balanced(pddl: str) -> bool:
    """Return True if parentheses are balanced."""
    depth = 0
    for ch in pddl:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if depth < 0:
            return False
    return depth == 0
