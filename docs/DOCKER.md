# 📄 DOCKER.md — Containerization & Docker Setup

---

## 🧠 Overview

This document defines how to containerize the moderation environment using Docker.

The container:

* runs the FastAPI server
* exposes required endpoints
* ensures reproducibility
* is compatible with Hugging Face Spaces

---

## 🐳 Dockerfile

---

## 📄 `Dockerfile`

```dockerfile
# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📦 requirements.txt

```txt
fastapi
uvicorn
pydantic
python-dotenv
openai
```

---

## 🐳 Build Instructions

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

### Test

```bash
curl http://localhost:8000/reset
```

---

## ⚙️ Environment Variables

(Optional but recommended)

---

### `.env`

```env
OPENAI_API_KEY=your_api_key_here
```

---

### Docker Support

```dockerfile
ENV OPENAI_API_KEY=${OPENAI_API_KEY}
```

Run with:

```bash
docker run -p 8000:8000 --env-file .env moderation-env
```

---

## ☁️ Hugging Face Spaces Notes

---

### Requirements

* Use Docker SDK
* Ensure port = `8000`
* App starts automatically

---

### Important

* No GPU required
* Keep image lightweight
* Avoid long startup time

---

## 🧪 Debugging Tips

---

### Container Logs

```bash
docker logs <container_id>
```

---

### Interactive Shell

```bash
docker exec -it <container_id> /bin/bash
```

---

### Rebuild Clean

```bash
docker build --no-cache -t moderation-env .
```

---

## ⚠️ Common Issues

---

### ❌ Module not found

* ensure correct folder structure
* check `COPY . .`

---

### ❌ Port not exposed

* confirm `EXPOSE 8000`
* uvicorn running on correct port

---

### ❌ Slow build

* remove unnecessary dependencies
* use slim base image

---

### ❌ HF Space fails to start

* check logs
* ensure app starts without manual input

---

## 🚀 Optimization (Optional)

---

### Reduce Image Size

* remove `build-essential` if not needed
* use `--no-cache-dir` in pip install

---

### Faster Startup

* avoid heavy initialization in app startup
* pre-load minimal resources

---

## 🧠 Deployment Flow Recap

```text
Code → Dockerfile → Build → Run → Test → Deploy (HF Spaces)
```

---

## 🧠 One-Line Summary

> A lightweight Docker setup that packages the FastAPI-based moderation environment into a reproducible, deployment-ready container.

---
