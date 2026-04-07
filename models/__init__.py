from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ViolationType(str, Enum):
    harassment = "harassment"
    misinformation = "misinformation"
    restricted = "restricted"
    safe = "safe"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


SEVERITY_ORDER = {Severity.low: 0, Severity.medium: 1, Severity.high: 2, Severity.critical: 3}


class ActionType(str, Enum):
    # Investigation actions
    fetch_user_history = "fetch_user_history"
    fetch_thread_context = "fetch_thread_context"
    check_policy_clause = "check_policy_clause"
    # Classification action
    mark_violation_type = "mark_violation_type"
    # Terminal actions
    allow = "allow"
    flag = "flag"
    remove = "remove"
    escalate = "escalate"


INVESTIGATION_ACTIONS = {
    ActionType.fetch_user_history,
    ActionType.fetch_thread_context,
    ActionType.check_policy_clause,
}

TERMINAL_ACTIONS = {
    ActionType.allow,
    ActionType.flag,
    ActionType.remove,
    ActionType.escalate,
}


class Observation(BaseModel):
    post_id: str
    content: str
    user_id: str
    reports: int
    engagement: dict[str, int]          # likes, shares, comments
    geo: Literal["US", "EU", "IN", "UK"]
    step: int
    max_steps: int
    done: bool
    # Progressively revealed fields
    user_history: list[str] | None = None
    thread_context: list[str] | None = None
    policy_clause: str | None = None
    violation_type: ViolationType | None = None


class Action(BaseModel):
    action_type: ActionType
    parameters: dict[str, Any] = Field(default_factory=dict)


class StepResult(BaseModel):
    observation: Observation
    reward: float
    reward_reason: str
    done: bool
    info: dict[str, Any] = Field(default_factory=dict)


class GroundTruth(BaseModel):
    violation_type: ViolationType
    base_severity: Severity
    final_severity: Severity
    expected_action: ActionType
    # Per-template optimal investigation path (used by grader)
    required_investigation: list[str] = Field(default_factory=list)
    min_steps: int = 1


class TaskConfig(BaseModel):
    task_id: str
    difficulty: Literal["easy", "medium", "hard"]
    description: str
    max_steps: int
    seed: int


class TrajectoryStep(BaseModel):
    step: int
    action: Action
    reward: float
    reward_reason: str


class EpisodeScore(BaseModel):
    final_action_score: float
    classification_score: float
    investigation_score: float
    efficiency_score: float
    total: float
    breakdown: dict[str, Any] = Field(default_factory=dict)


class ResetRequest(BaseModel):
    # task_id defaults to easy_harassment so POST /reset {} returns 200 (validator liveness check)
    task_id: str = "easy_harassment"
    seed: int | None = None


class BaselineResult(BaseModel):
    task_id: str
    seed: int
    score: EpisodeScore
    trajectory: list[TrajectoryStep]