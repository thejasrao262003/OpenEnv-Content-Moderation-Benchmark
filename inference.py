"""
Inference Script — OpenENV Content Moderation Environment
==========================================================

MANDATORY environment variables:
    API_BASE_URL   The API endpoint for the LLM  (e.g. https://router.huggingface.co/v1)
    MODEL_NAME     The model identifier           (e.g. meta-llama/Llama-3.3-70B-Instruct)
    HF_TOKEN       Your Hugging Face API key

Run:
    python inference.py

Architecture: Hybrid agent — deterministic planner for investigation,
LLM called at most TWICE per episode (classify + decide).
Target runtime: < 5 minutes on 2 vCPU / 8 GB RAM.
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field

from openai import OpenAI

# ---------------------------------------------------------------------------
# Environment variables — match the exact names required by the OpenEnv spec
# ---------------------------------------------------------------------------
API_BASE_URL = os.getenv("API_BASE_URL")
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

_missing = [
    k for k, v in [
        ("HF_TOKEN", API_KEY),
        ("MODEL_NAME", MODEL_NAME),
        ("API_BASE_URL", API_BASE_URL),
    ] if not v
]

if _missing:
    print(f"WARNING: env var(s) not set, using defaults: {', '.join(_missing)}", file=sys.stderr)
if not API_KEY:
    print("ERROR: HF_TOKEN environment variable is required.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Inline environment — no external HTTP server needed for inference
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(__file__))

from server.tasks import TASKS
from server.grader import Grader
from server.state_manager import StateManager
from models import Action, ActionType, TaskConfig

BENCHMARK = "content-moderation"
SUCCESS_SCORE_THRESHOLD = 0.5  # normalized score in [0, 1]

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OpenAI client (pointed at HuggingFace router or any OpenAI-compatible base)
# ---------------------------------------------------------------------------
client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)


# ---------------------------------------------------------------------------
# Structured stdout log helpers — exact format required by the evaluator
# ---------------------------------------------------------------------------

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: str | None = None) -> None:
    error_val = error if error else "null"
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: list[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )

# ---------------------------------------------------------------------------
# Prompts — two focused prompts instead of one generic one.
# Classify prompt: content analysis only.
# Decide prompt: terminal action with full scoring context.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
You are an AI content moderation agent. Evaluate social media posts and make
the correct moderation decision through structured investigation.

You will be called in two modes:

MODE 1 — CLASSIFY: Identify the violation type.
MODE 2 — DECIDE: Choose the terminal moderation action.

Scoring context you must optimize for:
- Correct final action = 50% of your total score
- False negatives (letting through harassment/misinformation) carry a HEAVY penalty
- Extra steps reduce your efficiency score — be decisive
- When uncertain: prefer "flag" over "allow" (conservative bias protects against false negatives)

Respond with ONLY a JSON object — no markdown, no explanation.
"""

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
# Agent internal state — tracks progress across steps (not part of env)
# ---------------------------------------------------------------------------
@dataclass
class AgentState:
    investigations_done: set[str] = field(default_factory=set)
    classified: bool = False
    violation_type: str | None = None
    steps_taken: int = 0
    last_confidence: float = 1.0


# ---------------------------------------------------------------------------
# Investigation planner — deterministic, zero LLM calls
# ---------------------------------------------------------------------------

# Priority order: user_history almost always required, policy_clause second
# (needed by medium/hard), thread_context third (high-engagement / viral cases).
_INVESTIGATION_PRIORITY = [
    ActionType.fetch_user_history,
    ActionType.check_policy_clause,
    ActionType.fetch_thread_context,
]


def _total_engagement(obs: dict) -> int:
    eng = obs.get("engagement", {})
    return eng.get("likes", 0) + eng.get("shares", 0) + eng.get("comments", 0)


def _is_obvious_threat(content: str) -> bool:
    """True for content so unambiguous that policy/thread context won't change the outcome."""
    markers = [
        "kill you", "i will kill", "find you and", "watch your back",
        "where you live", "make you regret", "dead to me", "living hell",
        "home address", "pay up or", "cannot be responsible", "final warning",
        "say goodbye to your job",
    ]
    c = content.lower()
    return any(m in c for m in markers)


