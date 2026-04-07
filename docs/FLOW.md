# 📄 FLOW.md — Runtime Flow & Execution Logic

---

## 🧠 Overview

This document defines the **end-to-end execution flow** of the moderation environment.

It describes:

* how an episode starts
* how actions are processed
* how state evolves
* how rewards and grading are computed

This serves as a **step-by-step guide for implementation**.

---

## 🔁 High-Level Flow

```text id="h7n2ka"
Client → /reset → initial state
       → /step → action loop
       → environment updates state
       → rewards computed
       → repeat until done
       → /grader → final score
```

---

## 🚀 1. Episode Initialization (`/reset`)

### Flow

```text id="h2fg8r"
API (/reset)
  ↓
Environment.reset()
  ↓
DataGenerator.generate(task_level)
  ↓
StateManager.initialize(state)
  ↓
PolicyEngine.compute_ground_truth(state)
  ↓
Return initial observation
```

---

### Output

```json
{
  "state": {...},
  "available_actions": [...]
}
```

---

## 🔄 2. Action Loop (`/step`)

Each step follows this pipeline:

---

### Step 1: Receive Action

```text id="cgm4kr"
Client → API (/step) → action payload
```

---

### Step 2: Validate Action

```text id="55zh0y"
if action not in allowed_actions:
    return error / penalty
```

---

### Step 3: Apply Action

```text id="p6p9d3"
StateManager.update(action)
```

Examples:

* fetch_user_history → populate state
* mark_violation_type → store prediction
* final decision → mark episode complete

---

### Step 4: Policy Evaluation

```text id="mw30qg"
PolicyEngine.evaluate(state)
```

Outputs:

* violation type
* severity
* expected action

---

### Step 5: Compute Reward

```text id="ctm69v"
RewardEngine.compute(
    state,
    action,
    ground_truth,
    step_count
)
```

---

### Step 6: Check Termination

Episode ends if:

```text id="ak2i8c"
- final action taken (allow/remove/etc)
OR
- max steps reached
```

---

### Step 7: Return Response

```json
{
  "state": {...},
  "reward": ...,
  "done": true/false,
  "info": {...}
}
```

---

## 🔁 3. State Evolution

State changes dynamically based on actions:

---

### Example Flow

```text id="flp5kp"
Initial State:
- post only

↓ fetch_user_history

Updated State:
- post + history

↓ check_policy_clause

Updated State:
- policy context added

↓ mark_violation_type

Updated State:
- predicted violation stored

↓ remove

Episode ends
```

---

## 🧠 4. Internal Data Tracking

The environment maintains:

```json
{
  "trajectory": [...],
  "step_count": ...,
  "predicted_violation": ...,
  "final_action": ...
}
```

---

## 🏁 5. Episode Completion

Triggered when:

* agent performs final action
* or step limit reached

---

## 🧪 6. Grading Flow (`/grader`)

```text id="l8uk6m"
Client → /grader
       ↓
GraderEngine.evaluate(trajectory, ground_truth)
       ↓
Score returned
```

---

### Output

```json
{
  "score": 0.82,
  "breakdown": {
    "action": ...,
    "violation": ...,
    "efficiency": ...
  }
}
```

---

## 🤖 7. Baseline Flow (`/baseline`)

```text
API → rule-based baseline agent
     → runs full episode loop (investigate → classify → decide)
     → returns graded result
```

---

## 🧠 7b. Gemini Agent Flow (`/agent/run`) — 🔹 Added

```text
POST /agent/run  { task_id, seed }
  ↓
GeminiAgent.run(task_config)
  ↓
StateManager.reset(task_config)   ← deterministic environment
  ↓
LOOP until done:
  build_turn_prompt(observation)
    ↓
  Gemini 2.5 Flash (multi-turn chat)
    system_instruction = SYSTEM_PROMPT
    user message       = current observation
    ↓
  Parse JSON response → Action
    (fallback: escalate on parse failure)
    ↓
  StateManager.step(action)
    ↓
  RewardEngine.compute(action, ...)   ← deterministic
    ↓
  Update observation (progressive reveal)
  ↓
Grader.score(episode_state)           ← deterministic
  ↓
Return BaselineResult { task_id, seed, score, trajectory }
```

### Key Invariant

The LLM **never touches** policy logic, reward computation, or grading.
It only outputs a JSON action. The environment evaluates that action
deterministically against ground truth.

### Prompt Structure

```
SYSTEM_PROMPT (static):
  - policy summary
  - allowed action types and their semantics
  - output format (JSON only)
  - decision guidelines

Per-turn user message (dynamic):
  - current observation fields
  - any context already revealed (user history, thread, policy clause)
  - classification so far (if mark_violation_type was called)
```

---

## 🔄 8. Task Flow

```text id="kq8c9h"
Client → /tasks
       ↓
Return:
- task list
- schema for actions
```

---

## 🧠 9. Full End-to-End Flow

```text id="4m5myi"
1. /reset
2. agent receives state
3. agent → /step
4. env updates state
5. reward returned
6. repeat steps
7. episode ends
8. /grader computes score
9. optional: /baseline runs benchmark
```

---

## ⚙️ Error Handling Flow

---

### Invalid Action

```text id="lg3y1c"
Action invalid → penalty → continue episode
```

---

### Max Steps Reached

```text id="79fcrn"
Episode forced to end → final score computed
```

---

### Missing Required Step

Handled via:

* lower reward
* grader penalty

---

## 🧠 Design Guarantees

* deterministic flow
* no hidden state transitions
* explicit state updates
* reproducible outcomes

---

## 🧠 One-Line Summary

> A structured execution pipeline where agent actions drive state transitions, rewards are computed step-wise, and final performance is evaluated deterministically.

---
