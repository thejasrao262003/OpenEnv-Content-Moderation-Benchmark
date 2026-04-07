"""
Rule-based baseline agent.

Used by the /baseline endpoint.  No LLM — purely heuristic so it always
produces a score and is fully reproducible regardless of API key availability.

Strategy (per difficulty):
  easy   → fetch_user_history → mark_violation_type → remove/allow
  medium → fetch_user_history → check_policy_clause → mark_violation_type → action
  hard   → fetch_user_history → fetch_thread_context → check_policy_clause
           → mark_violation_type → action
"""
from __future__ import annotations

import re

from server.grader import Grader
from server.state_manager import StateManager
from models import (
    Action,
    ActionType,
    BaselineResult,
    TaskConfig,
    ViolationType,
)

_THREAT_PATTERNS = [
    r"\bkill\b", r"\bmurder\b", r"\bstab\b", r"\bshoot\b",
    r"\bfind you\b", r"\bwatch your back\b", r"\bmake you regret\b",
    r"\bwhere you live\b", r"\bfinal warning\b", r"\bdead to me\b",
    r"\bliving hell\b", r"\baccidents happen\b", r"\bhome address\b",
    r"\bcannot be responsible\b", r"\bpay up\b",
    r"\bsay goodbye to your\b",
]
_MISINFO_PATTERNS = [
    r"\bvaccines? cause\b", r"\b5g.*covid\b", r"\bdoctors are hiding\b",
    r"\bgovernment.*hiding\b", r"\bradiation weakens\b",
    r"\bnatural immunity.*stronger\b", r"\bhydroxychloroquine cures\b",
    r"\bmasks cause\b", r"\bcure.*cancer\b", r"\bchemtrails\b",
    r"\bfluoride.*docile\b", r"\bmass medication\b",
]
_RESTRICTED_PATTERNS = [
    r"\bscam\b", r"\bcriminals?\b", r"\bponzi\b", r"\bfaked.*audit\b",
    r"\bfraud\b", r"\bdisappear with\b", r"\bblacklist\b",
    r"\bfake.*reviews?\b", r"\blife savings\b", r"\billegal.*advice\b",
    r"\bcover.up\b", r"\bcult\b",
]


def _classify(content: str) -> ViolationType:
    lowered = content.lower()
    if any(re.search(p, lowered) for p in _THREAT_PATTERNS):
        return ViolationType.harassment
    if any(re.search(p, lowered) for p in _MISINFO_PATTERNS):
        return ViolationType.misinformation
    if any(re.search(p, lowered) for p in _RESTRICTED_PATTERNS):
        return ViolationType.restricted
    return ViolationType.safe


def _decide_action(violation: ViolationType, has_prior_violations: bool) -> ActionType:
    if violation == ViolationType.safe:
        return ActionType.allow
    if violation == ViolationType.harassment:
        return ActionType.remove
    if violation == ViolationType.misinformation:
        return ActionType.remove
    if violation == ViolationType.restricted:
        return ActionType.flag if has_prior_violations else ActionType.escalate
    return ActionType.allow


class BaselineAgent:
    """Deterministic rule-based agent that runs a full episode."""

    def __init__(self, state_manager: StateManager, grader: Grader) -> None:
        self._sm = state_manager
        self._grader = grader

    def run(self, task_config: TaskConfig) -> BaselineResult:
        obs = self._sm.reset(task_config)
        diff = task_config.difficulty

        # Build investigation plan by difficulty
        investigation_steps: list[ActionType] = [ActionType.fetch_user_history]
        if diff in ("medium", "hard"):
            investigation_steps.append(ActionType.check_policy_clause)
        if diff == "hard":
            investigation_steps.append(ActionType.fetch_thread_context)

        has_prior_violations = False

        # Run investigation
        for inv_action in investigation_steps:
            result = self._sm.step(Action(action_type=inv_action))
            obs = result.observation
            if result.done:
                break

            # Parse user history for prior violations
            if inv_action == ActionType.fetch_user_history and obs.user_history:
                has_prior_violations = any(
                    "violation" in h.lower() for h in obs.user_history
                )

        if not obs.done:
            # Classify
            violation = _classify(obs.content)
            result = self._sm.step(
                Action(
                    action_type=ActionType.mark_violation_type,
                    parameters={"violation_type": violation.value},
                )
            )
            obs = result.observation

        if not obs.done:
            # Decide terminal action
            violation = _classify(obs.content)
            terminal = _decide_action(violation, has_prior_violations)
            result = self._sm.step(Action(action_type=terminal))
            obs = result.observation

        # Grade
        episode = self._sm.get_episode_state()
        score = self._grader.score(episode)

        return BaselineResult(
            task_id=task_config.task_id,
            seed=task_config.seed,
            score=score,
            trajectory=episode.trajectory,
        )
