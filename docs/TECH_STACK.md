# 📄 TECH_STACK.md — Technology Choices & Justification

---

## 🧠 Overview

This document defines the **technology stack** used to build the AI Community Moderation Environment.

The stack is chosen to:

* ensure **OpenEnv compliance**
* enable **fast development**
* support **deterministic execution**
* allow seamless **Docker + Hugging Face deployment**

---

## 🧱 Core Language

### 🐍 Python 3.10+

**Why:**

* native ecosystem for OpenEnv
* strong support for RL + APIs
* rapid prototyping and debugging

---

## 🌐 Backend Framework

### ⚡ FastAPI

**Why:**

* lightweight and high-performance
* built-in request validation (via Pydantic)
* async support
* ideal for exposing `/reset`, `/step`, `/grader`, etc.
* easily deployable on Hugging Face Spaces

---

## 🧾 Data Validation & Models

### 📦 Pydantic

**Why:**

* strict typing for OpenEnv compliance
* automatic validation of API inputs/outputs
* seamless integration with FastAPI
* ensures deterministic schema handling

---

## 🧠 Environment Logic

### 🧩 Custom Python Modules

* `env/` → environment core
* `policy_engine.py` → rule evaluation
* `reward_engine.py` → step rewards
* `data_generator.py` → synthetic data

**Why:**

* full control over logic
* deterministic execution
* no external dependencies

---

## 🤖 Baseline Agent

### 🪶 Rule-based Agent (`baseline/agent.py`)

Heuristic agent using keyword matching — no LLM, fully reproducible.

---

## 🧠 LLM Agent — 🔹 Added

### Gemini 2.5 Flash via `google-genai` SDK

**Why:**

* state-of-the-art reasoning on structured tasks
* multi-turn chat with system prompt support
* deterministic temperature=0.0 setting minimises variance
* `google-genai` SDK is the latest official Google AI Python SDK

**Key files:**

```
agent/gemini_agent.py   — GeminiAgent class, multi-turn loop
agent/prompts.py        — system prompt + per-turn prompt builder
```

**SDK:**

```python
from google import genai
client = genai.Client(api_key=GOOGLE_API_KEY)
chat = client.chats.create(model="gemini-2.5-flash", config=...)
response = chat.send_message(turn_prompt)
```

**Design constraint:** LLM is ONLY the decision layer. Policy, reward, and grading remain deterministic in `env/`.

---

## 📦 API Communication

### JSON over HTTP

**Why:**

* simple and standard
* compatible with OpenEnv expectations
* easy debugging and logging

---

## 🐳 Containerization

### 🐳 Docker

**Why:**

* mandatory for evaluation pipeline
* ensures consistent runtime environment
* required for Hugging Face Spaces deployment

---

## ☁️ Deployment Platform

### 🤗 Hugging Face Spaces (Docker-based)

**Why:**

* required by competition
* easy container deployment
* public endpoint for validation
* integrates well with OpenEnv ecosystem

---

## 🧪 Testing & Validation

### ✅ Pytest (optional but recommended)

**Why:**

* quick validation of:

  * policy engine
  * reward logic
  * graders

---

### 🔍 OpenEnv Validator

**Why:**

* ensures compliance with:

  * API schema
  * openenv.yaml
  * required endpoints

---

## 📊 Logging (Optional)

### Python Logging

**Why:**

* debug environment flow
* trace agent decisions
* inspect reward calculations

---

## 📦 Dependency Summary

```txt
fastapi
uvicorn[standard]
pydantic>=2.6
google-genai>=1.0
openai          # optional / legacy
pytest
httpx           # TestClient
```

---

## ⚙️ Runtime Setup

| Component  | Tool      |
| ---------- | --------- |
| API Server | Uvicorn   |
| Backend    | FastAPI   |
| Models     | Pydantic  |
| Container  | Docker    |
| Deployment | HF Spaces |

---

## 🧠 Design Principles

### 1. Minimalism

Only essential tools used

---

### 2. Determinism

No external APIs for core logic

---

### 3. Reproducibility

Same input → same output

---

### 4. Fast Iteration

Simple stack = quick debugging

---

## ⚠️ What We Avoid (Important)

* ❌ heavy ML frameworks (TensorFlow, PyTorch)
* ❌ databases (not needed for MVP)
* ❌ microservices complexity
* ❌ external APIs for environment logic

---

## 🧠 One-Line Summary

> A lightweight Python-based stack using FastAPI and Pydantic to build a deterministic, OpenEnv-compliant environment with Docker-based deployment.

---