def _plan_next_investigation(
    state: AgentState, obs: dict, difficulty: str
) -> ActionType | None:
    """
    Return the next investigation action to take, or None if investigation is complete.
    Completely deterministic — no LLM involved.

    Strategy varies by difficulty because templates have different required_investigation sets:
      easy   : user_history almost always required; thread/policy only for some
      medium : check_policy_clause always required; thread for most; history for some
      hard   : check_policy_clause always required; thread for most; history for some
    """
    remaining = obs["max_steps"] - obs["step"]
    content = obs.get("content", "")
    geo = obs.get("geo", "US")
    total_eng = _total_engagement(obs)

    # Never investigate with <= 2 steps left — need classify + decide
    if remaining <= 2:
        return None

    done = state.investigations_done

    for inv in _INVESTIGATION_PRIORITY:
        if inv.value in done:
            continue  # already done

        if inv == ActionType.fetch_user_history:
            # Always take user_history — it's required by the majority of templates
            return inv

        if inv == ActionType.check_policy_clause:
            # Medium/hard: policy clause is always required
            if difficulty in ("medium", "hard"):
                return inv
            # Easy: only needed for doxxing/coercion templates (special policy sections)
            coercion_signals = any(w in content.lower() for w in
                                   ["address", "screenshots", "pay up", "extort", "blackmail"])
            if coercion_signals:
                return inv
            # Easy + obvious threat + high confidence → skip policy check
            if _is_obvious_threat(content) and state.last_confidence >= 0.75:
                continue  # no policy check needed, saves a step

        if inv == ActionType.fetch_thread_context:
            # Always take for hard tasks (viral misinfo needs thread to confirm severity)
            if difficulty == "hard":
                return inv
            # Medium: take for high-engagement or EU/UK (DSA/OSA context matters)
            if difficulty == "medium" and (total_eng > 500 or geo in ("EU", "UK")):
                return inv
            # Easy: take only if low confidence after classify
            if state.classified and state.last_confidence < 0.65:
                return inv
            # Easy: take for coordinated harassment signals (UK/EU implied threats)
            if geo in ("EU", "UK") and not _is_obvious_threat(content):
                return inv
            continue  # skip for easy obvious threats

    return None  # investigation complete


# ---------------------------------------------------------------------------
# Fast-path terminal decision — rule-based for high-confidence clear cases
# ---------------------------------------------------------------------------

def _fast_decision(state: AgentState, obs: dict) -> ActionType | None:
    """
    Apply deterministic rules for cut-and-dry cases. Returns ActionType or None (→ use LLM).
    This avoids an LLM call entirely for obvious outcomes, saving time and tokens.
    """
    vt = state.violation_type
    remaining = obs["max_steps"] - obs["step"]
    confidence = state.last_confidence

    # Force decision if last step
    if remaining <= 1:
        if vt in ("harassment", "misinformation"):
            return ActionType.remove
        if vt == "restricted":
            return ActionType.flag
        return ActionType.allow

    # High-confidence harassment with user_history confirmed → remove immediately
    if (vt == "harassment"
            and confidence >= 0.85
            and "fetch_user_history" in state.investigations_done):
        return ActionType.remove

    # High-confidence safe content → allow immediately
    if vt == "safe" and confidence >= 0.80:
        return ActionType.allow

    # Cannot apply fast-path — defer to LLM
    return None


# ---------------------------------------------------------------------------
# LLM call wrapper — handles temperature rejection and errors
# ---------------------------------------------------------------------------

_FALLBACK_ESCALATE = '{"action_type": "escalate", "parameters": {}, "confidence": 0.5}'
_FALLBACK_CLASSIFY  = '{"action_type": "mark_violation_type", "parameters": {"violation_type": "restricted"}, "confidence": 0.4}'


