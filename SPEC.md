# PlanForge: AI Planning Studio
## Full Product Specification v1.0

---

## 1. What Is This?

**PlanForge** is a web-based SaaS that lets anyone solve AI planning problems using plain English.

A user types: *"stack block A on B, then C on top of A"*  
PlanForge returns: a formally verified step-by-step plan, animated visually, explained in plain English.

Under the hood: LLM generates PDDL → Fast Downward solves it → LLM explains it.

**Target users:**
- AI/robotics researchers who want to quickly prototype planning domains
- Students learning AI planning (PDDL is notoriously hard to write by hand)
- Engineers who need a planning API for their robotics/automation stack

---

## 2. Core Technical Pipeline

```
User types task (natural language)
        │
        ▼
Domain Classifier (LLM)
  → Checks domain library for a matching domain
  → If match found: fetch domain, generate problem only (fast, reliable)
  → If no match: generate domain + problem from scratch
        │
        ▼
Syntax Fixer
  → Balances parentheses
  → Fixes :preconditions → :precondition
  → Validates typing consistency
        │
        ▼
Fast Downward (A* + LM-Cut heuristic)
  → Finds optimal plan
  → If no plan: trigger repair loop (LLM re-generates with error context)
        │
        ▼
Plan Explainer (LLM)
  → Plain English step-by-step explanation
        │
        ▼
Response streamed to frontend
  → PDDL appears live (SSE streaming)
  → Plan animates step by step
  → Explanation rendered
```

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend  (HTML + Tailwind CSS + htmx + vanilla JS)        │
│                                                              │
│  / (landing)  /app (planner)  /domains  /benchmarks         │
│  /dashboard   /history        /login                        │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP REST + SSE (streaming)
┌────────────────────────▼────────────────────────────────────┐
│  FastAPI Backend                                             │
│                                                              │
│  POST /api/plan              → run planning pipeline         │
│  GET  /api/plan/stream       → SSE stream of plan progress   │
│  GET  /api/domains           → list domain library           │
│  POST /api/domains/upload    → user uploads custom domain    │
│  GET  /api/benchmarks        → run/fetch benchmark results   │
│  GET  /api/history           → user's past plans             │
│  GET  /auth/google           → OAuth redirect                │
│  GET  /auth/google/callback  → OAuth callback                │
│  POST /auth/logout           → clear session                 │
└──────────┬──────────────────────┬───────────────────────────┘
           │                      │
┌──────────▼──────────┐  ┌────────▼────────────────────────────┐
│  SQLite Database    │  │  Planning Engine (pddl_tool/)        │
│                     │  │                                      │
│  users              │  │  generator.py   → LLM → PDDL        │
│  plans              │  │  solver.py      → Fast Downward      │
│  domains            │  │  explainer.py   → LLM → English      │
│  benchmark_results  │  │  validator.py   → syntax fixer       │
└─────────────────────┘  │  classifier.py  → domain lookup      │
                          └────────────────────────────────────┘
