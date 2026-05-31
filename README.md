# LLM-PDDL Toolchain

> Natural language → PDDL → optimal plan → plain English explanation

Takes a task description in plain English, generates a PDDL domain + problem via LLM, solves it with [Fast Downward](https://github.com/aibasel/downward) (A* + LM-Cut), and explains the result. Available as both a **web app** and a **CLI tool**.

---

## Web App

A browser-based planning studio with live streaming output.

### Pages

**`/app` — Planner**

The main interface. Type a task, hit Solve. The pipeline streams back in real time:

```
┌─────────────────────────────────────────────────────────────────┐
│  Task:  stack block A on block B, then put C on top of A   [→]  │
│  Options: Show PDDL | Timeout: 30s | Domain: Auto-detect        │
├──────────────────────────┬──────────────────────────────────────┤
│  Plan                    │  PDDL Viewer                         │
│  ─────────────────────   │  ─────────────────────────────────   │
│  1. (pick-up a)          │  Domain  │  Problem                  │
│  2. (stack a b)          │                                      │
│  3. (pick-up c)          │  (:action stack                      │
│  4. (stack c a)  ✓ goal  │    :parameters (?b1 ?b2 - block)    │
│                          │    :precondition ...                  │
│  Explanation             │    :effect ...)                       │
│  ─────────────────────   │                                      │
│  Pick up A, stack on B.  │                                      │
│  Pick up C, stack on A.  │                                      │
└──────────────────────────┴──────────────────────────────────────┘
```

- Status bar shows live pipeline stage (Generating → Solving → Explaining)
- PDDL viewer with Domain / Problem tabs, syntax highlighted
- If the first plan attempt fails, the system automatically repairs and retries

**`/domains` — Domain Library**

Grid of all available PDDL domains. Click any card to view the full PDDL. Domains are matched automatically at plan time — no manual selection needed.

| Domain | Description |
|--------|-------------|
| blocksworld | Stack and unstack coloured blocks |
| logistics | Move packages between cities via trucks and planes |
| gripper | Robot with two grippers moves balls between rooms |
| rover | Mars rover navigates terrain, samples, and transmits data |
| depots | Forklifts move crates between depots |
| ferry | Ferry transports cars across a river |
| hanoi | Towers of Hanoi — move disks respecting size order |
| satellite | Satellite points instruments at targets and takes images |
| freecell | Freecell card game |
| tyreworld | Change a flat tyre step by step |
| + IPC variants | blocksworld_ipc, logistics_ipc, depots_ipc, driverlog, zenotravel, ... |

Upload your own `.pddl` domain file via the upload button — it gets added to the library and used in future classifications.

**`/history` — Plan History**

All plans from your browser session, newest first. Click any plan to open a detail drawer showing the full plan steps, explanation, and the generated PDDL.

**`/dashboard` — Session Stats**

Aggregate stats for your session: total plans run, success rate, average steps per plan, most-used domain. Shows the last 10 plans inline.

**`/benchmarks` — Benchmarks**

Runs Fast Downward directly on hand-written IPC problem files (no LLM involved). Shows a table of domain / problem / found / steps / solve time. Useful for verifying the planner is working correctly after setup.

---

## Running the Web App

```bash
git clone https://github.com/sathvik44mysore-cmyk/llm-pddl-toolchain
cd llm-pddl-toolchain
pip install -r requirements.txt
export GROQ_API_KEY="your-key-here"
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000` in your browser.

---

## CLI

The same pipeline as a terminal tool.

### Install

```bash
pip install -e .
export GROQ_API_KEY="your-key-here"
```

### Usage

```bash
# Basic
pddl-tool "stack block A on block B, then put C on top of A"

# Show the generated PDDL
pddl-tool --show-pddl "move the package from warehouse to shop"

# Skip explanation
pddl-tool --no-explain "pick up the red block"

# Longer timeout for complex tasks
pddl-tool --timeout 60 "complex multi-step task"
```

### Example output

```
$ pddl-tool "stack block A on block B, then put block C on top of A"

Generating PDDL...   done
Solving...           done  (4 steps, 0.20s)

Plan:
    1. (pick-up a)
    2. (stack a b)
    3. (pick-up c)
    4. (stack c a)

Explanation:
  Pick up A and stack it on B. Then pick up C and place it on A.
  Tower C → A → B complete in 4 steps.
```

---

## How It Works

```
Natural language task
        │
        ▼
  Domain Classifier (LLM)
        │  checks built-in library first
        ├─ match found → fetch domain, generate problem only (fast)
        └─ no match   → generate domain + problem from scratch
        │
        ▼
  Syntax Fixer
        │  balance parentheses, fix :preconditions → :precondition
        ▼
  Fast Downward  (A* + LM-Cut heuristic)
        │  if no plan found → repair loop (LLM re-generates with error context)
        ▼
  Plan (list of actions)
        │
        ▼
  LLM — plain English explanation
```

**Domain library self-grows:** every successfully solved LLM-generated domain is saved to the library and reused for similar future tasks.

---

## Prerequisites

- Python 3.10+
- [Fast Downward](https://github.com/aibasel/downward) built locally (expected at `~/fast_downward/fast-downward.py`)
- [Groq API key](https://console.groq.com) (free tier, Llama 3.3 70B)

```bash
# Override Fast Downward path if needed
export FAST_DOWNWARD_PATH="/path/to/fast-downward.py"
```

---

## Project Structure

```
llm-pddl-toolchain/
├── pddl_tool/
│   ├── generator.py      # LLM → PDDL (domain + problem), repair loop
│   ├── solver.py         # Fast Downward subprocess runner
│   ├── validator.py      # PDDL syntax fixer
│   ├── explainer.py      # LLM → plain English plan explanation
│   ├── classifier.py     # domain library lookup via LLM
│   └── cli.py            # Click CLI entry point
│
├── api/
│   ├── main.py           # FastAPI app, page routes
│   ├── routes/
│   │   ├── plan.py       # POST /api/plan/stream  (SSE)
│   │   ├── domains.py    # GET/POST /api/domains
│   │   ├── history.py    # GET /api/plans
│   │   └── benchmarks.py # GET/POST /api/benchmarks
│   └── db/
│       ├── models.py     # SQLAlchemy models (plans, domains, benchmark_results)
│       ├── crud.py       # async DB helpers
│       └── database.py   # SQLite + aiosqlite engine
│
├── frontend/templates/
│   ├── base.html         # shared nav + layout
│   ├── landing.html      # /
│   ├── app.html          # /app  — main planner
│   ├── domains.html      # /domains
│   ├── history.html      # /history
│   ├── dashboard.html    # /dashboard
│   └── benchmarks.html   # /benchmarks
│
├── domains/              # 20 built-in PDDL domain files
├── benchmarks/
│   ├── run_benchmarks.py
│   └── problems/         # hand-written IPC problem files
└── examples/             # sample CLI outputs
```

---

## Limitations

- Works best on classical planning domains (blocksworld, logistics, gripper, rover, etc.)
- Complex tasks with many interacting objects may need rephrasing
- Fast Downward must be installed separately
- Groq free tier has rate limits (~30 req/min)