def _call_llm(messages: list[dict], fallback: str) -> str:
    """Call the LLM with temperature fallback and full error handling."""
    for temperature in (0.0, 0.01):
        try:
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=temperature,
                max_tokens=512,
            )
            return resp.choices[0].message.content or fallback
        except Exception as exc:
            if temperature == 0.0 and "temperature" in str(exc).lower():
                continue  # retry with 0.01
            logger.error("LLM call failed (temp=%s): %s — using fallback", temperature, exc)
            return fallback
    return fallback


# ---------------------------------------------------------------------------
# Response parsing — kept from original for robustness across model families
# ---------------------------------------------------------------------------
_VALID = {a.value for a in ActionType}


def parse_action(raw: str) -> Action:
    """Parse LLM response into an Action. Three-tier fallback for verbose models."""
    text = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE).strip()

    # Tier 1: clean JSON parse
    try:
        data = json.loads(text)
        at = data.get("action_type", "")
        if at not in _VALID:
            raise ValueError(f"Unknown action_type: {at!r}")
        params = data.get("parameters", {})
        return Action(action_type=ActionType(at), parameters=params if isinstance(params, dict) else {})
    except Exception:
        pass

    # Tier 2: extract first {...} block containing action_type
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

    # Tier 3: scan for bare action name keyword
    for action_name in _VALID:
        if action_name in text:
            logger.warning("Extracted bare action_type %r from unstructured response", action_name)
            params: dict = {}
            if action_name == "mark_violation_type":
                for vt in ("harassment", "misinformation", "restricted", "safe"):
                    if vt in text:
                        params = {"violation_type": vt}
                        break
            return Action(action_type=ActionType(action_name), parameters=params)

    logger.warning("Could not parse LLM response — defaulting to escalate")
    return Action(action_type=ActionType.escalate)


def _parse_with_confidence(raw: str) -> tuple[Action, float]:
    """Parse action + extract optional confidence field. Returns (action, confidence)."""
    action = parse_action(raw)

    # Extract confidence from JSON (optional field — model may omit it)
    confidence = 1.0
    text = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE).strip()
    try:
        data = json.loads(text)
        c = data.get("confidence")
        if c is not None:
            confidence = max(0.0, min(1.0, float(c)))
    except Exception:
        # Try regex extraction from verbose response
        m = re.search(r'"confidence"\s*:\s*([0-9.]+)', text)
        if m:
            try:
                confidence = max(0.0, min(1.0, float(m.group(1))))
            except Exception:
                pass

    return action, confidence


# ---------------------------------------------------------------------------
# Context block builder — compact observation for LLM classify/decide calls
# ---------------------------------------------------------------------------

def _build_context(obs: dict) -> str:
    """Compact observation formatted for focused LLM calls."""
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
# Main episode runner — hybrid planner
# ---------------------------------------------------------------------------

