# 📄 DATA_MODEL.md — Data Structures & Typed Schemas

---

## 🧠 Overview

This document defines the **core data models** used in the moderation environment.

All models:

* are **strongly typed (Pydantic-ready)**
* align with OpenEnv requirements
* ensure **deterministic and structured data flow**

---

## 🧩 Core Model Categories

1. **Observation (State)**
2. **Action**
3. **Reward**
4. **Ground Truth**
5. **Trajectory**
6. **Task Configuration**

---

# 📥 1. Observation Model (State)

Represents what the agent sees at each step.

---

## Schema

```python id="z7v2gm"
class Observation(BaseModel):
    post_content: str
    user_history: List[str]
    reports: int
    engagement: Literal["low", "medium", "high"]
    geo: str
    thread_context: Optional[List[str]] = []
    policy_context: Optional[str] = None
    predicted_violation: Optional[str] = None
    final_action: Optional[str] = None
    step_count: int
    max_steps: int
```

---

## Notes

* `thread_context` and `policy_context` are revealed progressively
* `predicted_violation` is updated after classification
* `final_action` is set when episode ends

---

# 🎮 2. Action Model

Represents agent decisions.

---

## Schema

```python id="6y2kbb"
class Action(BaseModel):
    action_type: Literal[
        "fetch_user_history",
        "fetch_thread_context",
        "check_policy_clause",
        "mark_violation_type",
        "allow",
        "flag",
        "remove",
        "escalate"
    ]
    parameters: Optional[Dict[str, Any]] = None
```

---

## Examples

```json
{
  "action_type": "mark_violation_type",
  "parameters": {
    "violation_type": "misinformation"
  }
}
```

---

# 🏆 3. Reward Model

Represents reward returned after each step.

---

## Schema

```python id="b9p0kn"
class Reward(BaseModel):
    value: float
    reason: Optional[str]
```

---

## Example

```json
{
  "value": 0.5,
  "reason": "Correct violation classification"
}
```

---

# 🧾 4. Ground Truth Model

Defines deterministic truth for each scenario.

---

## Schema

```python id="ik2c6t"
class GroundTruth(BaseModel):
    violation_type: str
    base_severity: str
    final_severity: str
    expected_action: str
```

---

## Purpose

* used by Policy Engine
* used by Grader
* ensures deterministic evaluation

---

# 🔁 5. Trajectory Model

Tracks sequence of actions.

---

## Schema

```python id="l5v9j2"
class StepRecord(BaseModel):
    step: int
    action: str
    parameters: Optional[Dict[str, Any]]
    reward: float

class Trajectory(BaseModel):
    steps: List[StepRecord]
    final_action: Optional[str]
    predicted_violation: Optional[str]
```

---

## Purpose

* passed to Grader
* used for evaluation and debugging

---

# 🎯 6. Task Model

Defines task configuration.

---

## Schema

```python id="9c9o4r"
class TaskConfig(BaseModel):
    name: Literal["easy", "medium", "hard"]
    max_steps: int
    description: str
```

---

## Example

```json
{
  "name": "hard",
  "max_steps": 10,
  "description": "Contextual and geo-aware moderation"
}
```

---

# 📊 7. API Response Models

---

## Reset Response

```python id="1z8f0p"
class ResetResponse(BaseModel):
    state: Observation
    available_actions: List[str]
    done: bool
```

---

## Step Response

```python id="nvn4n6"
class StepResponse(BaseModel):
    state: Observation
    reward: float
    done: bool
    info: Dict[str, Any]
```

---

## Grader Response

```python id="i5r8v8"
class GraderResponse(BaseModel):
    score: float
    breakdown: Dict[str, float]
    steps_taken: int
    max_steps: int
```

---

# 🧠 Data Relationships

```text id="wrg7mj"
Action → State Update → Reward → Trajectory → Grader → Score
```

---

# ⚙️ Validation Rules

* `action_type` must be valid
* `parameters` must match action requirements
* `reward.value` must be numeric
* `step_count ≤ max_steps`
* `final_action` must be one of decision actions

---

# 🔁 Determinism Guarantees

* GroundTruth is fixed per scenario
* State transitions are rule-based
* No randomness in evaluation

---

# 🧠 Design Principles

### 1. Explicitness

All fields clearly defined

---

### 2. Extensibility

Easy to add new fields (e.g., new signals)

---

### 3. Consistency

Same structure across API + env

---

### 4. OpenEnv Compliance

Matches required interface patterns

---

## 🧠 One-Line Summary

> Strongly typed data models ensuring consistent, deterministic interaction between agent, environment, and evaluation system.

---
