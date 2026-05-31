"""
plan.py — /api/plan endpoints with SSE streaming.
"""

import json
import asyncio
import sys
import os
from typing import AsyncGenerator

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pddl_tool.classifier import get_domain_for_task, extract_domain_name, save_domain_to_library
from pddl_tool.generator import generate_pddl, generate_problem_only, repair_pddl
from pddl_tool.solver import solve
from pddl_tool.explainer import explain_plan

router = APIRouter(prefix="/api")


class PlanRequest(BaseModel):
    task: str
    timeout: int = 30
    domain_override: str | None = None


def sse_event(event: str, data: dict) -> str:
    """Format a Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def run_pipeline(task: str, timeout: int, domain_override: str | None, session_id: str = "anonymous") -> AsyncGenerator[str, None]:
    """
    Run the full planning pipeline and yield SSE events at each stage.

    Events emitted:
        status      — pipeline stage updates
        pddl        — generated domain + problem PDDL
        plan        — solved plan steps
        explanation — plain English explanation
        done        — final summary
        error       — any failure
    """
    loop = asyncio.get_event_loop()

    # ── Stage 1: Domain classification / generation ──────────────────────────
    yield sse_event("status", {"stage": "generating", "message": "Generating PDDL..."})

    try:
        domain_name = None
        domain_pddl = None
        problem_pddl = None

        if domain_override:
            from pddl_tool.classifier import load_domain_pddl
            domain_pddl = load_domain_pddl(domain_override)
            domain_name = domain_override if domain_pddl else None

        if not domain_pddl:
            # Try library first
            domain_name, domain_pddl = await loop.run_in_executor(
                None, get_domain_for_task, task
            )

        if domain_name and domain_pddl:
            yield sse_event("status", {
                "stage": "generating",
                "message": f"Using domain: {domain_name} — generating problem..."
            })
            # Pass full domain PDDL so LLM generates a compatible problem
            problem_pddl = await loop.run_in_executor(
                None, generate_problem_only, task, domain_pddl
            )
        else:
            # Generate both domain and problem from scratch
            yield sse_event("status", {
                "stage": "generating",
                "message": "No library match — generating domain + problem..."
            })
            domain_pddl, problem_pddl = await loop.run_in_executor(
                None, generate_pddl, task
            )
            domain_name = "generated"

    except Exception as e:
        yield sse_event("error", {"message": f"PDDL generation failed: {e}"})
        return

    yield sse_event("pddl", {
        "domain": domain_pddl,
        "problem": problem_pddl,
        "domain_name": domain_name,
    })

    # ── Stage 2: Solve ───────────────────────────────────────────────────────
    yield sse_event("status", {"stage": "solving", "message": "Solving with Fast Downward..."})

    result = await loop.run_in_executor(None, solve, domain_pddl, problem_pddl, timeout)

    repaired = False
    if not result["found"]:
        yield sse_event("status", {
            "stage": "repairing",
            "message": "Plan not found — repairing PDDL..."
        })
        try:
            domain_pddl, problem_pddl = await loop.run_in_executor(
                None, repair_pddl, task, domain_pddl, problem_pddl, result["error"]
            )
            yield sse_event("pddl", {
                "domain": domain_pddl,
                "problem": problem_pddl,
                "domain_name": domain_name,
                "repaired": True,
            })
            result = await loop.run_in_executor(None, solve, domain_pddl, problem_pddl, timeout)
            repaired = True
        except Exception as e:
            yield sse_event("error", {"message": f"Repair failed: {e}"})
            return

    if not result["found"]:
        yield sse_event("error", {
            "message": "Could not find a plan. Try rephrasing the task.",
            "detail": result["error"],
        })
        return

    yield sse_event("plan", {
        "steps": result["plan"],
        "cost": result["plan_cost"],
        "time_s": round(result["time_s"], 3),
    })

    # ── Stage 3: Explain ─────────────────────────────────────────────────────
    yield sse_event("status", {"stage": "explaining", "message": "Generating explanation..."})

    try:
        explanation = await loop.run_in_executor(
            None, explain_plan, task, result["plan"], domain_pddl
        )
    except Exception:
        explanation = ""

    yield sse_event("explanation", {"text": explanation})

    # ── Auto-save generated domains to library ────────────────────────────────
    if domain_name == "generated":
        try:
            extracted_name = extract_domain_name(domain_pddl)
            saved_name = await loop.run_in_executor(
                None, save_domain_to_library, extracted_name, domain_pddl,
                f"Auto-generated domain for: {task[:80]}"
            )
            domain_name = saved_name
            yield sse_event("status", {
                "stage": "saved",
                "message": f"New domain '{saved_name}' saved to library",
            })
        except Exception:
            pass  # saving is best-effort, never block the response

    # ── Done ─────────────────────────────────────────────────────────────────
    yield sse_event("done", {
        "steps": result["plan"],
        "cost": result["plan_cost"],
        "time_s": round(result["time_s"], 3),
        "domain_used": domain_name,
        "repaired": repaired,
        "explanation": explanation,
    })

    # Save plan to DB after all events are sent (no more yields after this)
    try:
        from api.db.database import AsyncSessionLocal
        from api.db.crud import create_plan
        async with AsyncSessionLocal() as db:
            await create_plan(
                db,
                session_id=session_id,
                task=task,
                domain_pddl=domain_pddl,
                problem_pddl=problem_pddl,
                plan_steps=result["plan"],
                explanation=explanation,
                domain_used=domain_name or "generated",
                plan_cost=result["plan_cost"],
                solve_time_s=result["time_s"],
                repaired=repaired,
                status="success",
            )
    except Exception:
        pass


@router.post("/plan/stream")
async def plan_stream(req: PlanRequest, request: Request):
    """SSE endpoint — streams pipeline progress events."""
    if not req.task.strip():
        raise HTTPException(status_code=400, detail="Task cannot be empty.")

    session_id = request.headers.get("X-Session-ID", "anonymous")

    # Rate limit: 20 successful plans per day per session
    if session_id != "anonymous":
        try:
            from api.db.database import AsyncSessionLocal
            from api.db.crud import count_plans_today
            async with AsyncSessionLocal() as db:
                today_count = await count_plans_today(db, session_id)
            if today_count >= 20:
                raise HTTPException(
                    status_code=429,
                    detail="Daily limit of 20 plans reached. Come back tomorrow!",
                )
        except HTTPException:
            raise
        except Exception:
            pass  # never block planning if rate-limit check fails

    async def generator():
        async for event in run_pipeline(req.task.strip(), req.timeout, req.domain_override, session_id):
            if await request.is_disconnected():
                break
            yield event

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/domains/list")
async def list_domains():
    """List all available domains in the library."""
    from pddl_tool.classifier import list_available_domains, DOMAIN_DESCRIPTIONS
    names = list_available_domains()
    return {
        "domains": [
            {
                "name": name,
                "description": DOMAIN_DESCRIPTIONS.get(name, ""),
            }
            for name in sorted(names)
        ]
    }


@router.get("/domains/{name}")
async def get_domain(name: str):
    """Return the PDDL for a named domain."""
    from pddl_tool.classifier import load_domain_pddl
    pddl = load_domain_pddl(name)
    if not pddl:
        raise HTTPException(status_code=404, detail=f"Domain '{name}' not found.")
    return {"name": name, "pddl": pddl}
