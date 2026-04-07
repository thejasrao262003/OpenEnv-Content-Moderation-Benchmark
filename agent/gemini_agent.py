"""
Gemini 2.5 Flash agent for the OpenENV moderation environment.

Uses the latest google-genai SDK (google-genai>=1.0).

The agent:
  1. Resets the episode via StateManager
  2. Loops: builds a prompt from the current observation → calls Gemini → parses action → steps
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

from google import genai
from google.genai import types

from agent.prompts import SYSTEM_PROMPT, build_turn_prompt
from env.grader import Grader
from env.state_manager import StateManager
from models.schemas import (
    Action,
    ActionType,
    BaselineResult,
    TaskConfig,
)

logger = logging.getLogger(__name__)

_MODEL_NAME = "gemini-2.5-flash"
_VALID_ACTION_TYPES = {a.value for a in ActionType}


class GeminiAgent:
    """LLM-driven agent using Gemini 2.5 Flash via the google-genai SDK."""

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

        # Start a multi-turn chat with the system prompt baked in
        chat = self._client.chats.create(
            model=_MODEL_NAME,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.0,    # deterministic as possible
            ),
        )

        while not obs.done:
            turn_prompt = build_turn_prompt(obs.model_dump())
            action = self._get_action(chat, turn_prompt)

            logger.info(
                "Gemini → action=%s params=%s",
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

    def _init_client(self) -> genai.Client:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GOOGLE_API_KEY or GEMINI_API_KEY environment variable is required "
                "to use the Gemini agent."
            )
        return genai.Client(api_key=api_key)

    def _get_action(self, chat: genai.chats.Chat, turn_prompt: str) -> Action:
        """Send the current observation to Gemini and parse its action response."""
        response = chat.send_message(turn_prompt)
        raw = response.text.strip()
        return self._parse_action(raw)

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
                "Could not parse Gemini response (%s): %r — defaulting to escalate",
                exc,
                raw,
            )
            return Action(action_type=ActionType.escalate)
