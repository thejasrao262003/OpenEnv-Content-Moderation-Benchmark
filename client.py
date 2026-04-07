"""
ModerationEnv — OpenEnv-compatible client for the Content Moderation environment.

Connects via WebSocket (persistent session) to the moderation server, following
the same pattern as TextArenaEnv / EchoEnv in the OpenEnv framework.

Usage (async):
    async with ModerationEnv(base_url="http://localhost:7860") as env:
        result = await env.reset(task_id="easy_harassment", seed=42)
        while not result.done:
            action = agent.select_action(result.observation)
            result = await env.step(action)

Usage (sync):
    with ModerationEnv(base_url="http://localhost:7860").sync() as env:
        result = env.reset(task_id="easy_harassment", seed=42)
        result = env.step(ModerationAction(action_type="fetch_user_history"))
"""
from __future__ import annotations

from typing import Any

from pydantic import ConfigDict, Field
from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import Action, Observation, State


# ---------------------------------------------------------------------------
# Action
# ---------------------------------------------------------------------------

class ModerationAction(Action):
    """
    An action the moderation agent can take.

    Investigation actions (reveal information progressively):
        fetch_user_history      — reveals the author's post history
        fetch_thread_context    — reveals replies and thread context
        check_policy_clause     — reveals the relevant policy clause

    Classification action (required before terminal action):
        mark_violation_type     — classifies the violation type
                                  parameters: {"violation_type": "harassment"|"misinformation"|"restricted"|"safe"}

    Terminal actions (end the episode):
        allow      — approve the post (no violation)
        flag       — flag for human review
        remove     — remove the post immediately
        escalate   — escalate to senior reviewer
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    action_type: str = Field(
        ...,
        description=(
            "One of: fetch_user_history, fetch_thread_context, check_policy_clause, "
            "mark_violation_type, allow, flag, remove, escalate"
        ),
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Action-specific parameters (e.g. violation_type for mark_violation_type)",
    )


# ---------------------------------------------------------------------------
# Observation
# ---------------------------------------------------------------------------

class ModerationObservation(Observation):
    """
    Observation returned by the content moderation environment.

    Core fields are always present. Progressive fields are revealed only after
    the corresponding investigation action is taken.
    """

    model_config = ConfigDict(
        extra="ignore",  # gracefully ignore any extra server fields
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    # Core fields (always present)
    post_id: str = Field(default="", description="Unique ID of the post being reviewed")
    content: str = Field(default="", description="Text content of the post")
    user_id: str = Field(default="", description="ID of the post author")
    reports: int = Field(default=0, description="Number of user reports")
    engagement: dict[str, int] = Field(
        default_factory=dict,
        description="Engagement metrics: likes, shares, comments",
    )
    geo: str = Field(default="US", description="Geographic region (US, EU, IN, UK)")
    step: int = Field(default=0, description="Current step number")
    max_steps: int = Field(default=10, description="Maximum steps allowed in this episode")

    # Progressive fields (None until revealed by investigation actions)
    user_history: list[str] | None = Field(
        default=None, description="Author's recent posts (revealed by fetch_user_history)"
    )
    thread_context: list[str] | None = Field(
        default=None, description="Thread replies/context (revealed by fetch_thread_context)"
    )
    policy_clause: str | None = Field(
        default=None, description="Relevant policy clause (revealed by check_policy_clause)"
    )
    violation_type: str | None = Field(
        default=None, description="Classified violation type (set by mark_violation_type)"
    )


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class ModerationEnv(EnvClient[ModerationAction, ModerationObservation, State]):
    """
    OpenEnv client for the Content Moderation environment.

    Maintains a persistent WebSocket connection to the server, enabling
    efficient multi-step episodes. Compatible with TRL's rollout_func pattern.

    Example (async):
        async with ModerationEnv(base_url="http://localhost:7860") as env:
            result = await env.reset(task_id="easy_harassment", seed=42)
            result = await env.step(ModerationAction(action_type="fetch_user_history"))
            result = await env.step(ModerationAction(
                action_type="mark_violation_type",
                parameters={"violation_type": "harassment"},
            ))
            result = await env.step(ModerationAction(action_type="remove"))
            print(result.reward)   # final step reward
            print(result.done)     # True

    Example (sync, e.g. for quick testing):
        with ModerationEnv(base_url="http://localhost:7860").sync() as env:
            result = env.reset(task_id="easy_harassment", seed=42)
            obs = result.observation
            print(obs.content)     # post content
            print(obs.reports)     # report count
    """

    def _step_payload(self, action: ModerationAction) -> dict[str, Any]:
        """Serialize ModerationAction to the dict the WS server expects in step.data."""
        return {
            "action_type": action.action_type,
            "parameters": action.parameters,
        }

    def _parse_result(self, payload: dict[str, Any]) -> StepResult[ModerationObservation]:
        """Parse a WS observation response into a typed StepResult."""
        # Merge reward from the outer payload into the observation data
        obs_data = {**payload.get("observation", {}), "reward": payload.get("reward")}
        return StepResult(
            observation=ModerationObservation(**obs_data),
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: dict[str, Any]) -> State:
        """Parse a WS state response into a State object."""
        return State(
            episode_id=payload.get("post_id"),
            step_count=payload.get("step", 0),
        )
