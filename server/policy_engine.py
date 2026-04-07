"""
Deterministic policy engine.

Given post content + full context (user history, engagement, geo), computes:
  - violation_type
  - base_severity (before modifiers)
  - final_severity (after user-history + engagement + geo overrides)
  - expected_action

No ML — pure keyword/rule matching so evaluation is fully reproducible.
"""
from __future__ import annotations

import re

from models import (
    ActionType,
    GroundTruth,
    Severity,
    SEVERITY_ORDER,
    ViolationType,
)

# ---------------------------------------------------------------------------
# Keyword banks
# ---------------------------------------------------------------------------

_HARASSMENT_KEYWORDS = [
    r"\bkill\b", r"\bmurder\b", r"\bstab\b", r"\bshoot\b",
    r"\bdead\b.*\byou\b", r"\byou.*\bdead\b",
    r"\bfind you\b", r"\bwatch your back\b", r"\bmake you regret\b",
    r"\bhate you\b", r"\bdestroy you\b",
]

_MISINFORMATION_KEYWORDS = [
    r"\bvaccines? cause autism\b", r"\b5g.*covid\b", r"\bcovid.*5g\b",
    r"\bdoctors are hiding\b", r"\bgovernment.*hiding\b",
    r"\bspread awareness\b.*\bdelete this\b",
    r"\bponzi scheme\b", r"\bfaked.*audit\b",
    r"\bradiation weakens\b",
]

_RESTRICTED_KEYWORDS = [
    r"\bscam\b", r"\bstealing\b", r"\bcriminals?\b",
    r"\bproof\b.*\bfaked?\b", r"\bhave proof\b",
]


def _matches_any(text: str, patterns: list[str]) -> bool:
    lowered = text.lower()
    return any(re.search(p, lowered) for p in patterns)


# ---------------------------------------------------------------------------
# Severity ladder helpers
# ---------------------------------------------------------------------------

_SEVERITY_LIST = [Severity.low, Severity.medium, Severity.high, Severity.critical]


def _bump(severity: Severity, n: int = 1) -> Severity:
    idx = min(SEVERITY_ORDER[severity] + n, len(_SEVERITY_LIST) - 1)
    return _SEVERITY_LIST[idx]


def _drop(severity: Severity, n: int = 1) -> Severity:
    idx = max(SEVERITY_ORDER[severity] - n, 0)
    return _SEVERITY_LIST[idx]


# ---------------------------------------------------------------------------
# PolicyEngine
# ---------------------------------------------------------------------------

class PolicyEngine:
    """Evaluate a post against platform policy deterministically."""

    def evaluate(
        self,
        content: str,
        geo: str,
        user_history: list[str],
        engagement: dict[str, int],
    ) -> GroundTruth:
        violation = self._detect_violation(content)
        base_severity = self._base_severity(violation)
        final_severity = self._apply_modifiers(
            base_severity, violation, user_history, engagement, geo
        )
        expected_action = self._map_action(violation, final_severity)

        return GroundTruth(
            violation_type=violation,
            base_severity=base_severity,
            final_severity=final_severity,
            expected_action=expected_action,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _detect_violation(self, content: str) -> ViolationType:
        if _matches_any(content, _HARASSMENT_KEYWORDS):
            return ViolationType.harassment
        if _matches_any(content, _MISINFORMATION_KEYWORDS):
            return ViolationType.misinformation
        if _matches_any(content, _RESTRICTED_KEYWORDS):
            return ViolationType.restricted
        return ViolationType.safe

    def _base_severity(self, violation: ViolationType) -> Severity:
        return {
            ViolationType.harassment: Severity.high,
            ViolationType.misinformation: Severity.high,
            ViolationType.restricted: Severity.medium,
            ViolationType.safe: Severity.low,
        }[violation]

    def _apply_modifiers(
        self,
        severity: Severity,
        violation: ViolationType,
        user_history: list[str],
        engagement: dict[str, int],
        geo: str,
    ) -> Severity:
        # Prior violations escalate severity
        prior_violations = sum(
            1 for h in user_history if "violation" in h.lower()
        )
        if prior_violations >= 2:
            severity = _bump(severity)
        elif prior_violations == 1:
            severity = _bump(severity) if SEVERITY_ORDER[severity] < 3 else severity

        # High engagement spreads harm faster
        total_engagement = sum(engagement.values())
        if total_engagement > 10_000:
            severity = _bump(severity)
        elif total_engagement > 1_000:
            severity = _bump(severity) if SEVERITY_ORDER[severity] < 2 else severity

        # Geo overrides
        severity = self._geo_override(severity, violation, geo)

        return severity

    def _geo_override(
        self, severity: Severity, violation: ViolationType, geo: str
    ) -> Severity:
        if geo == "EU":
            # EU DSA: stricter on misinformation and defamation
            if violation in (ViolationType.misinformation, ViolationType.restricted):
                severity = _bump(severity)
        elif geo == "IN":
            # India: political content gets more lenience; health mis stays strict
            if violation == ViolationType.restricted:
                severity = _drop(severity)
        # US: default — no geo adjustment
        return severity

    def _map_action(
        self, violation: ViolationType, severity: Severity
    ) -> ActionType:
        if violation == ViolationType.safe:
            return ActionType.allow

        s = SEVERITY_ORDER[severity]

        if violation == ViolationType.harassment:
            # Harassment: flag medium, remove high+
            if s >= SEVERITY_ORDER[Severity.high]:
                return ActionType.remove
            return ActionType.flag

        if violation == ViolationType.misinformation:
            if s >= SEVERITY_ORDER[Severity.high]:
                return ActionType.remove
            if s == SEVERITY_ORDER[Severity.medium]:
                return ActionType.flag
            return ActionType.allow

        if violation == ViolationType.restricted:
            if s >= SEVERITY_ORDER[Severity.high]:
                return ActionType.flag
            if s == SEVERITY_ORDER[Severity.medium]:
                return ActionType.escalate
            return ActionType.allow

        return ActionType.allow
