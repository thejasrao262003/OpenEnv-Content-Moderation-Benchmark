# 📄 TASKS.md — Task Definitions & Difficulty Levels

---

## 🧠 Overview

This document defines the **three required tasks (easy → medium → hard)** for the moderation environment.

Each task:

* represents a realistic moderation scenario
* has **deterministic ground truth** derived from `POLICY.md`
* increases in complexity through:

  * ambiguity
  * context dependency
  * multi-step reasoning

---

## 🎯 Task Structure

Each task instance contains:

```json
{
  "post_content": "...",
  "user_history": [...],
  "reports": ...,
  "engagement": ...,
  "geo": "...",
  "thread_context": [...],
  "ground_truth": {
    "violation_type": "...",
    "final_severity": "...",
    "expected_action": "..."
  }
}
```

---

## 🟢 Task 1 — Clear Violations (Easy)

### 📌 Description

Simple, unambiguous moderation scenarios where:

* violation is obvious
* minimal context is required
* single-step reasoning is sufficient

---

### 🎯 Objective

Agent must:

* correctly identify violation type
* take correct final action

---

### 🧪 Example

```json
{
  "post_content": "I will kill you",
  "user_history": [],
  "reports": 5,
  "engagement": "low",
  "geo": "US",
  "ground_truth": {
    "violation_type": "harassment",
    "final_severity": "high",
    "expected_action": "remove"
  }
}
```

---

### ⚙️ Characteristics

* direct keyword-based violations
* no ambiguity
* no need for investigation

---

### 🧠 Skills Tested

* basic policy mapping
* correct action selection

---

## 🟡 Task 2 — Ambiguous Moderation (Medium)

### 📌 Description

Moderately complex scenarios with:

* ambiguous language
* borderline violations
* need for context

---

### 🎯 Objective

Agent must:

* investigate context (history, reports)
* resolve ambiguity
* avoid over- or under-moderation

---

### 🧪 Example

```json
{
  "post_content": "This product is a scam",
  "user_history": ["normal posts"],
  "reports": 0,
  "engagement": "medium",
  "geo": "US",
  "ground_truth": {
    "violation_type": "safe",
    "final_severity": "low",
    "expected_action": "allow"
  }
}
```

---

### ⚙️ Characteristics

* multiple plausible interpretations
* requires investigation actions
* penalties for premature decisions

---

### 🧠 Skills Tested

* contextual reasoning
* correct use of investigation steps
* balanced decision-making

---

## 🔴 Task 3 — Contextual & Geo-Aware Moderation (Hard)

### 📌 Description

Complex, real-world scenarios involving:

* misinformation
* repeated offenders
* high engagement (viral content)
* geo-specific policy differences

---

### 🎯 Objective

Agent must:

* perform multi-step reasoning
* incorporate all context signals
* apply geo-specific policy overrides
* optimize long-term moderation outcome

---

### 🧪 Example

```json
{
  "post_content": "Vaccines don’t work, avoid them",
  "user_history": ["previous misinformation", "warning issued"],
  "reports": 120,
  "engagement": "high",
  "geo": "EU",
  "ground_truth": {
    "violation_type": "misinformation",
    "final_severity": "high",
    "expected_action": "remove"
  }
}
```

---

### ⚙️ Characteristics

* requires full pipeline:

  * investigation
  * classification
  * severity adjustment
  * action selection

* conflicting signals possible

* geo overrides critical

---

### 🧠 Skills Tested

* multi-step reasoning
* policy application under constraints
* handling real-world complexity

---

## 🔁 Task Progression Summary

| Task   | Complexity | Key Challenge             |
| ------ | ---------- | ------------------------- |
| Easy   | Low        | Direct mapping            |
| Medium | Medium     | Ambiguity + context       |
| Hard   | High       | Multi-step + geo + impact |

---

## 🧪 Dataset Generation per Task

Each task uses **controlled synthetic data**:

### Easy

* 100–200 fixed samples
* deterministic templates

---

### Medium

* 200–300 samples
* variation in tone + context

---

### Hard

* 300–500 samples
* multi-factor scenarios
* geo + history + engagement

---

## 🎯 Episode Configuration

| Task   | Max Steps |
| ------ | --------- |
| Easy   | 3         |
| Medium | 5         |
| Hard   | 7–10      |

---

## 🧠 Success Criteria

An agent performs well if it:

* correctly identifies violations
* uses investigation steps when required
* avoids unnecessary actions
* selects optimal final action

---

## 🧠 One-Line Summary

> Tasks progress from simple rule-based moderation to complex, context-aware decision-making under real-world constraints.

---
