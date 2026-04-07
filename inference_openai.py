"""
Inference Script (OpenAI) — OpenENV Content Moderation Environment
===================================================================

Validation script using the OpenAI API directly (api.openai.com).
Use this to confirm the agent logic produces correct results,
then compare scores against inference.py with a custom HF model.

Required:
    OPENAI_API_KEY   Your OpenAI API key

Optional:
    OPENAI_MODEL     Model to use (default: gpt-4o-mini)

Run:
    OPENAI_API_KEY=sk-... python inference_openai.py

Same agent logic as inference.py — only the client config differs.
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from dotenv import load_dotenv
from dataclasses import dataclass, field

load_dotenv()
from openai import OpenAI

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
API_KEY    = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not API_KEY:
    print("ERROR: OPENAI_API_KEY environment variable is required.", file=sys.stderr)
    sys.exit(1)

sys.path.insert(0, os.path.dirname(__file__))

from data.tasks import TASKS
from env.grader import Grader
from env.state_manager import StateManager
from models.schemas import Action, ActionType, TaskConfig

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# OpenAI client — pointed at api.openai.com (no base_url override)
client = OpenAI(api_key=API_KEY)

# ---------------------------------------------------------------------------
# Prompts (identical to inference.py)
# ---------------------------------------------------------------------------
CLASSIFY_PROMPT = """\
You are a content moderation classifier.

Classify the violation type of the post below.

Violation types:
- harassment   : explicit threats, targeted abuse, doxxing, coercion, stalking, blackmail
- misinformation: false health/safety claims, dangerous medical advice, conspiracies with public harm potential
- restricted   : borderline — unverified allegations, aggressive reviews, organisational criticism
- safe         : protected opinion, legitimate consumer review, no policy violation

Output JSON with a confidence score (0.0–1.0):
{"action_type": "mark_violation_type", "parameters": {"violation_type": "<type>"}, "confidence": <float>}

Confidence guide:
- 0.9+  : completely obvious (explicit death threat, fabricated study citation)
- 0.7–0.9: clear but some nuance (implied threat, aggressive allegation)
- 0.5–0.7: genuine ambiguity — classify your best guess
- < 0.5 : very unclear — default to "restricted" and flag for review

Respond with ONLY the JSON object.
"""

DECIDE_PROMPT = """\
You are a content moderation decision agent.

Based on all investigation results, choose the correct terminal moderation action.

Actions:
- allow    : post is safe, no violation, no action needed
- flag     : borderline — queue for human review, do not remove yet
- remove   : clear policy violation, immediate removal required
- escalate : conflicting signals that cannot be resolved — senior moderator needed

Decision rules (apply in order):
1. harassment OR misinformation at HIGH/CRITICAL severity → remove
2. misinformation at LOW/MEDIUM severity with moderate engagement → flag (not remove)
3. restricted content → flag (or escalate if genuinely unresolvable)
4. safe / protected opinion → allow
5. Unresolvable after full investigation → escalate

Geo modifiers:
- EU  : misinformation at medium severity → remove (DSA obligation, stricter than US)
- IN  : high engagement (>5000 total) amplifies severity — treat high as critical
- UK  : coordinated harassment campaigns → remove even at "high" (not just critical)
- US  : most permissive — flag before remove for borderline misinformation

Scoring penalties you must avoid:
- False negative (allow/flag when should remove harassment/misinformation) = HEAVY penalty
- Wrong action = 0 points for the 50% action weight
- When uncertain between "allow" and "flag" → always choose "flag"

Output JSON with confidence (0.0–1.0):
{"action_type": "<allow|flag|remove|escalate>", "parameters": {}, "confidence": <float>}

