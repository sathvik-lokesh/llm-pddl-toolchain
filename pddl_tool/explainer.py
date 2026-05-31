"""
explainer.py — Turn a raw PDDL plan into a plain-English explanation via LLM.
"""

from groq import Groq
from .generator import _get_client


def explain_plan(task: str, plan: list[str], domain_pddl: str) -> str:
    """
    Generate a plain-English explanation of a PDDL plan.

    Args:
        task:        Original natural language task description.
        plan:        List of PDDL action strings from the planner.
        domain_pddl: Domain PDDL (for context on what actions mean).

    Returns:
        Human-readable explanation of the plan as a string.
    """
    if not plan:
        return "No plan was found."

    numbered = "\n".join(f"{i+1}. {a}" for i, a in enumerate(plan))

    prompt = f"""\
Task: {task}

PDDL Plan ({len(plan)} steps):
{numbered}

Domain context:
{domain_pddl[:800]}

Explain this plan in 3–5 clear sentences of plain English. \
Describe what happens step by step and why it achieves the goal. \
Do not use PDDL syntax in your explanation."""

    client = _get_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a helpful AI planning assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=512,
    )

    return response.choices[0].message.content.strip()
