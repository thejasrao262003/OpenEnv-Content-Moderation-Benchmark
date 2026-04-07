# 📄 REWARD.md — Step-wise Reward Design

---

## 🧠 Overview

This document defines the **reward function** used during agent interaction with the environment.

Unlike the final grader (which evaluates overall performance), this reward system provides **dense, step-by-step feedback** to guide learning.

The reward function is:

* **deterministic**
* aligned with `POLICY.md`
* consistent with `GRADERS.md`
* designed to encourage **correct reasoning paths**, not just final answers

---

## 🎯 Reward Objectives

The reward system encourages:

1. Correct investigation behavior
2. Accurate violation classification
3. Optimal final decision
4. Efficient action sequences
5. Avoidance of risky moderation errors

---

## 🔁 Reward Structure

Rewards are assigned at each step:

```text id="i5zy6z"
step(action) → reward → next_state
```

---

## 🧩 Reward Components

---

### 1. 🔍 Investigation Rewards

Encourage proper use of investigation steps.

| Action                    | Condition         | Reward |
| ------------------------- | ----------------- | ------ |
| fetch_user_history        | required & useful | +0.2   |
| fetch_thread_context      | required          | +0.2   |
| check_policy_clause       | relevant          | +0.2   |
| unnecessary investigation | not needed        | -0.1   |

---

### 2. 🧠 Classification Rewards

| Action                   | Condition            | Reward |
| ------------------------ | -------------------- | ------ |
| correct violation type   | matches ground truth | +0.5   |
| incorrect classification | mismatch             | -0.3   |

---

### 3. 🎯 Final Decision Rewards

| Action                 | Condition               | Reward |
| ---------------------- | ----------------------- | ------ |
| correct final action   | exact match             | +1.0   |
| acceptable alternative | e.g. escalate           | +0.5   |
| false positive         | safe content removed    | -0.5   |
| false negative         | harmful content allowed | -2.0   |

---

### 4. ⚖️ Escalation Rewards

| Action                 | Condition         | Reward |
| ---------------------- | ----------------- | ------ |
| correct escalation     | ambiguity present | +0.5   |
| unnecessary escalation | clear case        | -0.2   |

---

### 5. ⚡ Efficiency Penalty

Encourages minimal steps.

```python id="flb5ax"
step_penalty = -0.05 per extra step beyond optimal
```

---

### 6. 🚫 Invalid Actions

```python id="0rygw8"
if action is invalid:
    reward = -0.2
```

---

## 🧮 Reward Aggregation

Total episode reward is:

```python id="0bm36z"
total_reward = sum(step_rewards)
```

Optionally normalized:

```python id="xbfh61"
normalized_reward = total_reward / max_possible_reward
```

---

## 🎯 Task-Specific Adjustments

---

### 🟢 Easy Task

* minimal investigation required
* higher reward for correct action

```python id="02ybzq"
action_reward_weight = 1.2
investigation_penalty_weight = 1.0
```

---

### 🟡 Medium Task

* balanced reward distribution

```python id="0i14xh"
investigation_weight = 1.0
classification_weight = 1.0
```

---

### 🔴 Hard Task

* investigation and context critical
* higher penalty for mistakes

```python id="9r4g65"
false_negative_penalty = -2.5
investigation_reward_weight = 1.2
```

---

## 🔁 Reward vs Grader Alignment

| Component      | Reward | Grader |
| -------------- | ------ | ------ |
| final action   | ✅      | ✅      |
| classification | ✅      | ✅      |
| investigation  | ✅      | ✅      |
| efficiency     | ✅      | ✅      |

👉 Reward guides learning
👉 Grader evaluates outcome

---

## ⚠️ Important Design Constraints

* rewards must be **deterministic**
* no randomness in scoring
* no hidden signals
* all rewards derivable from:

  * policy
  * ground truth
  * action sequence

---

## 🧠 RL Interpretation

This reward function enables:

* **credit assignment** across steps
* learning optimal action sequences
* balancing trade-offs (precision vs recall)
* adapting strategy based on context

---

## 🧠 One-Line Summary

> A dense, deterministic reward system that guides agents toward correct, efficient, and policy-compliant moderation decisions.

---
