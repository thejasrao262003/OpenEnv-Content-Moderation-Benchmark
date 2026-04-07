"""
Integration tests for the OpenENV moderation environment API.

Uses FastAPI's TestClient (httpx-backed) — no server needed.
"""
import sys
import os

# Ensure the project root is on the path so imports resolve correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health + meta
# ---------------------------------------------------------------------------

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_tasks_list():
    r = client.get("/tasks")
    assert r.status_code == 200
    tasks = r.json()
    assert "easy_harassment" in tasks
    assert "medium_ambiguous" in tasks
    assert "hard_misinformation" in tasks


# ---------------------------------------------------------------------------
# Error cases before reset
# ---------------------------------------------------------------------------

def test_step_without_reset():
    # Use a fresh app instance to guarantee no prior episode
    from api.app import _state_manager
    _state_manager._state = None

    r = client.post("/step", json={"action_type": "allow", "parameters": {}})
    assert r.status_code == 400


def test_state_without_reset():
    from api.app import _state_manager
    _state_manager._state = None

    r = client.get("/state")
    assert r.status_code == 400


def test_grader_without_reset():
    from api.app import _state_manager
    _state_manager._state = None

    r = client.get("/grader")
    assert r.status_code == 400


def test_reset_unknown_task():
    r = client.post("/reset", json={"task_id": "nonexistent_task"})
    assert r.status_code == 400


def test_invalid_action_type():
    client.post("/reset", json={"task_id": "easy_harassment", "seed": 42})
    r = client.post("/step", json={"action_type": "explode", "parameters": {}})
    assert r.status_code == 422  # Pydantic validation error


# ---------------------------------------------------------------------------
# Easy episode — happy path
# ---------------------------------------------------------------------------

def test_easy_full_episode():
    r = client.post("/reset", json={"task_id": "easy_harassment", "seed": 42})
    assert r.status_code == 200
    obs = r.json()
    assert obs["done"] is False
    assert obs["content"] != ""
    assert obs["user_history"] is None  # not yet revealed

    # Investigate
    r = client.post("/step", json={"action_type": "fetch_user_history", "parameters": {}})
    assert r.status_code == 200
    result = r.json()
    assert result["observation"]["user_history"] is not None
    assert result["reward"] > 0

    # Classify
    r = client.post("/step", json={
        "action_type": "mark_violation_type",
        "parameters": {"violation_type": "harassment"},
    })
    assert r.status_code == 200

    # Terminal action
    r = client.post("/step", json={"action_type": "remove", "parameters": {}})
    assert r.status_code == 200
    result = r.json()
    assert result["done"] is True

    # Grade
    r = client.get("/grader")
    assert r.status_code == 200
    score = r.json()
    assert 0.0 <= score["total"] <= 1.0
    assert score["final_action_score"] == 1.0  # remove is correct for easy harassment


# ---------------------------------------------------------------------------
# Medium episode — happy path
# ---------------------------------------------------------------------------

def test_medium_full_episode():
    r = client.post("/reset", json={"task_id": "medium_ambiguous", "seed": 100})
    assert r.status_code == 200

    # Investigate: user history + policy clause
    client.post("/step", json={"action_type": "fetch_user_history", "parameters": {}})
    client.post("/step", json={"action_type": "check_policy_clause", "parameters": {}})

    # Classify
    client.post("/step", json={
        "action_type": "mark_violation_type",
        "parameters": {"violation_type": "safe"},
    })

    # Terminal
    r = client.post("/step", json={"action_type": "allow", "parameters": {}})
    assert r.status_code == 200
    assert r.json()["done"] is True

    # Grade
    r = client.get("/grader")
    score = r.json()
    assert 0.0 <= score["total"] <= 1.0


# ---------------------------------------------------------------------------
# Hard episode — happy path
# ---------------------------------------------------------------------------

def test_hard_full_episode():
    r = client.post("/reset", json={"task_id": "hard_misinformation", "seed": 10})
    assert r.status_code == 200

    for action in [
        "fetch_user_history",
        "fetch_thread_context",
        "check_policy_clause",
    ]:
        r = client.post("/step", json={"action_type": action, "parameters": {}})
        assert r.status_code == 200

    client.post("/step", json={
        "action_type": "mark_violation_type",
        "parameters": {"violation_type": "misinformation"},
    })

    r = client.post("/step", json={"action_type": "remove", "parameters": {}})
    assert r.json()["done"] is True

    r = client.get("/grader")
    score = r.json()
    assert score["total"] > 0.5   # well-investigated + correct action should score high


# ---------------------------------------------------------------------------
# Episode termination guard
# ---------------------------------------------------------------------------

def test_action_after_episode_done():
    client.post("/reset", json={"task_id": "easy_harassment", "seed": 42})
    client.post("/step", json={"action_type": "remove", "parameters": {}})

    # Try another action after episode is done
    r = client.post("/step", json={"action_type": "allow", "parameters": {}})
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Grader before episode done
# ---------------------------------------------------------------------------

def test_grader_before_done():
    client.post("/reset", json={"task_id": "easy_harassment", "seed": 42})
    r = client.get("/grader")
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# /state reflects progressive reveal
# ---------------------------------------------------------------------------

def test_state_progressive_reveal():
    client.post("/reset", json={"task_id": "hard_misinformation", "seed": 777})

    r = client.get("/state")
    assert r.json()["user_history"] is None

    client.post("/step", json={"action_type": "fetch_user_history", "parameters": {}})

    r = client.get("/state")
    assert r.json()["user_history"] is not None
    assert r.json()["thread_context"] is None  # not yet revealed


# ---------------------------------------------------------------------------
# Baseline agent
# ---------------------------------------------------------------------------

def test_baseline_easy():
    r = client.get("/baseline", params={"task_id": "easy_harassment", "seed": 42})
    assert r.status_code == 200
    result = r.json()
    assert 0.0 <= result["score"]["total"] <= 1.0
    assert len(result["trajectory"]) > 0


def test_baseline_medium():
    r = client.get("/baseline", params={"task_id": "medium_ambiguous", "seed": 100})
    assert r.status_code == 200
    assert 0.0 <= r.json()["score"]["total"] <= 1.0


def test_baseline_hard():
    r = client.get("/baseline", params={"task_id": "hard_misinformation", "seed": 777})
    assert r.status_code == 200
    assert 0.0 <= r.json()["score"]["total"] <= 1.0


# ---------------------------------------------------------------------------
# Determinism — same seed → same result
# ---------------------------------------------------------------------------

def test_determinism():
    r1 = client.get("/baseline", params={"task_id": "easy_harassment", "seed": 42})
    r2 = client.get("/baseline", params={"task_id": "easy_harassment", "seed": 42})
    assert r1.json()["score"]["total"] == r2.json()["score"]["total"]
