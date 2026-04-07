---
title: Openenv Content Moderation
emoji: 🛡️
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 8000
pinned: false
---

# OpenENV — Content Moderation Environment

A **multi-step reinforcement learning environment** for AI content moderation agents, built on the [OpenEnv](https://github.com/meta-pytorch/OpenEnv) framework. Agents receive partial observations of real social media posts and must investigate context, classify violations, and make the correct moderation decision across **24 deterministic scenarios** spanning four real-world jurisdictions (US, EU, India, UK).

**Live Space:** `https://huggingface.co/spaces/ThejasRao/openenv-content-moderation`

---

## Why This Environment Matters

Content moderation is one of the most consequential tasks performed at internet scale. Human moderators review millions of posts daily under time pressure, incomplete context, and shifting policy landscapes. The decisions — remove, flag, allow, escalate — have real consequences for users, platforms, and society.

This environment makes that challenge trainable for AI agents:

- Posts arrive with **minimal context** (content, engagement metrics, geo, report count)
- Agents must **actively investigate** before deciding — fetching user history, thread context, policy clause
- Decisions must be **jurisdiction-aware**: the same post warrants different outcomes under EU DSA vs US First Amendment principles
- **Both types of error are penalised**: over-removal (flagging protected speech) and under-removal (missing critical harassment or viral misinformation)

This partial-observability + multi-step structure makes it ideal for training agents with RL methods like GRPO, PPO, or REINFORCE — where the reward signal emerges from a sequence of decisions, not a single output.

---

## OpenEnv Standard API

The environment implements the full [OpenEnv](https://github.com/meta-pytorch/OpenEnv) HTTP + WebSocket specification.

### HTTP Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Liveness check — returns `{"status": "healthy"}` |
| `GET` | `/tasks` | List all available tasks |
| `POST` | `/reset` | Start a new episode |
| `POST` | `/step` | Submit one action, receive observation + reward |
| `GET` | `/state` | Current observation (read-only, no state change) |
| `GET` | `/grader` | Final episode score — only available when `done=true` |
| `GET` | `/baseline` | Run the rule-based baseline agent on a task |
| `POST` | `/agent/run` | Run the configured LLM agent on a full episode |
| `GET` | `/docs` | Interactive OpenAPI documentation |

### WebSocket Endpoint

```
WS /ws
```

Persistent session — lower latency for sequential steps. The OpenEnv Python client uses this by default.

**Message types (client → server):**

```json
{"type": "reset", "data": {"task_id": "easy_harassment", "seed": 42}}
{"type": "step",  "data": {"action_type": "fetch_user_history", "parameters": {}}}
{"type": "state"}
{"type": "close"}
```

**Response types (server → client):**

```json
{"type": "observation", "data": {"observation": {...}, "reward": 0.20, "done": false}}
{"type": "state",       "data": {...}}
{"type": "error",       "data": {"message": "...", "code": "SESSION_ERROR"}}
```

### Request / Response Schemas

**POST `/reset`**
```json
// Request (task_id passed as extra field, seed optional)
{"task_id": "easy_harassment", "seed": 42}

// Response
{
  "observation": { "post_id": "...", "content": "...", "done": false, ... },
  "reward": null,
  "done": false
}
```

**POST `/step`**
```json
// Request — action wrapped under "action" key
{"action": {"action_type": "fetch_user_history", "parameters": {}}}

// Response
{
  "observation": { "step": 1, "user_history": ["..."], "done": false, ... },
  "reward": 0.20,
  "done": false
}
```

---

## Observation Space

Every step the agent receives:

| Field | Type | Always present | Description |
|---|---|---|---|
| `post_id` | string | ✅ | Unique post identifier |
| `content` | string | ✅ | Post text |
| `user_id` | string | ✅ | Poster's user ID |
| `reports` | int | ✅ | Number of user reports |
| `engagement` | dict | ✅ | `{likes, shares, comments}` |
| `geo` | enum | ✅ | `US \| EU \| IN \| UK` — policy jurisdiction |
| `step` | int | ✅ | Current step number |
| `max_steps` | int | ✅ | Episode step budget |
| `done` | bool | ✅ | Episode completed flag |
| `user_history` | list\|null | After `fetch_user_history` | Prior violations, account age |
| `thread_context` | list\|null | After `fetch_thread_context` | Thread replies and conversation |
| `policy_clause` | string\|null | After `check_policy_clause` | Applicable platform policy text |
| `violation_type` | enum\|null | After `mark_violation_type` | Classified violation category |

---

## Action Space

### Investigation actions — reveal hidden context, earn +0.20 reward each
| Action | Reveals |
|---|---|
| `fetch_user_history` | Prior violations, account creation date |
| `fetch_thread_context` | Replies, reactions, conversation tone |
| `check_policy_clause` | Applicable policy section for this geo + content type |

### Classification action — required before any terminal action
| Action | Parameters |
|---|---|
| `mark_violation_type` | `{"violation_type": "harassment \| misinformation \| restricted \| safe"}` |

### Terminal actions — end the episode
| Action | When to use |
|---|---|
| `allow` | Post is safe, no policy violation |
| `flag` | Borderline content — queue for human review |
| `remove` | Clear violation — immediate removal required |
| `escalate` | Genuinely ambiguous — route to senior moderator |

---

## Tasks

### `easy_harassment` — seed 42, max 6 steps
Clear harassment: explicit death threats, doxxing, stalking, coercion across US/EU/IN/UK jurisdictions. Violation is evident from content; user history confirms severity. A well-tuned agent needs 1–2 investigation steps.

**Expected action:** `remove`

### `medium_ambiguous` — seed 100, max 8 steps
Ambiguous commercial speech: aggressive reviews, unverified fraud allegations, whistleblower content. The correct action (allow/flag/escalate) depends on thread context and the applicable policy clause. EU DSA produces different outcomes than US policy for identical content.

**Expected actions:** `allow`, `flag`, or `escalate` depending on scenario

### `hard_misinformation` — seed 777, max 10 steps
Subtle and viral health misinformation: anti-vaccine claims, dangerous medical advice, infrastructure conspiracies. Severity depends on engagement scale, active public health emergency status, geo jurisdiction, and partial scientific basis. Frontier models frequently err here — over-removing low-reach conspiracies or under-removing viral health claims.

**Expected actions:** `remove` (high-severity viral misinfo) or `flag` (moderate-reach conspiracy)

---

## Reward Function

Rewards are **dense** — the agent receives a signal at every step, not just at episode end.

| Event | Reward |
|---|---|
| Investigation action (any) | **+0.20** |
| Correct violation classification | **+0.50** |
| Wrong violation classification | **−0.30** |
| Correct terminal action | **+1.00** |
| Wrong terminal action | **−0.50** |
| False negative (missed critical harassment / misinfo) | **−2.00** |
| Extra steps beyond minimum optimal | **−0.05** per step |

The **false-negative penalty** reflects real-world cost asymmetry: letting through a credible death threat or viral health misinformation is far more harmful than an over-removal. This asymmetry is intentional and pushes agents toward conservative, evidence-based decisions.

---

## Grader — Final Score (0.0–1.0)

The final episode score is a weighted sum of four components:

| Component | Weight | Description |
|---|---|---|
| Final action accuracy | **50%** | Correct terminal action? |
| Classification accuracy | **20%** | Correct violation type? |
| Investigation quality | **15%** | Gathered the recommended context signals? |
| Efficiency | **15%** | Reached decision without unnecessary steps? |

Each scenario has its own optimal investigation path and minimum step count. Scores reflect per-post adaptation, not difficulty-level averages.

### Baseline Scores (rule-based agent, no LLM)

| Task | Total | Action | Classification | Investigation | Efficiency |
|---|---|---|---|---|---|
| `easy_harassment` | **0.93** | 1.00 | 1.00 | 0.50 | 1.00 |
| `medium_ambiguous` | **1.00** | 1.00 | 1.00 | 1.00 | 1.00 |
| `hard_misinformation` | **0.50** | 0.00 | 1.00 | 1.00 | 1.00 |

The hard task exposes baseline limits: it correctly classifies but applies the wrong terminal action because severity-aware geo reasoning (EU DSA, IN viral amplification rules) requires language understanding beyond keyword matching.

---

## OpenEnv Python Client

Install the client directly from the Space:

```bash
pip install git+https://huggingface.co/spaces/ThejasRao/openenv-content-moderation
```

```python
from client import ModerationEnv, ModerationAction

# Async (recommended)
import asyncio

async def main():
    async with ModerationEnv(base_url="https://thejasrao-openenv-content-moderation.hf.space") as env:
        result = await env.reset(task_id="easy_harassment", seed=42)
        obs = result.observation

        print(obs.content)    # "I know where you live, Laura..."
        print(obs.reports)    # 15
        print(obs.geo)        # "EU"

        # Investigation step
        result = await env.step(ModerationAction(action_type="fetch_user_history"))
        print(obs.user_history)  # ["Prior violation: doxxing (2024-01)", ...]
        print(result.reward)     # 0.20

        # Classification
        result = await env.step(ModerationAction(
            action_type="mark_violation_type",
            parameters={"violation_type": "harassment"}
        ))

        # Terminal decision
        result = await env.step(ModerationAction(action_type="remove"))
        print(result.done)    # True
        print(result.reward)  # 0.95

asyncio.run(main())

# Sync wrapper
with ModerationEnv(base_url="https://thejasrao-openenv-content-moderation.hf.space").sync() as env:
    result = env.reset(task_id="easy_harassment", seed=42)
    result = env.step(ModerationAction(action_type="fetch_user_history"))
```

### Typed Observation Fields

```python
obs = result.observation  # ModerationObservation

obs.post_id        # str
obs.content        # str
obs.user_id        # str
obs.reports        # int
obs.engagement     # dict[str, int]  — {likes, shares, comments}
obs.geo            # str             — US | EU | IN | UK
obs.step           # int
obs.max_steps      # int
obs.done           # bool
obs.user_history   # list[str] | None
obs.thread_context # list[str] | None
obs.policy_clause  # str | None
obs.violation_type # str | None
```

---

## RL Training with TRL (GRPO)

This environment is designed to plug directly into TRL's GRPO rollout function. See the [OpenEnv Wordle GRPO notebook](https://github.com/huggingface/trl/blob/main/examples/notebooks/openenv_wordle_grpo.ipynb) for the full training pattern.

```python
from client import ModerationEnv, ModerationAction
from trl.experimental.openenv import generate_rollout_completions

env = ModerationEnv(base_url="https://thejasrao-openenv-content-moderation.hf.space")
sync_env = env.sync()
sync_env.connect()

def rollout_func(prompts, trainer=None):
    episode_prompt_ids, episode_completion_ids, episode_logprobs = [], [], []
    correctness_rewards, step_rewards = [], []

    for prompt_text in prompts:
        result = sync_env.reset(task_id="hard_misinformation", seed=777)
        obs = result.observation

        prompt_ids, completion_ids, logprobs, rewards = [], [], [], []

        for _turn in range(obs.max_steps):
            if result.done:
                break

            # Build prompt from observation
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": build_moderation_prompt(obs)},
            ]
            prompt_text = tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)

            # Generate completion via trainer's vLLM
            rollout = generate_rollout_completions(trainer, [prompt_text])[0]
            prompt_ids.extend(rollout["prompt_ids"])
            completion_ids.extend(rollout["completion_ids"])
            logprobs.extend(rollout["logprobs"])

            # Parse action from model output and step environment
            action = parse_action(rollout.get("text", ""))
            result = sync_env.step(ModerationAction(action_type=action))
            rewards.append(float(result.reward or 0.0))
            obs = result.observation

        episode_prompt_ids.append(prompt_ids)
        episode_completion_ids.append(completion_ids)
        episode_logprobs.append(logprobs)
        correctness_rewards.append(rewards[-1] if rewards else 0.0)
        step_rewards.append(sum(rewards))

    return {
        "prompt_ids":      episode_prompt_ids,
        "completion_ids":  episode_completion_ids,
        "logprobs":        episode_logprobs,
        "correct_reward":  correctness_rewards,
        "step_reward":     step_rewards,
    }
```

---

## Inference Script

`inference.py` runs the hybrid LLM agent (deterministic planner + 2 LLM calls per episode) against all 3 tasks and emits structured stdout logs consumed by the evaluator.

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `HF_TOKEN` | **Yes** | — | HuggingFace / API key |
| `API_BASE_URL` | Yes | `https://router.huggingface.co/v1` | OpenAI-compatible endpoint |
| `MODEL_NAME` | Yes | `meta-llama/Llama-3.3-70B-Instruct` | Model identifier |
| `OPENAI_API_KEY` | Optional | — | Direct OpenAI access |
| `GOOGLE_API_KEY` | Optional | — | Gemini agent via `/agent/run` |
| `LLM_PROVIDER` | Optional | `openai` | `openai` or `gemini` |

### Stdout Log Format

```
[START] task=<task_id> env=content-moderation model=<model_name>
[STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
[END]   success=<true|false> steps=<n> score=<0.000> rewards=<r1,r2,...>
```

**Example output:**
```
[START] task=easy_harassment env=content-moderation model=meta-llama/Llama-3.3-70B-Instruct
[STEP] step=1 action=fetch_user_history reward=0.20 done=false error=null
[STEP] step=2 action=mark_violation_type reward=0.50 done=false error=null
[STEP] step=3 action=remove reward=0.95 done=true error=null
[END] success=true steps=3 score=0.925 rewards=0.20,0.50,0.95
```

### Running Inference

```bash
export HF_TOKEN="hf_..."
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="meta-llama/Llama-3.3-70B-Instruct"

python inference.py
```

Target runtime: **< 5 minutes** on 2 vCPU / 8 GB RAM (LLM called at most twice per episode).

---

## Local Setup

```bash
# Clone
git clone https://github.com/thejasrao262003/OpenEnv-Content-Moderation-Benchmark.git
cd OpenEnv-Content-Moderation-Benchmark

# Install (with uv, recommended)
uv sync

# Or with pip
pip install -r requirements.txt

# Set environment variables
cp .env.example .env   # then fill in your keys

# Start the server
uvicorn api.app:app --reload --port 7860

# Health check
curl http://localhost:7860/health
# {"status":"healthy"}
```

### Quick API Test

```bash
# Reset (task_id passed as extra field)
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy_harassment", "seed": 42}'

# Step — action wrapped under "action" key (OpenEnv standard)
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "fetch_user_history", "parameters": {}}}'

# Classify
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "mark_violation_type", "parameters": {"violation_type": "harassment"}}}'

# Decide
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "remove", "parameters": {}}}'

# Grade
curl http://localhost:7860/grader

# Run baseline (no API key needed)
curl "http://localhost:7860/baseline?task_id=easy_harassment"
```

### Docker

```bash
docker build -t openenv-moderation .
docker run -p 7860:7860 \
  -e HF_TOKEN="hf_..." \
  -e API_BASE_URL="https://router.huggingface.co/v1" \
  -e MODEL_NAME="meta-llama/Llama-3.3-70B-Instruct" \
  openenv-moderation
```

---

## Project Structure

```
OpenENV_Hackathon/
├── api/
│   └── app.py              # FastAPI — all HTTP + WebSocket endpoints
├── env/
│   ├── data_generator.py   # 24 seed-deterministic post templates
│   ├── policy_engine.py    # Violation detection + geo jurisdiction overrides
│   ├── reward_engine.py    # Dense per-step reward computation
│   ├── state_manager.py    # Episode lifecycle + progressive context reveal
│   └── grader.py           # 4-component final score (0.0–1.0)
├── models/
│   └── schemas.py          # Pydantic types: Observation, Action, StepResult, etc.
├── data/
│   └── tasks.py            # 3 task definitions (easy / medium / hard)
├── baseline/
│   └── agent.py            # Rule-based baseline (no LLM — keyword heuristics)
├── agent/
│   ├── openai_agent.py     # OpenAI SDK LLM agent
│   ├── gemini_agent.py     # Gemini SDK LLM agent
│   └── prompts.py          # System + turn prompts
├── policies/               # Regional policy documents (US / EU / IN / UK)
├── tests/                  # Integration test suite
├── frontend/               # React dashboard UI
├── client.py               # ModerationEnv — OpenEnv WebSocket client
├── inference.py            # Evaluator inference script (root, mandatory)
├── openenv.yaml            # OpenEnv spec manifest
├── Dockerfile              # Container definition (port 7860 for HF Spaces)
├── pyproject.toml
└── requirements.txt
```

---

## Design Decisions

**Why content moderation as an RL environment?**
It is a real task at internet scale with measurable, non-trivial success criteria. The partial-observability structure (hidden context behind investigation actions) maps naturally to the MDP formulation. Unlike games or toy tasks, the correct action depends on multi-signal reasoning — engagement metrics, jurisdiction, user history, thread context — making it genuinely hard for both rule-based and LLM agents.

**Why 24 scenarios instead of 3?**
Three scenarios allow trivial memorisation. With 24 seed-deterministic templates across 4 geos and 3 difficulty levels, an agent must generalize rather than recall.

**Why per-template grading criteria?**
Difficulty-level averages produce identical scores for all posts at the same level. Each template has its own `required_investigation` path and `min_steps`, so scores genuinely reflect how well the agent adapted to the specific post and jurisdiction.

**Why a false-negative penalty of −2.0?**
Missing a credible death threat or viral health misinformation is far more harmful than an over-removal. The asymmetric penalty reflects real-world platform risk: false negatives cause direct harm; false positives cause user friction. This forces agents to develop conservative, evidence-based decision-making rather than defaulting to `allow`.

**Why a hybrid inference agent (deterministic planner + 2 LLM calls)?**
On 2 vCPU / 8 GB RAM with a 20-minute runtime budget, calling an LLM per step is too slow. The planner handles all investigation decisions deterministically; the LLM is called once to classify and once to decide. This stays under 5 minutes while still exercising language-based policy reasoning.
