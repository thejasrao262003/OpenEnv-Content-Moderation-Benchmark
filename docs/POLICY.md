# 📄 POLICY.md — Synthetic Community Guidelines & Enforcement Rules

---

## 🧠 Overview

This document defines a **synthetic but deterministic policy framework** used to evaluate moderation decisions in the environment.

All:

* violation detection
* severity classification
* enforcement actions

are derived **strictly from this policy**.

This ensures:

* reproducibility
* deterministic grading
* zero subjectivity

---

## 🎯 Policy Design Goals

* Fully **rule-based and computable**
* Reflect real-world moderation challenges
* Support **multi-step reasoning**
* Enable **geo-specific variations**
* Provide **clear mapping → action**

---

## 🧾 Violation Taxonomy

Each post is classified into exactly one category:

---

### 1. 🚫 Harassment / Threats

#### Definition:

Content that includes:

* threats of violence
* abusive or degrading language

#### Detection Rules:

* contains threat keywords (`kill`, `hurt`, `destroy`)
* direct attack on a person/group

#### Severity:

* **High** → direct threat
* **Medium** → abusive language

---

### 2. ⚠️ Misinformation

#### Definition:

False or misleading claims presented as facts

#### Detection Rules:

* matches known misinformation templates
* contradicts known truth set (synthetic KB)

#### Severity:

* **High** → harmful misinformation (health, safety)
* **Medium** → general false claims

---

### 3. 🔞 Restricted / Sensitive Content

#### Definition:

Content requiring moderation but not outright removal

#### Detection Rules:

* borderline unsafe language
* controversial claims without clear harm

#### Severity:

* **Low to Medium**

---

### 4. ✅ Safe Content

#### Definition:

Content that does not violate any rules

---

## 🧪 Contextual Modifiers

The same post may lead to different outcomes based on context:

---

### 👤 User History

| Condition           | Effect                           |
| ------------------- | -------------------------------- |
| repeated violations | increase severity by +1          |
| clean history       | reduce severity by -1 (min: low) |

---

### 📊 Engagement / Virality

| Condition       | Effect                  |
| --------------- | ----------------------- |
| high engagement | increase severity by +1 |
| low engagement  | no change               |

---

### 🚩 Reports

| Condition                      | Effect                |
| ------------------------------ | --------------------- |
| reports > threshold            | trigger investigation |
| reports aligned with violation | reinforce severity    |

---

## 🌍 Geo-Specific Overrides

Policies may vary by region:

---

### 🇪🇺 EU

* stricter misinformation handling
* misinformation → always at least Medium severity

---

### 🇮🇳 India

* political content allowed unless explicitly harmful

---

### 🇺🇸 US

* broader allowance for controversial speech
* harassment rules unchanged

---

## 🎮 Action Mapping Rules

Final action is determined using:

```text id="cwlb5o"
(violation_type + severity + context) → action
```

---

### Action Table

| Violation      | Severity | Action |
| -------------- | -------- | ------ |
| harassment     | high     | remove |
| harassment     | medium   | remove |
| misinformation | high     | remove |
| misinformation | medium   | flag   |
| restricted     | medium   | flag   |
| restricted     | low      | allow  |
| safe           | -        | allow  |

---

### Escalation Rules

Escalate when:

* conflicting signals exist
* insufficient context
* severity borderline
* geo-policy conflict

---

## 🔁 Multi-Step Enforcement Logic

The agent is expected to follow:

```text id="j4z09p"
1. Observe post  
2. Investigate context (history, reports)  
3. Identify violation type  
4. Apply severity modifiers  
5. Decide action  
```

Skipping steps may result in lower reward.

---

## 🧾 Ground Truth Definition

Each scenario includes:

```json id="b9r1p4"
{
  "violation_type": "misinformation",
  "base_severity": "medium",
  "final_severity": "high",
  "expected_action": "remove"
}
```

This is computed using:

* base template label
* context modifiers
* geo overrides

---

## 🧪 Deterministic Evaluation Rules

* Exact match → score = 1.0
* Acceptable alternative → score = 0.5
* Incorrect → score = 0.0

Examples:

| Expected | Agent Action | Score |
| -------- | ------------ | ----- |
| remove   | remove       | 1.0   |
| remove   | escalate     | 0.5   |
| remove   | allow        | 0.0   |

---

## ⚠️ Edge Cases

### Ambiguity

* if multiple valid interpretations exist → escalation preferred

---

### Missing Context

* agent must request investigation before final decision

---

### Policy Conflict

* geo overrides take precedence

---

## 🧠 Key Principle

> All moderation decisions must be explainable through explicit policy rules — not intuition.

---

## 🧠 One-Line Summary

> A deterministic policy system that maps content + context → violation → severity → action.

---