```

---

## 4. Database Schema

```sql
-- Users (created on first Google OAuth login)
CREATE TABLE users (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    google_id    TEXT UNIQUE NOT NULL,
    email        TEXT UNIQUE NOT NULL,
    name         TEXT,
    avatar_url   TEXT,
    tier         TEXT DEFAULT 'free',   -- 'free' | 'pro' (Stripe later)
    plans_today  INTEGER DEFAULT 0,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Plans (each run of the pipeline)
CREATE TABLE plans (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER REFERENCES users(id),
    task          TEXT NOT NULL,
    domain_pddl   TEXT,
    problem_pddl  TEXT,
    plan_steps    TEXT,                 -- JSON array of action strings
    explanation   TEXT,
    domain_used   TEXT,                 -- name of domain from library (or 'generated')
    plan_cost     INTEGER,
    solve_time_s  REAL,
    repaired      BOOLEAN DEFAULT FALSE,
    status        TEXT DEFAULT 'success', -- 'success' | 'failed'
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Domain Library
CREATE TABLE domains (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT UNIQUE NOT NULL,
    description  TEXT,
    domain_pddl  TEXT NOT NULL,
    source       TEXT DEFAULT 'builtin', -- 'builtin' | 'generated' | 'user'
    user_id      INTEGER REFERENCES users(id),  -- null for builtin
    use_count    INTEGER DEFAULT 0,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Benchmark Results
CREATE TABLE benchmark_results (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_name  TEXT,
    problem_name TEXT,
    found        BOOLEAN,
    plan_cost    INTEGER,
    solve_time_s REAL,
    ran_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/plan` | optional | Run full planning pipeline |
| GET | `/api/plan/{id}/stream` | optional | SSE stream of plan progress |
| GET | `/api/plans` | required | List user's plan history |
| GET | `/api/plans/{id}` | required | Get a specific plan |
| GET | `/api/domains` | none | List all domains in library |
| GET | `/api/domains/{name}` | none | Get domain PDDL |
| POST | `/api/domains/upload` | required | Upload custom domain |
| GET | `/api/benchmarks` | none | Get benchmark results |
| POST | `/api/benchmarks/run` | admin | Trigger benchmark run |
| GET | `/auth/google` | none | Initiate Google OAuth |
| GET | `/auth/google/callback` | none | OAuth callback |
| POST | `/auth/logout` | required | Logout |
| GET | `/api/me` | required | Current user info |

---

## 6. Frontend Pages

### `/`: Landing Page
- Hero: "Solve planning problems in plain English"
- Live demo (pre-recorded or live iframe of the planner)
- How it works (3-step diagram)
- Domain library preview
- "Try free, no credit card" CTA

### `/app`: Planner (main feature)
- Task input box (large, prominent)
- Options: show PDDL toggle, timeout slider, domain override dropdown
- Live output panel:
  - Status indicators (Generating... Solving... Explaining...)
  - PDDL viewer (syntax highlighted, streams in)
  - Plan steps (numbered, highlights current step)
  - Block/object animator (canvas, shows blocks moving)
  - Plain English explanation
- Share button (public link to this plan)

### `/domains`: Domain Library
- Grid of domain cards (Blocksworld, Logistics, Gripper, Rover, Depots...)
- Each card: name, description, number of predicates/actions, use count
- Search/filter
- Upload your own domain button
- Click domain → view full PDDL

### `/benchmarks`: Benchmarks
- Table: domain × problem × found? × plan length × solve time
- Overall success rate badge
- Comparison: LLM-generated PDDL vs hand-written PDDL

### `/dashboard`: User Dashboard (auth required)
- Stats: total plans run, success rate, favourite domain
- Recent plans (last 10)
- Saved domains

### `/history`: Plan History (auth required)
- Full list of user's plans
- Filter by domain, date, status
- Click to replay any plan

---

## 7. Built-in Domain Library (10 IPC domains)

| Domain | Description | Actions |
|--------|-------------|---------|
| blocksworld | Stack/unstack coloured blocks | pick-up, put-down, stack, unstack |
| logistics | Move packages between cities via trucks/planes | load, unload, drive, fly |
| gripper | Robot gripper moves balls between rooms | pick, drop, move |
| rover | Mars rover collects samples | navigate, sample, communicate |
| depots | Forklifts move crates in depots | drive, lift, drop, load |
| ferry | Ferry transports cars across river | board, sail, debark |
| hanoi | Towers of Hanoi | move-disk |
| freecell | Freecell card game | move-card |
| sokoban | Push boxes to goal positions | move, push |
| satellite | Satellite points instruments at targets | turn-to, switch-on, calibrate, take-image |

---

## 8. Rate Limits (Free Tier)

| Limit | Free | Pro (later) |
|-------|------|-------------|
| Plans per day | 20 | Unlimited |
| Max timeout | 30s | 120s |
| Custom domain uploads | 3 | Unlimited |
| API access | No | Yes |
| History retention | 7 days | Forever |

Rate limits enforced via `plans_today` counter on the users table, reset daily via a cron job.

---

## 9. Authentication Flow

1. User clicks "Login with Google"
2. Redirect to `/auth/google` → FastAPI redirects to Google OAuth consent
3. Google redirects to `/auth/google/callback` with auth code
4. FastAPI exchanges code for token → gets user profile (email, name, avatar)
5. Upsert user in DB → create session (JWT stored in httpOnly cookie)
6. Redirect to `/app`

**Unauthenticated users** can still use the planner (5 plans/day, no history saved).

---

## 10. File Structure

```
llm-pddl-toolchain/
├── pddl_tool/                  # Core planning engine (already built)
│   ├── __init__.py
│   ├── generator.py            # LLM → PDDL
│   ├── solver.py               # Fast Downward runner
│   ├── explainer.py            # LLM → English explanation
│   ├── validator.py            # PDDL syntax fixer
│   └── classifier.py           # Domain library lookup (to build)
│
├── api/                        # FastAPI backend (to build)
│   ├── main.py                 # App entry point, router registration
│   ├── routes/
│   │   ├── plan.py             # /api/plan endpoints
│   │   ├── domains.py          # /api/domains endpoints
│   │   ├── benchmarks.py       # /api/benchmarks endpoints
│   │   ├── auth.py             # /auth/google OAuth
│   │   └── users.py            # /api/me, /api/history
│   ├── db/
│   │   ├── database.py         # SQLite connection + init
│   │   ├── models.py           # SQLAlchemy models
│   │   └── crud.py             # DB helper functions
│   └── middleware/
│       ├── auth.py             # JWT session middleware
│       └── ratelimit.py        # Rate limiting middleware
│
├── frontend/                   # HTML + Tailwind + htmx (to build)
│   ├── static/
│   │   ├── css/main.css        # Tailwind output
│   │   └── js/
│   │       ├── planner.js      # SSE handler, UI updates
│   │       └── animator.js     # Block world canvas animation
│   └── templates/
│       ├── base.html           # Base layout (nav, footer)
│       ├── landing.html        # / landing page
│       ├── app.html            # /app planner
│       ├── domains.html        # /domains library
│       ├── benchmarks.html     # /benchmarks
│       ├── dashboard.html      # /dashboard
│       └── history.html        # /history
│
├── domains/                    # Built-in PDDL domain files (to build)
│   ├── blocksworld.pddl
│   ├── logistics.pddl
│   ├── gripper.pddl
│   ├── rover.pddl
│   ├── depots.pddl
│   ├── ferry.pddl
│   ├── hanoi.pddl
│   ├── freecell.pddl
│   ├── sokoban.pddl
│   └── satellite.pddl
│
├── benchmarks/                 # Benchmark problems + runner
│   ├── problems/               # PDDL problem files per domain
│   └── run_benchmarks.py
│
├── examples/                   # Sample CLI outputs (already have)
├── SPEC.md                     # This file
├── README.md
├── pyproject.toml
└── requirements.txt
```

---

## 11. Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | FastAPI | Async, fast, automatic OpenAPI docs |
| Database | SQLite → PostgreSQL | Simple now, easy to migrate |
| ORM | SQLAlchemy | Standard, works with both DBs |
| Auth | authlib (Google OAuth) + JWT | Simple, well-maintained |
| Frontend | HTML + Tailwind CSS + htmx | No React needed, feels dynamic |
| LLM | Groq (Llama 3.3 70B) | Free tier, fast, good at PDDL |
| Planner | Fast Downward | Industry standard, A* + LM-Cut |
| Streaming | Server-Sent Events (SSE) | Simple, built into browsers |
| Hosting | Railway (free tier) | One-command deploy from git |
| Payments | Stripe (Phase 2) | Industry standard |

---

## 12. Development Phases

### Phase 1: Core Web App (Days 1–2)
- [ ] FastAPI backend with `/api/plan` endpoint
- [ ] SSE streaming of pipeline progress
- [ ] Basic HTML frontend, task input + output panel
- [ ] Domain library (10 PDDL files + classifier)
- [ ] SQLite DB with plans table

### Phase 2: Auth + User Features (Days 3–4)
- [ ] Google OAuth flow
- [ ] User sessions (JWT cookie)
- [ ] Plan history saved per user
- [ ] Dashboard page
- [ ] Rate limiting (free tier)

### Phase 3: Polish + Deploy (Day 5)
- [ ] Block world canvas animator
- [ ] Benchmarks page
- [ ] Landing page
- [ ] Deploy to Railway
- [ ] Custom domain upload

### Phase 4: Payments (Later)
- [ ] Stripe integration
- [ ] Pro tier feature gates
- [ ] Billing dashboard

---

## 13. What Makes This Different

1. **Domain library with classifier**: not just "LLM writes PDDL", but a growing knowledge base of validated domains. Gets smarter over time.
2. **Repair loop**: automatically fixes failed plans by sending error context back to LLM.
3. **Live streaming**: PDDL generates character by character, plan steps highlight in real time.
4. **Formal verification**: every plan is provably correct (Fast Downward guarantees optimality).
5. **Self-growing**: every successful LLM-generated domain gets saved. The system improves with use.

---

## 14. Notes for LLMs Working on This

- All PDDL must use `:requirements :strips :typing` and declare `:types`
- Fast Downward binary is at `~/fast_downward/fast-downward.py`
- Groq API key is in `$GROQ_API_KEY` environment variable
- Google OAuth credentials need to be set: `$GOOGLE_CLIENT_ID` and `$GOOGLE_CLIENT_SECRET`
- JWT secret: `$JWT_SECRET`
- DB path: `./planforge.db`
- Never hardcode secrets, always read from environment
- Use async FastAPI routes (async def) for all I/O-bound operations
- SSE endpoint must set `Content-Type: text/event-stream`
- Frontend uses htmx for dynamic updates, avoid writing raw JS unless necessary
