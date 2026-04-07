"""
Dense, per-step reward engine.

Rewards are computed after every /step call.  Terminal actions produce
the largest signals (+1.0 correct, -2.0 false negative).  Investigation
actions give small positive rewards to encourage information gathering.
"""
from __future__ import annotations

from models import (
    Action,
    ActionType,
    GroundTruth,
    INVESTIGATION_ACTIONS,
    SEVERITY_ORDER,
    Severity,
    TERMINAL_ACTIONS,
    ViolationType,
)

# ---------------------------------------------------------------------------
# Reward constants
# ---------------------------------------------------------------------------

INVESTIGATION_REWARD = 0.2
CORRECT_CLASSIFICATION = 0.5
WRONG_CLASSIFICATION = -0.3
CORRECT_TERMINAL = 1.0
WRONG_TERMINAL = -0.5
FALSE_NEGATIVE_PENALTY = -2.0      # e.g. agent allows a critical harassment post
ESCALATE_AMBIGUOUS = 0.5
ESCALATE_UNNECESSARY = -0.2
EXTRA_STEP_PENALTY = -0.05

# Actions that should never be "allowed" when ground truth says remove/flag
_SEVERE_VIOLATIONS = {ViolationType.harassment, ViolationType.misinformation}


class RewardEngine:
    """Compute per-step reward given the current action and episode context."""

    def compute(
        self,
        action: Action,
        step: int,
        steps_taken: list[ActionType],
        ground_truth: GroundTruth,
        difficulty: str,
    ) -> tuple[float, str]:
        """
        Returns:
            reward  — float
            reason  — human-readable explanation
        """
        at = action.action_type

        if at in INVESTIGATION_ACTIONS:
            return self._investigation_reward(at, steps_taken)

        if at == ActionType.mark_violation_type:
            return self._classification_reward(action, ground_truth)

        if at in TERMINAL_ACTIONS:
            return self._terminal_reward(at, step, ground_truth, difficulty)

        return 0.0, "unknown action type"

    # ------------------------------------------------------------------

    def _investigation_reward(
        self, at: ActionType, steps_taken: list[ActionType]
    ) -> tuple[float, str]:
        if at in steps_taken:
            # Penalise redundant investigation
            return -0.1, f"duplicate investigation action: {at.value}"
        return INVESTIGATION_REWARD, f"investigation step: {at.value} (+{INVESTIGATION_REWARD})"

    def _classification_reward(
        self, action: Action, ground_truth: GroundTruth
    ) -> tuple[float, str]:
        claimed = action.parameters.get("violation_type")
        if claimed is None:
            return WRONG_CLASSIFICATION, "mark_violation_type missing 'violation_type' parameter"

        try:
            claimed_vt = ViolationType(claimed)
        except ValueError:
            return WRONG_CLASSIFICATION, f"invalid violation_type value: {claimed}"

        if claimed_vt == ground_truth.violation_type:
            return CORRECT_CLASSIFICATION, (
                f"correct classification: {claimed_vt.value} (+{CORRECT_CLASSIFICATION})"
            )
        return WRONG_CLASSIFICATION, (
            f"wrong classification: got '{claimed_vt.value}', "
            f"expected '{ground_truth.violation_type.value}' ({WRONG_CLASSIFICATION})"
        )

    def _terminal_reward(
        self,
        at: ActionType,
        step: int,
        ground_truth: GroundTruth,
        difficulty: str,
    ) -> tuple[float, str]:
        expected = ground_truth.expected_action
        severity = ground_truth.final_severity

        # Efficiency: steps beyond the minimum allowed
        min_steps = {"easy": 1, "medium": 2, "hard": 3}[difficulty]
        extra = max(0, step - min_steps)
        efficiency_penalty = extra * EXTRA_STEP_PENALTY

        # Escalate on ambiguous / restricted content
        if at == ActionType.escalate:
            if ground_truth.violation_type == ViolationType.restricted:
                r = ESCALATE_AMBIGUOUS + efficiency_penalty
                return r, f"escalate on ambiguous content (+{ESCALATE_AMBIGUOUS}), efficiency {efficiency_penalty:.2f}"
            else:
                r = ESCALATE_UNNECESSARY + efficiency_penalty
                return r, f"unnecessary escalate ({ESCALATE_UNNECESSARY}), efficiency {efficiency_penalty:.2f}"

        # Exact match
        if at == expected:
            r = CORRECT_TERMINAL + efficiency_penalty
            return r, f"correct action: {at.value} (+{CORRECT_TERMINAL}), efficiency {efficiency_penalty:.2f}"

        # False negative: agent chose allow/flag when remove was required for serious violation
        is_false_negative = (
            at in (ActionType.allow, ActionType.flag)
            and expected == ActionType.remove
            and ground_truth.violation_type in _SEVERE_VIOLATIONS
            and SEVERITY_ORDER[severity] >= SEVERITY_ORDER[Severity.high]
        )
        if is_false_negative:
            r = FALSE_NEGATIVE_PENALTY + efficiency_penalty
            return r, (
                f"false negative: chose '{at.value}' but '{expected.value}' required "
                f"for {ground_truth.violation_type.value}/{severity.value} "
                f"({FALSE_NEGATIVE_PENALTY})"
            )

        r = WRONG_TERMINAL + efficiency_penalty
        return r, (
            f"wrong action: chose '{at.value}', expected '{expected.value}' "
            f"({WRONG_TERMINAL}), efficiency {efficiency_penalty:.2f}"
        )
