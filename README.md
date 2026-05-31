# LLM-PDDL Toolchain

> Natural language → PDDL → plan → plain English explanation

A CLI tool that takes a task description in plain English, generates a PDDL domain and problem using an LLM, solves it with [Fast Downward](https://github.com/aibasel/downward), and explains the resulting plan in plain English.

---

## Demo

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
  The plan starts by picking up block A and stacking it on block B.
  Then block C is picked up and placed on top of A, completing the
  tower C → A → B as required.
```

```
$ pddl-tool "a robot needs to move a package from the warehouse to the shop"

Generating PDDL...   done
Solving...           done  (3 steps, 0.38s)

Plan:
    1. (pick-up robot1 package1 warehouse)
    2. (move-robot robot1 warehouse shop)
    3. (drop robot1 package1 shop)

Explanation:
  The robot picks up the package at the warehouse, moves to the shop,
  and drops the package there — achieving delivery in 3 steps.
```

---

## How It Works

```
Natural language task
        │
        ▼
  LLM (Llama 3.3 70B via Groq)
        │  generates
        ▼
  PDDL domain + problem
        │
        ▼
  Syntax fixer (parenthesis balance, keyword corrections)
        │
        ▼
  Fast Downward (A* + LM-Cut heuristic)
        │  if no plan found → repair loop
        ▼
  Plan (list of actions)
        │
        ▼
  LLM (plain English explanation)
        │
        ▼
  Output to terminal
```

**Repair loop:** if the planner cannot find a plan, the PDDL is sent back to the LLM with the error context and common fix hints. This handles the most frequent LLM mistake (missing `clear` predicate after stacking) automatically.

---

## Installation

### Prerequisites

- Python 3.10+
- [Fast Downward](https://github.com/aibasel/downward) built locally
- A [Groq API key](https://console.groq.com) (free tier)

### Install

```bash
git clone https://github.com/sathvik44mysore-cmyk/llm-pddl-toolchain
cd llm-pddl-toolchain
pip install -e .
```

### Configure

```bash
export GROQ_API_KEY="your-key-here"

# Optional: if Fast Downward is not at ~/fast_downward/fast-downward.py
export FAST_DOWNWARD_PATH="/path/to/fast-downward.py"
```

---

## Usage

```bash
# Basic
pddl-tool "your task description"

# Show the generated PDDL
pddl-tool --show-pddl "move the box from room A to room B"

# Skip the plain-English explanation
pddl-tool --no-explain "pick up the red block"

# Increase planner timeout (default: 30s)
pddl-tool --timeout 60 "complex multi-step task"
```

---

## Project Structure

```
llm-pddl-toolchain/
├── pddl_tool/
│   ├── cli.py          # Click CLI entry point
│   ├── generator.py    # LLM → PDDL generation + repair
│   ├── solver.py       # Fast Downward subprocess runner
│   ├── explainer.py    # LLM → plain English explanation
│   └── validator.py    # Syntax fixer (parentheses, keywords)
├── examples/           # Sample inputs and outputs
├── pyproject.toml      # pip-installable package config
└── requirements.txt
```

---

## Limitations

- Works best on classical planning domains (Blocksworld, Logistics, Gripper)
- Complex tasks with many interacting objects may require rephrasing
- Depends on Groq free tier (rate limits apply for heavy use)
- Fast Downward must be installed separately

---

## Author

**Sathvik** — Masters in IT, University of Stuttgart
