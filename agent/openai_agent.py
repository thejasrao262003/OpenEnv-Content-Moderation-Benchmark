"""
OpenAI agent for the OpenENV moderation environment.

The agent:
  1. Resets the episode via StateManager
  2. Loops: builds a prompt from the current observation → calls OpenAI → parses action → steps
  3. Stops when done=True
  4. Returns the graded result

The environment (policy, reward, grader) stays fully deterministic.
The LLM is ONLY the decision-making layer.
"""
from __future__ import annotations

import json
import logging
import os
import re

from openai import OpenAI

from agent.prompts import SYSTEM_PROMPT, build_turn_prompt
from server.grader import Grader
from server.state_manager import StateManager
from models import (
    Action,
    ActionType,
    BaselineResult,
    TaskConfig,
)

logger = logging.getLogger(__name__)

_MODEL_NAME = "gpt-4o-mini"
_VALID_ACTION_TYPES = {a.value for a in ActionType}


class OpenAIAgent:
    """LLM-driven agent using the OpenAI SDK."""

    def __init__(self, state_manager: StateManager, grader: Grader) -> None:
        self._sm = state_manager
        self._grader = grader
        self._client = self._init_client()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def run(self, task_config: TaskConfig) -> BaselineResult:
        """Run a full episode and return the graded result."""
        obs = self._sm.reset(task_config)

        # Multi-turn chat history array
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        while not obs.done:
            turn_prompt = build_turn_prompt(obs.model_dump())
            messages.append({"role": "user", "content": turn_prompt})
            
            action, response_content = self._get_action(messages)
            
            messages.append({"role": "assistant", "content": response_content})

            logger.info(
                "OpenAI → action=%s params=%s",
                action.action_type.value,
                action.parameters,
            )

            result = self._sm.step(action)
            obs = result.observation

        episode = self._sm.get_episode_state()
        score = self._grader.score(episode)

        return BaselineResult(
            task_id=task_config.task_id,
            seed=task_config.seed,
            score=score,
            trajectory=episode.trajectory,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _init_client(self) -> OpenAI:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY environment variable is required "
                "to use the OpenAI agent."
            )
        return OpenAI(api_key=api_key)

    def _get_action(self, messages: list[dict]) -> tuple[Action, str]:
        """Send the conversation to OpenAI and parse its action response."""
        response = self._client.chat.completions.create(
            model=_MODEL_NAME,
            messages=messages,
            temperature=0.0,
        )
        raw = response.choices[0].message.content or ""
        return self._parse_action(raw), raw

    def _parse_action(self, raw: str) -> Action:
        """Parse LLM JSON output into an Action; fall back to escalate on failure."""
        # Strip markdown fences if the model wrapped the JSON
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
        raw = raw.strip()

        try:
            data = json.loads(raw)
            action_type_str = data.get("action_type", "")
            if action_type_str not in _VALID_ACTION_TYPES:
                raise ValueError(f"Unknown action_type: '{action_type_str}'")
            params = data.get("parameters", {})
            if not isinstance(params, dict):
                params = {}
            return Action(action_type=ActionType(action_type_str), parameters=params)
        except Exception as exc:
            logger.warning(
                "Could not parse OpenAI response (%s): %r — defaulting to escalate",
                exc,
                raw,
            )
            return Action(action_type=ActionType.escalate)
