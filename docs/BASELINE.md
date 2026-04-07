# BASELINE.md — Baseline Agent Specification

---

## Overview

Two baseline agents are provided:

| Agent | File | LLM? | Endpoint |
|---|---|---|---|
| Rule-based | `baseline/agent.py` | No | `GET /baseline` |
| Gemini 2.5 Flash | `agent/gemini_agent.py` | Yes | `POST /agent/run` |

---

## 1. Rule-based Baseline Agent (`baseline/agent.py`)

### Purpose

Establishes a reproducible lower-bound score with zero external dependencies.

### Strategy

| Difficulty | Investigation Plan | Classification | Decision |
|---|---|---|---|
| easy | fetch_user_history | keyword match | remove/allow |
| medium | fetch_user_history → check_policy_clause | keyword match | flag/escalate/allow |
| hard | fetch_user_history → fetch_thread_context → check_policy_clause | keyword match | remove/escalate |

### Classification Keywords

- **Harassment**: kill, murder, find you, watch your back, make you regret
- **Misinformation**: vaccines cause, 5G COVID, doctors are hiding, radiation weakens
- **Restricted**: scam, criminals, Ponzi, faked audit
- **Safe**: none of the above

### Expected Scores (approximate)

| Task | Expected Total |
|---|---|
| easy_harassment | 0.70–0.90 |
| medium_ambiguous | 0.55–0.75 |
| hard_misinformation | 0.50–0.70 |

### Invocation

```bash
curl "localhost:8000/baseline?task_id=easy_harassment&seed=42"
```

---

## 2. Gemini 2.5 Flash Agent (`agent/gemini_agent.py`)

### Purpose

Provides a realistic LLM-driven benchmark demonstrating multi-step reasoning.

### Model

`gemini-2.5-flash` via `google-genai` SDK

### Configuration

| Setting | Value |
|---|---|
| temperature | 0.0 (deterministic) |
| chat mode | multi-turn (full conversation history retained) |
| output format | JSON-only (enforced via system prompt) |

### System Prompt Summary

```
- Policy summary (violation types + severities)
- All 8 action types with semantics
- Decision guidelines (investigate → classify → decide)
- Output format: {"action_type": "...", "parameters": {...}}
```

### Per-Turn Prompt

Built dynamically from the current `Observation`:
- post content, user_id, reports, engagement, geo
- any context revealed so far (user_history, thread_context, policy_clause)
- current violation classification (if marked)

### Fallback Behaviour

If Gemini returns invalid JSON or an unknown action type, the agent
falls back to `escalate`. This prevents infinite loops and protects episode integrity.

### Required Environment Variables

```bash
GOOGLE_API_KEY=<your-key>
# or
GEMINI_API_KEY=<your-key>
```

### Invocation

```bash
curl -X POST localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"task_id": "hard_misinformation", "seed": 777}'
```

### Expected Scores (approximate)

| Task | Expected Total |
|---|---|
| easy_harassment | 0.80–1.0 |
| medium_ambiguous | 0.65–0.85 |
| hard_misinformation | 0.70–0.90 |

---

## Design Invariants

- **Environment stays deterministic**: policy, reward, grading are never delegated to the LLM
- **Agent output is structured**: only valid ActionType values are accepted
- **Seed reproducibility**: same seed always produces the same task scenario
- **No side effects**: running `/agent/run` or `/baseline` does not affect a concurrently running human episode (both reset the shared state manager, so they should not be called mid-episode)
