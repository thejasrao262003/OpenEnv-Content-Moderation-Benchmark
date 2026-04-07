# 📄 ARCHITECTURE.md — System Design & Component Architecture

---

## 🧠 Overview

This document defines the **system architecture** for the AI Community Moderation Environment.

The system is designed to:

* comply with **OpenEnv specification**
* support **multi-step agent interaction**
* provide **deterministic evaluation**
* be easily deployable via **FastAPI + Docker**

---

## 🏗️ High-Level Architecture

### 🔹 Updated — Agent layer added

```text
┌─────────────────────────────────────────────────────────────────┐
│                        Agent Layer                              │
│                                                                 │
│   ┌──────────────────────┐    ┌──────────────────────────────┐  │
│   │  Gemini 2.5 Flash    │    │  Rule-based Baseline Agent   │  │
│   │  (agent/gemini_      │    │  (baseline/agent.py)         │  │
│   │   agent.py)          │    │                              │  │
│   └──────────┬───────────┘    └─────────────┬────────────────┘  │
│              │  /reset  /step  /agent/run    │  /baseline        │
└──────────────┼──────────────────────────────┼───────────────────┘
               │                              │
               ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FastAPI API (api/app.py)                  │
│  /reset  /step  /state  /tasks  /grader  /baseline  /agent/run  │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────▼────────────────────┐
        │          Environment Core (env/)        │
        └───────┬─────────────────┬───────────────┘
                │                 │
      ┌─────────▼──────┐  ┌───────▼───────┐
      │ State Manager   │  │ Reward Engine │
      └─────────┬──────┘  └───────────────┘
                │
      ┌─────────▼──────────┐
      │ Policy Engine       │
      └─────────┬──────────┘
                │
      ┌─────────▼──────────┐
      │ Data Generator      │
      └─────────────────────┘

      ┌─────────────────────────────────────┐
      │           Grader Engine             │
      └─────────────────────────────────────┘
```

---

## 📦 Core Modules

---

## 1. 🧠 Environment Core (`env/`)

### Responsibility

Implements OpenEnv interface:

* `reset()`
* `step(action)`
* `state()`

### Key File

```python id="f36n7z"
env/moderation_env.py
```

### Responsibilities

* orchestrates entire flow
* maintains episode lifecycle
* integrates all sub-components

---

## 2. 📊 State Manager (`env/state_manager.py`)

### Responsibility

Handles:

* current state representation
* updates after each action

### State Includes

* post content
* user history
* reports
* geo
* context

---

## 3. 🧾 Policy Engine (`env/policy_engine.py`)

### Responsibility

* implements rules from `POLICY.md`
* computes:

  * violation type
  * severity
  * expected action

### Key Function

```python id="0w8e3u"
def evaluate_policy(state) -> dict:
    return {
        "violation_type": ...,
        "severity": ...,
        "expected_action": ...
    }
```

---

## 4. 🧬 Data Generator (`env/data_generator.py`)

### Responsibility

* generates synthetic moderation scenarios
* ensures deterministic outputs

### Features

* template-based post generation
* context simulation (history, reports, geo)
* seed-controlled reproducibility

---

## 5. 🏆 Reward Engine (`env/reward_engine.py`)

### Responsibility

* computes step-wise rewards
* aligns with `REWARD.md`

### Input

* current state
* action
* ground truth

---

## 6. 🧪 Grader Engine (`graders/`)

### Responsibility

* computes final episode score
* aligns with `GRADERS.md`

### Key File

```python id="4bqj7f"
graders/grader.py
```

---

## 7. 🌐 API Layer (`api/`)

### Framework

* FastAPI

### Responsibilities

Expose endpoints:

| Endpoint      | Function                         |
| ------------- | -------------------------------- |
| `/reset`      | start new episode                |
| `/step`       | take action                      |
| `/state`      | current state                    |
| `/tasks`      | list tasks                       |
| `/grader`     | compute score                    |
| `/baseline`   | run rule-based baseline agent    |
| `/agent/run`  | run Gemini 2.5 Flash agent 🔹    |
| `/health`     | liveness check                   |

---

## 8. 🤖 Baseline Agent (`baseline/`)

### Responsibility

* runs simple rule-based heuristic agent
* produces reproducible benchmark without any LLM dependency

---

## 9. 🧠 Gemini Agent (`agent/`) — 🔹 Added

### Responsibility

* LLM-driven agent using **Gemini 2.5 Flash** (google-genai SDK)
* interacts with the environment via the same `/reset` and `/step` API
* uses multi-turn chat with a structured system prompt
* parses JSON action responses; falls back to `escalate` on parse failure

### Key Files

```
agent/gemini_agent.py   — GeminiAgent class
agent/prompts.py        — SYSTEM_PROMPT + build_turn_prompt()
```

### Design Constraint

The LLM is **only the decision-making layer**. Policy evaluation, reward
computation, and grading remain fully deterministic in the environment.

---

## 🔁 Data Flow

### 1. Reset

```text id="5v3sbh"
API → Environment.reset()
     → DataGenerator
     → StateManager
     → Initial State returned
```

---

### 2. Step

```text id="4cx7qf"
Agent Action → API
             → Environment.step()
             → StateManager update
             → PolicyEngine evaluate
             → RewardEngine compute
             → New State returned
```

---

### 3. Grading

```text id="yy9gsl"
Episode complete → GraderEngine
                → Score computed
                → Returned via API
```

---

## 🧠 Internal Interaction Flow

```text id="4l9p6p"
Action
  ↓
State Update
  ↓
Policy Evaluation
  ↓
Reward Calculation
  ↓
Next State
```

---

## 🧩 Component Dependencies

| Component     | Depends On            |
| ------------- | --------------------- |
| Environment   | State, Policy, Reward |
| State Manager | Data Generator        |
| Reward Engine | Policy Engine         |
| Grader        | Policy + Trajectory   |
| API           | Environment           |

---

## ⚙️ Execution Model

* single-threaded environment (MVP)
* stateless API with session tracking (in-memory)
* reproducible seeds for all scenarios

---

## 🐳 Deployment Architecture

```text id="0shdn3"
Docker Container
  ├── FastAPI Server
  ├── Environment Core
  ├── Graders
  └── Baseline Agent
```

Runs on:

* Hugging Face Spaces
* local Docker

---

## 🧠 Design Principles

### 1. Modularity

Each component is isolated and testable

---

### 2. Determinism

All outputs reproducible

---

### 3. Simplicity

Avoid unnecessary abstraction

---

### 4. Spec Compliance

Strict adherence to OpenEnv interface

---

## 🧠 One-Line Summary

> A modular, deterministic system where an environment core orchestrates policy evaluation, reward computation, and grading through well-defined components exposed via a FastAPI interface.

---
