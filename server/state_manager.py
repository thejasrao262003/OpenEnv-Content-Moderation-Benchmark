"""
StateManager — owns the lifecycle of a single episode.

Single-threaded MVP: one active episode at a time.  A new /reset always
overwrites the previous episode state.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from models import (
    Action,
    ActionType,
    GroundTruth,
    Observation,
    StepResult,
    TaskConfig,
    TERMINAL_ACTIONS,
    TrajectoryStep,
)
from .data_generator import DataGenerator
from .reward_engine import RewardEngine


@dataclass
class EpisodeState:
    task_config: TaskConfig
    observation: Observation
    ground_truth: GroundTruth
    # Private context stores — revealed progressively
    _user_history: list[str]
    _thread_context: list[str]
    _policy_clause: str
    trajectory: list[TrajectoryStep] = field(default_factory=list)
    # Track which investigation actions have been taken (for duplicate detection)
    investigation_log: list[ActionType] = field(default_factory=list)
    # Whether classification was attempted
    classified: bool = False
    final_action: ActionType | None = None


class StateManager:
    """Manages the current episode state."""

    def __init__(self) -> None:
        self._state: EpisodeState | None = None
        self._generator = DataGenerator()
        self._reward_engine = RewardEngine()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self, task_config: TaskConfig) -> Observation:
        obs, gt, hidden = self._generator.generate(task_config)
        self._state = EpisodeState(
            task_config=task_config,
            observation=obs,
            ground_truth=gt,
            _user_history=hidden["user_history"],
            _thread_context=hidden["thread_context"],
            _policy_clause=hidden["policy_clause"],
        )
        return obs

    def step(self, action: Action) -> StepResult:
        state = self._require_state()

        if state.observation.done:
            raise ValueError("Episode is already finished. Call /reset to start a new episode.")

        # Snapshot investigation log BEFORE applying action (duplicate check needs prior state)
        prior_investigation_log = list(state.investigation_log)

        # Execute the action — mutate observation in place
        self._apply_action(action, state)

        # Compute reward (pass the pre-action investigation log so duplicate detection is correct)
        reward, reason = self._reward_engine.compute(
            action=action,
            step=state.observation.step,
            steps_taken=prior_investigation_log,
            ground_truth=state.ground_truth,
            difficulty=state.task_config.difficulty,
        )

        # Advance step counter AFTER reward (so min_steps calc uses current step)
        state.observation.step += 1

        # Check terminal condition
        done = self._is_terminal(action, state)
        state.observation.done = done
        if action.action_type in TERMINAL_ACTIONS:
            state.final_action = action.action_type

        # Record trajectory
        state.trajectory.append(
            TrajectoryStep(
                step=state.observation.step,
                action=action,
                reward=reward,
                reward_reason=reason,
            )
        )

        return StepResult(
            observation=state.observation.model_copy(),
            reward=reward,
            reward_reason=reason,
            done=done,
            info={
                "ground_truth": state.ground_truth.model_dump(),
                "step": state.observation.step,
            },
        )

    def get_state(self) -> Observation:
        return self._require_state().observation

    def get_episode_state(self) -> EpisodeState:
        return self._require_state()

    def has_active_episode(self) -> bool:
        return self._state is not None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_state(self) -> EpisodeState:
        if self._state is None:
            raise ValueError("No active episode. Call /reset first.")
        return self._state

    def _apply_action(self, action: Action, state: EpisodeState) -> None:
        at = action.action_type
        obs = state.observation

        if at == ActionType.fetch_user_history:
            obs.user_history = state._user_history
            state.investigation_log.append(at)

        elif at == ActionType.fetch_thread_context:
            obs.thread_context = state._thread_context
            state.investigation_log.append(at)

        elif at == ActionType.check_policy_clause:
            obs.policy_clause = state._policy_clause
            state.investigation_log.append(at)

        elif at == ActionType.mark_violation_type:
            vt_value = action.parameters.get("violation_type")
            if vt_value:
                try:
                    from models import ViolationType
                    obs.violation_type = ViolationType(vt_value)
                except ValueError:
                    pass  # invalid value — reward engine will penalise
            state.classified = True

        # Terminal actions (allow/flag/remove/escalate) don't mutate observation fields

    def _is_terminal(self, action: Action, state: EpisodeState) -> bool:
        if action.action_type in TERMINAL_ACTIONS:
            return True
        # step has already been incremented before this call
        if state.observation.step >= state.task_config.max_steps:
            return True
        return False
