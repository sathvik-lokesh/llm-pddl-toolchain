"""
solver.py — Run Fast Downward on a PDDL domain + problem and return the plan.
"""

import os
import re
import subprocess
import tempfile
import time

FAST_DOWNWARD = os.environ.get(
    "FAST_DOWNWARD_PATH",
    os.path.expanduser("~/fast_downward/fast-downward.py"),
)


def solve(domain_pddl: str, problem_pddl: str, timeout: int = 30) -> dict:
    """
    Run Fast Downward and return the plan.

    Args:
        domain_pddl:  PDDL domain string.
        problem_pddl: PDDL problem string.
        timeout:      Max seconds to wait for the planner.

    Returns:
        dict with keys:
            found      (bool)   — whether a plan was found
            plan       (list)   — list of action strings (empty if not found)
            plan_cost  (int)    — number of steps
            time_s     (float)  — wall-clock solve time
            error      (str)    — error message if failed
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        domain_path  = os.path.join(tmpdir, "domain.pddl")
        problem_path = os.path.join(tmpdir, "problem.pddl")
        sas_path     = os.path.join(tmpdir, "output.sas")
        plan_path    = os.path.join(tmpdir, "plan.txt")

        with open(domain_path, "w")  as f: f.write(domain_pddl)
        with open(problem_path, "w") as f: f.write(problem_pddl)

        cmd = [
            "python3", FAST_DOWNWARD,
            "--sas-file", sas_path,
            "--plan-file", plan_path,
            domain_path, problem_path,
            "--search", "astar(lmcut())",
        ]

        t0 = time.perf_counter()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir,
            )
        except subprocess.TimeoutExpired:
            return {
                "found": False, "plan": [], "plan_cost": 0,
                "time_s": timeout, "error": f"Timed out after {timeout}s",
            }
        elapsed = time.perf_counter() - t0

        if not os.path.exists(plan_path):
            stderr = result.stderr[-800:] if result.stderr else ""
            stdout = result.stdout[-800:] if result.stdout else ""
            return {
                "found": False, "plan": [], "plan_cost": 0,
                "time_s": elapsed,
                "error": _extract_error(stdout + "\n" + stderr),
            }

        plan = _parse_plan(plan_path)
        return {
            "found": True,
            "plan": plan,
            "plan_cost": len(plan),
            "time_s": elapsed,
            "error": "",
        }


def _parse_plan(plan_path: str) -> list[str]:
    """Read Fast Downward plan file and return list of action strings."""
    actions = []
    with open(plan_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith(";"):
                continue
            if line.startswith("(") and line.endswith(")"):
                actions.append(line)
    return actions


def _extract_error(output: str) -> str:
    """Pull the most relevant error line from FD output."""
    for line in reversed(output.splitlines()):
        line = line.strip()
        if any(kw in line.lower() for kw in ("error", "fail", "unsolvable", "parse")):
            return line
    return "Fast Downward returned no plan (see stderr for details)."
