# 📄 API_CONTRACT.md — API Specification & Schemas

---

## 🧠 Overview

This document defines the **API contract** for the moderation environment.

All endpoints:

* follow REST principles
* return JSON responses
* are deterministic and reproducible
* align with OpenEnv requirements

---

## 🌐 Base URL

```text
http://localhost:8000
```

(Will be deployed on Hugging Face Spaces)

---

## 📌 Endpoints Summary

| Endpoint      | Method | Description                            |
| ------------- | ------ | -------------------------------------- |
| `/reset`      | POST   | Initialize a new episode               |
| `/step`       | POST   | Apply an action                        |
| `/state`      | GET    | Get current state                      |
| `/tasks`      | GET    | List available tasks                   |
| `/grader`     | GET    | Get score for current episode          |
| `/baseline`   | GET    | Run rule-based baseline agent          |
| `/agent/run`  | POST   | Run Gemini 2.5 Flash agent 🔹 Added   |
| `/health`     | GET    | Liveness check                         |

---

# 🚀 1. `/reset`

### Description

Initializes a new episode.

---

### Request

```json
{
  "task": "easy | medium | hard",
  "seed": 42
}
```

---

### Response

```json
{
  "state": {
    "post_content": "...",
    "user_history": [...],
    "reports": ...,
    "engagement": "...",
    "geo": "...",
    "available_context": []
  },
  "available_actions": [
    "fetch_user_history",
    "fetch_thread_context",
    "check_policy_clause",
    "mark_violation_type",
    "allow",
    "flag",
    "remove",
    "escalate"
  ],
  "done": false
}
```

---

# 🔄 2. `/step`

### Description

Executes one action in the environment.

---

### Request

```json
{
  "action": "fetch_user_history",
  "parameters": {
    "violation_type": "misinformation"
  }
}
```

---

### Response

```json
{
  "state": {
    "post_content": "...",
    "user_history": [...],
    "reports": ...,
    "engagement": "...",
    "geo": "...",
    "thread_context": [...],
    "policy_context": "...",
    "predicted_violation": "..."
  },
  "reward": 0.2,
  "done": false,
  "info": {
    "step": 2,
    "message": "User history fetched"
  }
}
```

---

# 📊 3. `/state`

### Description

Returns current environment state without taking action.

---

### Request

```json
{}
```

---

### Response

```json
{
  "state": {...},
  "step_count": 3,
  "done": false
}
```

---

# 📋 4. `/tasks`

### Description

Returns available tasks and action schema.

---

### Response

```json
{
  "tasks": [
    {
      "name": "easy",
      "description": "Clear violations"
    },
    {
      "name": "medium",
      "description": "Ambiguous moderation"
    },
    {
      "name": "hard",
      "description": "Contextual + geo-aware"
    }
  ],
  "action_schema": {
    "action": "string",
    "parameters": "object (optional)"
  }
}
```

---

# 🧪 5. `/grader`

### Description

Returns score for completed episode.

---

### Response

```json
{
  "score": 0.82,
  "breakdown": {
    "final_action": 1.0,
    "violation": 1.0,
    "investigation": 0.66,
    "efficiency": 0.8
  },
  "steps_taken": 4,
  "max_steps": 7
}
```

---

# 🤖 6. `/baseline`

### Description

Runs the rule-based baseline agent on a task and returns the graded result.

### Query Parameters

| Param     | Type   | Default             | Description     |
| --------- | ------ | ------------------- | --------------- |
| `task_id` | string | `easy_harassment`   | Task to run     |
| `seed`    | int    | task default        | Optional seed   |

### Response

```json
{
  "task_id": "easy_harassment",
  "seed": 42,
  "score": {
    "final_action_score": 1.0,
    "classification_score": 1.0,
    "investigation_score": 1.0,
    "efficiency_score": 0.5,
    "total": 0.875,
    "breakdown": {}
  },
  "trajectory": [...]
}
```

---

# 🧠 7. `/agent/run` — 🔹 Added

### Description

Runs the **Gemini 2.5 Flash LLM agent** on a full episode.
Requires `GOOGLE_API_KEY` or `GEMINI_API_KEY` in the server environment.

### Method: `POST`

### Request Body

```json
{
  "task_id": "hard_misinformation",
  "seed": 777
}
```

### Response

```json
{
  "task_id": "hard_misinformation",
  "seed": 777,
  "score": {
    "final_action_score": 1.0,
    "classification_score": 1.0,
    "investigation_score": 1.0,
    "efficiency_score": 0.43,
    "total": 0.88,
    "breakdown": {...}
  },
  "trajectory": [
    { "step": 1, "action": {"action_type": "fetch_user_history", "parameters": {}}, "reward": 0.2, "reward_reason": "..." },
    ...
  ]
}
```

### Error: Missing API Key

```json
{ "detail": "GOOGLE_API_KEY or GEMINI_API_KEY environment variable is required..." }
```
HTTP 500

---

# 🧾 Action Definitions

---

## 🔍 Investigation Actions

| Action               | Parameters  | Description                   |
| -------------------- | ----------- | ----------------------------- |
| fetch_user_history   | none        | Retrieve user past activity   |
| fetch_thread_context | none        | Retrieve conversation context |
| check_policy_clause  | {clause_id} | Retrieve policy info          |

---

## 🧠 Classification Actions

| Action              | Parameters | Description                |
| ------------------- | ---------- | -------------------------- |
| mark_violation_type | {type}     | Predict violation category |

---

## 🎯 Decision Actions

| Action   | Parameters | Description          |
| -------- | ---------- | -------------------- |
| allow    | none       | Approve content      |
| flag     | none       | Mark for review      |
| remove   | none       | Remove content       |
| escalate | none       | Send to human review |

---

# ⚠️ Error Handling

---

## Invalid Action

```json
{
  "error": "Invalid action",
  "reward": -0.2
}
```

---

## Episode Already Complete

```json
{
  "error": "Episode finished",
  "done": true
}
```

---

## Missing Parameters

```json
{
  "error": "Missing required parameter: violation_type"
}
```

---

# 🔁 State Schema

```json
{
  "post_content": "string",
  "user_history": "array",
  "reports": "integer",
  "engagement": "low | medium | high",
  "geo": "string",
  "thread_context": "array",
  "policy_context": "string",
  "predicted_violation": "string",
  "final_action": "string"
}
```

---

# 🧠 Design Principles

* consistent request/response format
* explicit state representation
* deterministic outputs
* minimal ambiguity

---

## 🧠 One-Line Summary

> A clean, deterministic API contract enabling structured interaction between agent and moderation environment.

---
