"""
Post-episode grader.

Computes a final [0, 1] score from four weighted components:
  - Final action score  50%
  - Classification      20%
  - Investigation       15%
  - Efficiency          15%
"""
from __future__ import annotations

from models import (
    ActionType,
    EpisodeScore,
    INVESTIGATION_ACTIONS,
    SEVERITY_ORDER,
    Severity,
    ViolationType,
)
from .state_manager import EpisodeState

# Fallback required investigation per difficulty (used only if ground_truth has none)
_REQUIRED_INVESTIGATION_FALLBACK: dict[str, set[ActionType]] = {
    "easy": {ActionType.fetch_user_history},
    "medium": {ActionType.fetch_user_history, ActionType.check_policy_clause},
    "hard": {
        ActionType.fetch_user_history,
        ActionType.fetch_thread_context,
        ActionType.check_policy_clause,
    },
}

_MIN_STEPS_FALLBACK: dict[str, int] = {"easy": 2, "medium": 3, "hard": 4}


class Grader:
    """Score a completed episode."""

    def score(self, state: EpisodeState) -> EpisodeScore:
        diff = state.task_config.difficulty
        gt = state.ground_truth
        final_action = state.final_action
        actual_steps = state.observation.step

        fa_raw = self._final_action_score(final_action, gt)
        cls_raw = self._classification_score(state)
        inv_raw = self._investigation_score(state, diff, gt)
        eff_raw = self._efficiency_score(actual_steps, diff, gt)

        # Weighted sum
        fa = fa_raw * 0.50
        cls = cls_raw * 0.20
        inv = inv_raw * 0.15
        eff = eff_raw * 0.15

        # Critical false-negative penalty (agent let through a must-remove post)
        penalty = 0.0
        if (
            final_action in (ActionType.allow, ActionType.flag)
            and gt.expected_action == ActionType.remove
            and gt.violation_type in (ViolationType.harassment, ViolationType.misinformation)
            and SEVERITY_ORDER[gt.final_severity] >= SEVERITY_ORDER[Severity.high]
        ):
            penalty = 0.5

        total = max(0.0, min(1.0, fa + cls + inv + eff - penalty))

        return EpisodeScore(
            final_action_score=round(fa_raw, 4),
            classification_score=round(cls_raw, 4),
            investigation_score=round(inv_raw, 4),
            efficiency_score=round(eff_raw, 4),
            total=round(total, 4),
            breakdown={
                "final_action_weighted": round(fa, 4),
                "classification_weighted": round(cls, 4),
                "investigation_weighted": round(inv, 4),
                "efficiency_weighted": round(eff, 4),
                "false_negative_penalty": round(penalty, 4),
                "agent_action": final_action.value if final_action else None,
                "expected_action": gt.expected_action.value,
                "violation_type": gt.violation_type.value,
                "final_severity": gt.final_severity.value,
            },
        )

    # ------------------------------------------------------------------

    def _final_action_score(
        self, final_action: ActionType | None, gt: "GroundTruth"
    ) -> float:
        if final_action is None:
            return 0.0
        if final_action == gt.expected_action:
            return 1.0
        # Escalate is always a partial credit when unsure
        if final_action == ActionType.escalate:
            return 0.5
        return 0.0

    def _classification_score(self, state: EpisodeState) -> float:
        if not state.classified:
            return 0.0
        # Find last mark_violation_type action in trajectory
        for step in reversed(state.trajectory):
            if step.action.action_type == ActionType.mark_violation_type:
                claimed = step.action.parameters.get("violation_type")
                try:
                    if ViolationType(claimed) == state.ground_truth.violation_type:
                        return 1.0
                except (ValueError, TypeError):
                    pass
                return 0.0
        return 0.0

    def _investigation_score(self, state: EpisodeState, difficulty: str, gt) -> float:
        # Use per-template required_investigation if available, else fall back to difficulty defaults
        if gt.required_investigation:
            required = {ActionType(a) for a in gt.required_investigation}
        else:
            required = _REQUIRED_INVESTIGATION_FALLBACK.get(difficulty, set())
        if not required:
            return 1.0
        used = set(state.investigation_log)
        matched = required & used
        return len(matched) / len(required)

    def _efficiency_score(self, actual_steps: int, difficulty: str, gt) -> float:
        # Use per-template min_steps if set (>0), else fall back to difficulty defaults
        min_steps = gt.min_steps if gt.min_steps > 0 else _MIN_STEPS_FALLBACK.get(difficulty, 2)
        if actual_steps == 0:
            return 0.0
        return min(1.0, min_steps / actual_steps)
