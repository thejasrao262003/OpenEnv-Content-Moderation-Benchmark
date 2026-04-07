# 📄 DEPLOYMENT.md — Deployment Strategy & Setup

---

## 🧠 Overview

This document defines how the moderation environment is:

* built
* containerized
* deployed
* validated

The system is deployed as a **Docker-based Hugging Face Space** and must:

* expose all required endpoints
* respond to `/reset` successfully
* run baseline and graders without errors

---

## 🎯 Deployment Requirements

As per competition:

* Docker build must succeed
* API must respond with HTTP 200
* OpenEnv spec must be valid
* `/baseline` must run successfully
* all endpoints must be reachable

---

## 🐳 1. Local Development Setup

---

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 2: Run FastAPI Server

```bash
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

---

### Step 3: Test Endpoints

```bash
curl -X POST http://localhost:8000/reset
curl -X POST http://localhost:8000/step
curl http://localhost:8000/state
curl http://localhost:8000/grader
```

---

## 🐳 2. Docker Build

---

### Build Image

```bash
docker build -t moderation-env .
```

---

### Run Container

```bash
docker run -p 8000:8000 moderation-env
```

---

### Verify

```bash
curl http://localhost:8000/reset
```

Expected:

* HTTP 200 response
* valid JSON output

---

## ☁️ 3. Hugging Face Spaces Deployment

---

### Step 1: Create Space

* Platform: Hugging Face Spaces
* SDK: **Docker**
* Visibility: Public

---

### Step 2: Upload Files

Include:

* `Dockerfile`
* `requirements.txt`
* `api/`
* `env/`
* `graders/`
* `baseline/`
* `openenv.yaml`

---

### Step 3: Configure Space

* No GPU required
* CPU environment sufficient
* Add environment variables if needed

---

### Step 4: Deploy

* Push code to Space repo
* Docker build will auto-trigger

---

### Step 5: Validate Deployment

Test:

```bash
POST https://<space-url>/reset
```

Must:

* return valid response
* not crash

---

## 🔍 4. OpenEnv Validation

---

### Run Validator (locally or CI)

Ensure:

* `openenv.yaml` is valid
* endpoints conform to spec
* observation/action models match

---

### Key Checks

* `/reset` returns valid observation
* `/step` returns reward + done
* `/state` returns current state
* `/grader` returns score

---

## 🤖 5. Baseline Validation

---

### Run Baseline

```bash
curl http://localhost:8000/baseline
```

---

### Expected Output

```json
{
  "easy_score": ...,
  "medium_score": ...,
  "hard_score": ...,
  "overall_score": ...
}
```

---

## 📊 6. Health Check

Optional endpoint:

```bash
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

---

## ⚠️ Common Failure Points (Avoid These)

---

### ❌ Docker build fails

* missing dependencies
* incorrect paths

---

### ❌ API crashes on `/reset`

* invalid state initialization
* missing fields

---

### ❌ Non-deterministic outputs

* random without seed
* inconsistent generation

---

### ❌ Baseline fails

* missing OpenAI key handling
* incorrect loop logic

---

### ❌ Timeout errors

* long processing inside `/step`

---

## 🧠 Deployment Checklist

Before submission:

* [ ] Docker builds successfully
* [ ] Container runs locally
* [ ] `/reset` returns 200
* [ ] `/step` works correctly
* [ ] `/grader` returns score
* [ ] `/baseline` executes fully
* [ ] Hugging Face Space is live
* [ ] OpenEnv validation passes

---

## 🚀 Recommended Workflow

```text
1. Build locally
2. Test endpoints
3. Dockerize
4. Test container
5. Deploy to HF
6. Validate endpoints
7. Run baseline
```

---

## 🧠 Design Principles

* simplicity over complexity
* deterministic behavior
* fast response time
* reproducible builds

---

## 🧠 One-Line Summary

> A Docker-based deployment pipeline ensuring the environment runs reliably, validates against OpenEnv, and is accessible via Hugging Face Spaces.

---