def run_episode(task: TaskConfig, sm: StateManager, grader: Grader) -> dict:
    """
    Hybrid agent loop:
      1. Deterministic planner drives all investigation steps (no LLM)
      2. LLM called ONCE for classification (mark_violation_type)
      3. LLM called ONCE for terminal decision (allow/flag/remove/escalate)
      4. Confidence gating: if classify confidence < 0.6, do one more investigation
      5. Fast-path: obvious cases decided without LLM terminal call
      6. Conservative bias: prefer flag over allow when uncertain

    Emits mandatory structured logs: [START], [STEP], [END]
    """
    log_start(task=task.task_id, env=BENCHMARK, model=MODEL_NAME)

    obs = sm.reset(task)
    state = AgentState()
    difficulty = task.difficulty
    step_rewards: list[float] = []

    # Separate message histories for classify and decide LLM calls
    classify_messages: list[dict] = [
        {"role": "system", "content": CLASSIFY_PROMPT}
    ]
    decide_messages: list[dict] = [
        {"role": "system", "content": DECIDE_PROMPT}
    ]

    try:
        while not obs.done:
            obs_dict = obs.model_dump()
            remaining = obs.max_steps - obs.step

            # ── PHASE 1: INVESTIGATE (deterministic, no LLM) ──────────────────
            if not state.classified:
                next_inv = _plan_next_investigation(state, obs_dict, difficulty)
                if next_inv is not None:
                    result = sm.step(Action(action_type=next_inv))
                    state.investigations_done.add(next_inv.value)
                    state.steps_taken += 1
                    obs = result.observation
                    reward = float(result.reward or 0.0)
                    step_rewards.append(reward)
                    log_step(step=obs.step, action=next_inv.value, reward=reward, done=result.done)
                    logger.info("[INV] %s", next_inv.value)
                    continue

            # ── PHASE 2: CLASSIFY (LLM call #1) ───────────────────────────────
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
                reward = float(result.reward or 0.0)
                step_rewards.append(reward)
                log_step(step=obs.step, action=action.action_type.value, reward=reward, done=result.done)
                logger.info("[CLS] %s  confidence=%.2f", state.violation_type, confidence)

                if confidence < 0.60 and remaining > 3:
                    obs_dict = obs.model_dump()
                    bonus_inv = _plan_next_investigation(state, obs_dict, difficulty)
                    if bonus_inv is not None:
                        result = sm.step(Action(action_type=bonus_inv))
                        state.investigations_done.add(bonus_inv.value)
                        state.steps_taken += 1
                        obs = result.observation
                        reward = float(result.reward or 0.0)
                        step_rewards.append(reward)
                        log_step(step=obs.step, action=bonus_inv.value, reward=reward, done=result.done)
                        logger.info("[INV+] %s  (low-confidence bonus)", bonus_inv.value)

                continue

            # ── PHASE 3: DECIDE ───────────────────────────────────────────────
            fast = _fast_decision(state, obs_dict)
            if fast is not None:
                result = sm.step(Action(action_type=fast))
                state.steps_taken += 1
                obs = result.observation
                reward = float(result.reward or 0.0)
                step_rewards.append(reward)
                log_step(step=obs.step, action=fast.value, reward=reward, done=result.done)
                logger.info("[FAST] %s", fast.value)
                continue

            obs_dict = obs.model_dump()
            decide_messages.append({"role": "user", "content": _build_context(obs_dict)})
            raw = _call_llm(decide_messages, _FALLBACK_ESCALATE)
            decide_messages.append({"role": "assistant", "content": raw})

            action, confidence = _parse_with_confidence(raw)
            state.last_confidence = confidence

            if (action.action_type == ActionType.allow
                    and state.violation_type in ("harassment", "misinformation")
                    and confidence < 0.75):
                logger.info("[OVERRIDE] allow → flag  (low confidence on dangerous type)")
                action = Action(action_type=ActionType.flag)

            if action.action_type not in (
                ActionType.allow, ActionType.flag, ActionType.remove, ActionType.escalate
            ):
                logger.warning("[COERCE] non-terminal action from LLM → escalate")
                action = Action(action_type=ActionType.escalate)

            result = sm.step(action)
            state.steps_taken += 1
            obs = result.observation
            reward = float(result.reward or 0.0)
            step_rewards.append(reward)
            log_step(step=obs.step, action=action.action_type.value, reward=reward, done=result.done)
            logger.info("[DECIDE] %s  confidence=%.2f", action.action_type.value, confidence)

    except Exception as exc:
        logger.error("Episode error: %s", exc)

    episode = sm.get_episode_state()
    score = grader.score(episode)
    success = score.total >= SUCCESS_SCORE_THRESHOLD

    log_end(success=success, steps=obs.step, score=score.total, rewards=step_rewards)

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
    print("  OpenENV Content Moderation — Inference Script")
    print(f"  Model   : {MODEL_NAME}")
    print(f"  API URL : {API_BASE_URL}")
    print(f"{'='*60}\n")

    sm = StateManager()
    grader = Grader()
    results = []
    total_start = time.time()

    for task_id, task in TASKS.items():
        print(f"▶  Running task: {task_id}  (seed={task.seed}, difficulty={task.difficulty})")
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

    # Machine-readable summary (consumed by evaluators)
    print(json.dumps({"model": MODEL_NAME, "results": results, "average": round(avg, 4)}, indent=2))


if __name__ == "__main__":
    main()
