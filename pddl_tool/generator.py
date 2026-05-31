"""
generator.py — Natural language → PDDL domain + problem via LLM.
"""

import os
import re
from groq import Groq
from .validator import fix_pddl

_client = None

def _get_client():
    global _client
    if _client is None:
        key = os.environ.get("GROQ_API_KEY")
        if not key:
            raise EnvironmentError("GROQ_API_KEY not set.")
        _client = Groq(api_key=key)
    return _client


_SYSTEM_PROMPT = """\
You are an expert AI planner. Given a natural language task description, generate:
1. A PDDL domain file
2. A PDDL problem file

Strict rules:
- Use STRIPS-style PDDL only (no numeric fluents, no durative actions, no ADL unless needed)
- Use :precondition (singular, NOT :preconditions)
- Every opening parenthesis MUST have a matching closing parenthesis
- Every action's :effect and :precondition must be properly closed
- Predicates and actions must be consistent between domain and problem
- The problem must have a reachable goal from the given initial state
- Output ONLY the two PDDL blocks, no explanation, no commentary

Format your response exactly like this (nothing else):

```pddl-domain
(define (domain domain-name)
  (:requirements :strips :typing)
  (:types object-type)
  (:predicates
    (predicate-name ?x - object-type)
  )
  (:action action-name
    :parameters (?x - object-type)
    :precondition (and ...)
    :effect (and ...)
  )
)
```

```pddl-problem
(define (problem problem-name)
  (:domain domain-name)
  (:objects obj1 obj2 - object-type)
  (:init ...)
  (:goal (and ...))
)
```

Critical: always include :typing in requirements and always declare :types in the domain when using typed objects.
"""


def generate_problem_only(task_description: str, domain_pddl: str) -> str:
    """
    Generate only the PDDL problem file for an existing domain.
    Passes the full domain to the LLM so predicates/actions match exactly.

    Returns:
        problem_pddl as a string.
    """
    client = _get_client()

    prompt = f"""Given this existing PDDL domain, generate ONLY a problem file for the task below.
Use ONLY the predicates, actions, and types already defined in the domain — do not invent new ones.

Task: {task_description}

Domain:
{domain_pddl}

Output ONLY the problem block:

```pddl-problem
(define (problem ...)
  (:domain ...)
  (:objects ...)
  (:init ...)
  (:goal (and ...))
)
```"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=1024,
    )

    raw = response.choices[0].message.content

    # Try to extract problem block
    import re
    m = re.search(r"```pddl-problem\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    if m:
        return fix_pddl(m.group(1).strip())

    # Fallback: find (define (problem ...)) block
    m = re.search(r"\(define\s+\(problem\b.*", raw, re.DOTALL)
    if m:
        return fix_pddl(m.group(0).strip())

    raise ValueError("Could not parse problem PDDL from LLM response.")


def generate_pddl(task_description: str) -> tuple[str, str]:
    """
    Generate PDDL domain and problem from a natural language task.

    Args:
        task_description: Plain English description of the planning task.

    Returns:
        Tuple of (domain_pddl, problem_pddl) as strings.

    Raises:
        ValueError: If the LLM response cannot be parsed.
    """
    client = _get_client()

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"Task: {task_description}"},
        ],
        temperature=0.2,
        max_tokens=2048,
    )

    raw = response.choices[0].message.content
    domain, problem = _parse_pddl_blocks(raw)
    return fix_pddl(domain), fix_pddl(problem)


def repair_pddl(
    task_description: str,
    domain_pddl: str,
    problem_pddl: str,
    error_hint: str = "",
) -> tuple[str, str]:
    """
    Ask the LLM to fix a PDDL pair that failed to find a plan.

    Args:
        task_description: Original task.
        domain_pddl:      Current domain that failed.
        problem_pddl:     Current problem that failed.
        error_hint:       Optional error message from the planner.

    Returns:
        Repaired (domain_pddl, problem_pddl).
    """
    client = _get_client()

    hint = f"\nPlanner error: {error_hint}" if error_hint else ""
    prompt = f"""The following PDDL failed to find a plan for this task: {task_description}
{hint}

Check for these common mistakes:
- Missing (clear ?x) in stack/put-down effects (a placed block becomes clear on top)
- Missing (ontable) predicate when needed
- Unreachable goal given the initial state
- Inconsistent predicate names between domain and problem

Fix the PDDL so it correctly models the task and a plan can be found.

Current domain:
{domain_pddl}

Current problem:
{problem_pddl}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=2048,
    )

    raw = response.choices[0].message.content
    domain, problem = _parse_pddl_blocks(raw)
    return fix_pddl(domain), fix_pddl(problem)


def _parse_pddl_blocks(text: str) -> tuple[str, str]:
    """Extract domain and problem PDDL blocks from LLM output."""
    domain_match = re.search(
        r"```pddl-domain\s*(.*?)```", text, re.DOTALL | re.IGNORECASE
    )
    problem_match = re.search(
        r"```pddl-problem\s*(.*?)```", text, re.DOTALL | re.IGNORECASE
    )

    # Fallback: try to find two (define ...) blocks if markers are missing
    if not domain_match or not problem_match:
        defines = re.findall(r"\(define\s+\(domain.*?\n\)", text, re.DOTALL)
        if len(defines) < 2:
            defines = re.findall(r"\(define\b.*?(?=\(define\b|\Z)", text, re.DOTALL)
        if len(defines) >= 2:
            return defines[0].strip(), defines[1].strip()
        raise ValueError(
            "Could not parse PDDL blocks from LLM response.\n\n" + text[:500]
        )

    return domain_match.group(1).strip(), problem_match.group(1).strip()