Respond with ONLY the JSON object.
"""

# ---------------------------------------------------------------------------
# Agent state
# ---------------------------------------------------------------------------
@dataclass
class AgentState:
    investigations_done: set[str] = field(default_factory=set)
    classified: bool = False
    violation_type: str | None = None
    steps_taken: int = 0
    last_confidence: float = 1.0


# ---------------------------------------------------------------------------
# Planner (identical logic to inference.py)
# ---------------------------------------------------------------------------
_INVESTIGATION_PRIORITY = [
    ActionType.fetch_user_history,
    ActionType.check_policy_clause,
    ActionType.fetch_thread_context,
]


def _total_engagement(obs: dict) -> int:
    eng = obs.get("engagement", {})
    return eng.get("likes", 0) + eng.get("shares", 0) + eng.get("comments", 0)


def _is_obvious_threat(content: str) -> bool:
    markers = [
        "kill you", "i will kill", "find you and", "watch your back",
        "where you live", "make you regret", "dead to me", "living hell",
        "home address", "pay up or", "cannot be responsible", "final warning",
        "say goodbye to your job",
    ]
    c = content.lower()
    return any(m in c for m in markers)


def _plan_next_investigation(state: AgentState, obs: dict, difficulty: str) -> ActionType | None:
    remaining = obs["max_steps"] - obs["step"]
    content = obs.get("content", "")
    geo = obs.get("geo", "US")
    total_eng = _total_engagement(obs)
    done = state.investigations_done

    if remaining <= 2:
        return None

    for inv in _INVESTIGATION_PRIORITY:
        if inv.value in done:
            continue

        if inv == ActionType.fetch_user_history:
            return inv

        if inv == ActionType.check_policy_clause:
            if difficulty in ("medium", "hard"):
                return inv
            coercion_signals = any(w in content.lower() for w in
                                   ["address", "screenshots", "pay up", "extort", "blackmail"])
            if coercion_signals:
                return inv
            if _is_obvious_threat(content) and state.last_confidence >= 0.75:
                continue

        if inv == ActionType.fetch_thread_context:
            if difficulty == "hard":
                return inv
            if difficulty == "medium" and (total_eng > 500 or geo in ("EU", "UK")):
                return inv
            if state.classified and state.last_confidence < 0.65:
                return inv
            if geo in ("EU", "UK") and not _is_obvious_threat(content):
                return inv
            continue

    return None


def _fast_decision(state: AgentState, obs: dict) -> ActionType | None:
    vt = state.violation_type
    remaining = obs["max_steps"] - obs["step"]
    confidence = state.last_confidence

    if remaining <= 1:
        if vt in ("harassment", "misinformation"):
            return ActionType.remove
        if vt == "restricted":
            return ActionType.flag
        return ActionType.allow

    if (vt == "harassment"
            and confidence >= 0.85
            and "fetch_user_history" in state.investigations_done):
        return ActionType.remove

    if vt == "safe" and confidence >= 0.80:
        return ActionType.allow

    return None


# ---------------------------------------------------------------------------
# LLM call wrapper
# ---------------------------------------------------------------------------
_FALLBACK_ESCALATE = '{"action_type": "escalate", "parameters": {}, "confidence": 0.5}'
_FALLBACK_CLASSIFY  = '{"action_type": "mark_violation_type", "parameters": {"violation_type": "restricted"}, "confidence": 0.4}'


def _call_llm(messages: list[dict], fallback: str) -> str:
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.0,
            max_tokens=512,
        )
        return resp.choices[0].message.content or fallback
    except Exception as exc:
        logger.error("LLM call failed: %s — using fallback", exc)
        return fallback


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
_VALID = {a.value for a in ActionType}


def parse_action(raw: str) -> Action:
    text = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE).strip()

    try:
        data = json.loads(text)
        at = data.get("action_type", "")
        if at not in _VALID:
            raise ValueError(f"Unknown action_type: {at!r}")
        params = data.get("parameters", {})
        return Action(action_type=ActionType(at), parameters=params if isinstance(params, dict) else {})
    except Exception:
        pass

    match = re.search(r'\{[^{}]*"action_type"[^{}]*\}', text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            at = data.get("action_type", "")
            if at in _VALID:
                params = data.get("parameters", {})
                return Action(action_type=ActionType(at), parameters=params if isinstance(params, dict) else {})
        except Exception:
            pass

    for action_name in _VALID:
        if action_name in text:
            params: dict = {}
            if action_name == "mark_violation_type":
                for vt in ("harassment", "misinformation", "restricted", "safe"):
                    if vt in text:
                        params = {"violation_type": vt}
                        break
            return Action(action_type=ActionType(action_name), parameters=params)

    return Action(action_type=ActionType.escalate)


def _parse_with_confidence(raw: str) -> tuple[Action, float]:
    action = parse_action(raw)
    confidence = 1.0
    text = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE).strip()
    try:
        data = json.loads(text)
        c = data.get("confidence")
        if c is not None:
            confidence = max(0.0, min(1.0, float(c)))
    except Exception:
        m = re.search(r'"confidence"\s*:\s*([0-9.]+)', text)
        if m:
            try:
                confidence = max(0.0, min(1.0, float(m.group(1))))
            except Exception:
                pass
    return action, confidence


# ---------------------------------------------------------------------------
# Context builder
# ---------------------------------------------------------------------------
def _build_context(obs: dict) -> str:
    step = obs["step"]
    max_steps = obs["max_steps"]
    remaining = max_steps - step
    eng = obs.get("engagement", {})
    total_eng = eng.get("likes", 0) + eng.get("shares", 0) + eng.get("comments", 0)

    lines = [
        f"Post content : {obs['content']}",
        f"Geo          : {obs['geo']} | Reports: {obs['reports']} | "
        f"Engagement: {total_eng:,} total "
        f"(likes={eng.get('likes',0):,}, shares={eng.get('shares',0):,}, "
        f"comments={eng.get('comments',0):,})",
        f"Step         : {step}/{max_steps}  (remaining: {remaining})",
    ]

    if remaining <= 2:
        lines.append("⚠️  FINAL STEP: Output a terminal action (allow/flag/remove/escalate) NOW.")

    if obs.get("user_history") is not None:
        lines.append("User history : " + " | ".join(obs["user_history"]))
    if obs.get("thread_context") is not None:
        lines.append("Thread ctx   : " + " | ".join(obs["thread_context"]))
    if obs.get("policy_clause") is not None:
        lines.append(f"Policy clause: {obs['policy_clause']}")
    if obs.get("violation_type") is not None:
        lines.append(f"Classified   : {obs['violation_type']}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Episode runner (identical logic to inference.py)
# ---------------------------------------------------------------------------
def run_episode(task: TaskConfig, sm: StateManager, grader: Grader) -> dict:
    obs = sm.reset(task)
    state = AgentState()
    difficulty = task.difficulty

    classify_messages: list[dict] = [{"role": "system", "content": CLASSIFY_PROMPT}]
    decide_messages: list[dict]   = [{"role": "system", "content": DECIDE_PROMPT}]

    while not obs.done:
        obs_dict = obs.model_dump()
        remaining = obs.max_steps - obs.step

        # Phase 1: deterministic investigation
        if not state.classified:
            next_inv = _plan_next_investigation(state, obs_dict, difficulty)
            if next_inv is not None:
                result = sm.step(Action(action_type=next_inv))
                state.investigations_done.add(next_inv.value)
                state.steps_taken += 1
                obs = result.observation
                continue

        # Phase 2: LLM classify
        if not state.classified:
            classify_messages.append({"role": "user", "content": _build_context(obs_dict)})
            raw = _call_llm(classify_messages, _FALLBACK_CLASSIFY)
            classify_messages.append({"role": "assistant", "content": raw})

            action, confidence = _parse_with_confidence(raw)
            state.last_confidence = confidence

            if action.action_type != ActionType.mark_violation_type:
                vt_guess = action.parameters.get("violation_type", "restricted")
                if vt_guess not in ("harassment", "misinformation", "restricted", "safe"):
                    vt_guess = "restricted"
                action = Action(
                    action_type=ActionType.mark_violation_type,
                    parameters={"violation_type": vt_guess},
                )

            result = sm.step(action)
            state.classified = True
            state.violation_type = action.parameters.get("violation_type")
            state.steps_taken += 1
            obs = result.observation

            # Low-confidence bonus investigation
            if confidence < 0.60 and remaining > 3:
                obs_dict = obs.model_dump()
                bonus_inv = _plan_next_investigation(state, obs_dict, difficulty)
                if bonus_inv is not None:
                    result = sm.step(Action(action_type=bonus_inv))
                    state.investigations_done.add(bonus_inv.value)
                    state.steps_taken += 1
                    obs = result.observation

            continue

        # Phase 3: fast-path or LLM decide
        fast = _fast_decision(state, obs_dict)
        if fast is not None:
            result = sm.step(Action(action_type=fast))
            state.steps_taken += 1
            obs = result.observation
            continue

        decide_messages.append({"role": "user", "content": _build_context(obs_dict)})
        raw = _call_llm(decide_messages, _FALLBACK_ESCALATE)
        decide_messages.append({"role": "assistant", "content": raw})

        action, confidence = _parse_with_confidence(raw)
        state.last_confidence = confidence

        if (action.action_type == ActionType.allow
                and state.violation_type in ("harassment", "misinformation")
                and confidence < 0.75):
            action = Action(action_type=ActionType.flag)

        if action.action_type not in (
            ActionType.allow, ActionType.flag, ActionType.remove, ActionType.escalate
        ):
            action = Action(action_type=ActionType.escalate)

        result = sm.step(action)
        state.steps_taken += 1
        obs = result.observation

    episode = sm.get_episode_state()
    score = grader.score(episode)
    return {
        "task_id": task.task_id,
        "seed": task.seed,
        "total": round(score.total, 4),
        "final_action_score": round(score.final_action_score, 4),
        "classification_score": round(score.classification_score, 4),
        "investigation_score": round(score.investigation_score, 4),
        "efficiency_score": round(score.efficiency_score, 4),
        "agent_action": score.breakdown.get("agent_action"),
        "expected_action": score.breakdown.get("expected_action"),
        "steps": obs.step,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print(f"\n{'='*60}")
    print("  OpenENV — Inference (OpenAI validation run)")
    print(f"  Model   : {MODEL_NAME}")
    print(f"  API URL : api.openai.com")
    print(f"{'='*60}\n")

    sm = StateManager()
    grader = Grader()
    results = []
    total_start = time.time()

    for task_id, task in TASKS.items():
        print(f"▶  {task_id}  (seed={task.seed}, difficulty={task.difficulty})")
        t0 = time.time()
        try:
            r = run_episode(task, sm, grader)
        except Exception as exc:
            print(f"   ERROR: {exc}")
            r = {"task_id": task_id, "total": 0.0, "error": str(exc)}
        elapsed = time.time() - t0

        results.append(r)
        if "error" not in r:
            correct = "✓" if r["agent_action"] == r["expected_action"] else "✗"
            print(
                f"   {correct} Score: {r['total']:.2f}  "
                f"(action={r['final_action_score']:.2f}  "
                f"class={r['classification_score']:.2f}  "
                f"inv={r['investigation_score']:.2f}  "
                f"eff={r['efficiency_score']:.2f})  "
                f"steps={r['steps']}  [{elapsed:.1f}s]"
            )
            print(f"   agent={r['agent_action']}  expected={r['expected_action']}")
        print()

    total_elapsed = time.time() - total_start
    avg = sum(r.get("total", 0) for r in results) / len(results)

    print(f"{'='*60}")
    print(f"  Average score : {avg:.4f}")
    print(f"  Total runtime : {total_elapsed:.1f}s")
    print(f"{'='*60}\n")

    print(json.dumps({"model": MODEL_NAME, "results": results, "average": round(avg, 4)}, indent=2))


if __name__ == "__main__":
    main()
