# 📄 GRADERS.md — Deterministic Evaluation & Scoring Logic

---

## 🧠 Overview

This document defines the **grading system** used to evaluate agent performance across all tasks.

Grading is:

* **fully deterministic**
* derived strictly from `POLICY.md`
* consistent across runs (reproducible)

Each episode produces a **score between 0.0 and 1.0**.

---

## 🎯 Grading Objectives

The grader evaluates:

1. **Correctness of final action**
2. **Correct identification of violation type**
3. **Efficiency of decision-making (steps used)**
4. **Quality of action sequence (investigation vs shortcuts)**

---

## 🧩 Inputs to Grader

Each episode provides:

```json
{
  "trajectory": [
    {"action": "...", "step": 1},
    {"action": "...", "step": 2}
  ],
  "final_action": "...",
  "predicted_violation": "...",
  "ground_truth": {
    "violation_type": "...",
    "expected_action": "...",
    "final_severity": "..."
  },
  "steps_taken": 4,
  "max_steps": 7
}
```

---

## 🏆 Scoring Components

### 1. Final Action Score (Weight: 50%)

```python
if final_action == expected_action:
    score_action = 1.0
elif final_action == "escalate":
    score_action = 0.5
else:
    score_action = 0.0
```

---

### 2. Violation Classification Score (Weight: 20%)

```python
if predicted_violation == violation_type:
    score_violation = 1.0
else:
    score_violation = 0.0
```

---

### 3. Investigation Quality Score (Weight: 15%)

Evaluate whether agent used appropriate investigation steps.

```python
required_steps = ["fetch_user_history"]  # varies by task

used_steps = [a["action"] for a in trajectory]

score_investigation = len(set(required_steps) & set(used_steps)) / len(required_steps)
```

---

### 4. Efficiency Score (Weight: 15%)

Encourages optimal number of steps.

```python
efficiency_ratio = steps_taken / max_steps
score_efficiency = 1.0 - efficiency_ratio
```

---

## 🧮 Final Score Calculation

```python
final_score = (
    0.5 * score_action +
    0.2 * score_violation +
    0.15 * score_investigation +
    0.15 * score_efficiency
)
```

Final score is clipped to:

```python
final_score = max(0.0, min(1.0, final_score))
```

---

## 🎯 Task-Specific Grading Adjustments

### 🟢 Easy Task

* investigation not required
* efficiency weighted higher

```python
weights = {
  "action": 0.7,
  "violation": 0.2,
  "efficiency": 0.1
}
```

---

### 🟡 Medium Task

* investigation required
* balanced weights

```python
weights = {
  "action": 0.5,
  "violation": 0.2,
  "investigation": 0.2,
  "efficiency": 0.1
}
```

---

### 🔴 Hard Task

* full pipeline required
* investigation + reasoning critical

```python
weights = {
  "action": 0.4,
  "violation": 0.2,
  "investigation": 0.25,
  "efficiency": 0.15
}
```

---

## ⚠️ Penalty Rules

### ❌ False Negative (Critical)

* harmful content allowed

```python
if expected_action == "remove" and final_action == "allow":
    final_score -= 0.5
```

---

### ❌ False Positive

* safe content removed

```python
if expected_action == "allow" and final_action == "remove":
    final_score -= 0.2
```

---

### ❌ No Decision / Timeout

```python
if final_action is None:
    final_score = 0.0
```

---

## 🧪 Determinism Guarantees

* ground truth derived from `POLICY.md`
* no randomness in grading
* identical inputs → identical scores

---

## 🔁 Episode-Level vs Task-Level Score

### Episode Score

* computed using above formula

---

### Task Score

Average across all episodes:

```python
task_score = sum(episode_scores) / len(episode_scores)
```

---

### Final Benchmark Score

```python
final_score = (easy + medium + hard) / 3
```

---

## 🧠 Key Design Principle

> The grader must reward correct reasoning and penalize risky or lazy decisions, while remaining fully deterministic.

---

## 🧠 One-Line Summary

> A weighted, deterministic scoring system evaluating correctness, reasoning quality, and efficiency of moderation decisions.

---
