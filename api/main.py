"""
main.py — PlanForge FastAPI application entry point.
"""

import os
import sys

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
import jinja2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api.routes.plan import router as plan_router
from api.routes.domains import router as domains_router
from api.routes.history import router as history_router
from api.routes.benchmarks import router as benchmarks_router

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = FastAPI(title="PlanForge", version="0.1.0")

# Static files
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")),
    name="static",
)

_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(FRONTEND_DIR, "templates")),
    autoescape=True,
    cache_size=0,  # disable cache to avoid system Jinja2 LRU bug
)

def render(name: str, **ctx) -> HTMLResponse:
    tmpl = _jinja_env.get_template(name)
    return HTMLResponse(tmpl.render(**ctx))

# API routes — order matters: literal paths before parameterised ones
app.include_router(plan_router)
app.include_router(domains_router)
app.include_router(history_router)
app.include_router(benchmarks_router)


# ── Page routes ──────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def landing():
    return render("landing.html")


@app.get("/app", response_class=HTMLResponse)
async def planner():
    return render("app.html")


@app.get("/domains", response_class=HTMLResponse)
async def domains_page():
    return render("domains.html")


@app.get("/history", response_class=HTMLResponse)
async def history_page():
    return render("history.html")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    return render("dashboard.html")


@app.get("/benchmarks", response_class=HTMLResponse)
async def benchmarks_page():
    return render("benchmarks.html")


@app.on_event("startup")
async def startup():
    """Ensure DB tables exist on startup."""
    try:
        from api.db.database import init_db
        await init_db()
    except Exception as e:
        print(f"DB init warning: {e}")
