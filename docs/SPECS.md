# 📄 SPECS.md — AI Community Moderation & Escalation Environment

---

## 🧠 Overview

This project defines an **OpenEnv-compliant environment** that simulates a real-world **content moderation and policy enforcement system**.

The agent operates as a moderation decision-maker responsible for:

* identifying policy violations
* investigating context
* enforcing appropriate actions
* handling ambiguity under platform rules

Unlike static classification tasks, this environment models moderation as a **multi-step decision process** with **deterministic grading derived from a formal policy document**.

---

## 🎯 Problem Definition

Given:

* a user-generated post
* associated context (user history, reports, geo, thread)
* a predefined policy document

The agent must:

1. Investigate the content
2. Identify violation type (if any)
3. Decide and execute an appropriate moderation action

---

## 🧩 Core Design Principles

### 1. Deterministic Evaluation

All decisions are evaluated against:

* a **synthetic policy document**
* predefined violation taxonomy
* rule-based ground truth

No subjective scoring is allowed.

---

### 2. Multi-Step Decision Process

```text
observe → investigate → classify → decide → enforce
```

Each step contributes to final reward.

---

### 3. Partial Observability

The agent does not initially receive full information and must:

* request additional context
* inspect user behavior
* interpret signals over time

---

### 4. Real-World Alignment

The environment reflects real moderation challenges:

* misinformation
* harassment
* context-dependent violations
* geo-specific policy differences

---

## 🧱 Environment Components

### 📥 State (Observation)

Each state includes:

* `post_content`: text of the content
* `user_history`: last N posts + violation count
* `reports`: number and type of reports
* `engagement`: likes, shares, virality score
* `geo`: region identifier (e.g., IN, EU, US)
* `thread_context`: previous messages (optional)
* `policy_context`: relevant policy snippets (optional)

---

### 🎮 Action Space

#### Investigation Actions

* `fetch_user_history`
* `fetch_thread_context`
* `check_policy_clause`

#### Classification Actions

* `mark_violation_type` (harassment, misinformation, safe, etc.)

#### Decision Actions

* `allow`
* `flag`
* `remove`
* `escalate`

---

### 🔁 Episode Flow

1. `reset()` initializes a moderation scenario
2. Agent receives initial state
3. Agent performs a sequence of actions
4. Environment updates state accordingly
5. Rewards are assigned incrementally
6. Episode ends when:

   * final decision is made, or
   * max steps reached

---

## 🏆 Reward Design

### Step-level Rewards

* correct investigation step → +0.2
* correct violation classification → +0.5
* unnecessary action → -0.1

### Final Decision Rewards

* correct action → +1.0
* acceptable but suboptimal → +0.5
* false positive → -0.5
* false negative → -2.0

### Escalation Handling

* correct escalation → +0.5
* unnecessary escalation → -0.2

---

## 🎯 Tasks

### 🟢 Task 1 — Clear Violations (Easy)

* explicit harmful content
* no ambiguity
* minimal context required

**Goal:** correct identification and action

---

### 🟡 Task 2 — Ambiguous Content (Medium)

* sarcasm, criticism, borderline cases
* requires context and policy reasoning

**Goal:** balanced moderation decision

---

### 🔴 Task 3 — Contextual & Geo-Aware Moderation (Hard)

* misinformation, repeated offenders, viral posts
* geo-specific policy differences
* multi-step reasoning required

**Goal:** optimize long-term safety and correctness

---

## 🧪 Grading Strategy

Each task includes a **deterministic grader** that:

* compares agent decisions to ground truth derived from policy rules
* assigns score between **0.0 and 1.0**
* accounts for:

  * correctness
  * efficiency
  * decision quality

---

## 🧬 Data Creation Strategy

To ensure deterministic grading and reproducibility, all data in the environment is **synthetically generated using controlled templates and rules**.

### 1. Template-Based Generation

Posts are generated using predefined templates mapped to violation types:

```python
TEMPLATES = {
  "harassment": ["I will hurt you", "You are worthless"],
  "misinformation": ["Vaccines don't work", "This cures all diseases"],
  "safe": ["Had a great day!", "Check out this cool product"]
}
```

Each template includes:

* known violation label
* severity level
* expected action

---

### 2. Controlled Variations

To increase diversity while preserving ground truth:

* tone variation (angry, sarcastic, neutral)
* noise injection (irrelevant text, emojis, typos)
* paraphrasing using rule-based transformations

---

### 3. Context Generation

Additional signals are generated programmatically:

* **user_history**

  * prior violations count
  * repeated behavior patterns

* **reports**

  * number of reports aligned with severity

* **engagement**

  * virality score (affects task difficulty)

* **geo**

  * region-specific overrides (policy-dependent)

---

### 4. Ground Truth Labeling

Each generated scenario includes:

```json
{
  "violation_type": "misinformation",
  "severity": "high",
  "expected_action": "remove"
}
```

This ensures:

* fully deterministic grading
* no ambiguity in evaluation

---

### 5. Reproducibility

* random seeds used for generation
* fixed datasets per task level
* identical inputs produce identical outputs

---

## 🔁 RL Framing

This environment models moderation as a **sequential decision-making problem**:

* actions influence future state
* rewards accumulate over steps
* agents must learn optimal action sequences

---

## 📦 OpenEnv Compliance

The environment implements:

* `reset()` → returns initial observation
* `step(action)` → returns (observation, reward, done, info)
* `state()` → returns current state

Additionally:

* typed models for Observation, Action, Reward
* `openenv.yaml` for metadata
* reproducible baseline inference

---

## 🧠 One-Line Summary

> A deterministic, multi-step content moderation environment where agents learn to enforce platform policies under ambiguity, context, and real-world constraints.

---
