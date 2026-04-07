"""
OpenENV Moderation Environment — FastAPI application.

Standard OpenEnv endpoints:
  WS   /ws         — persistent WebSocket session (primary client interface)
  GET  /health     — liveness check
  POST /reset      — start a new episode
  POST /step       — take an action
  GET  /state      — current observation / state
  GET  /docs       — OpenAPI documentation (auto-generated)

Custom endpoints:
  GET  /tasks      — available tasks
  GET  /grader     — final episode score
  GET  /baseline   — run rule-based baseline agent and return its score
  POST /agent/run  — run selected LLM agent on a full episode

Web interface (when ENABLE_WEB_INTERFACE=true):
  GET  /web        — Gradio playground UI
"""
from __future__ import annotations

import json
import logging
import os

from dotenv import load_dotenv
load_dotenv()  # loads .env from project root before anything else

from fastapi import FastAPI, HTTPException, Body, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from openenv.core.env_server.types import (
    HealthResponse,
    HealthStatus,
    ResetRequest as OEResetRequest,
    ResetResponse,
    StepRequest,
    StepResponse,
    WSObservationResponse,
    WSStateResponse,
    WSErrorResponse,
    WSErrorCode,
)

from .tasks import TASKS
from .grader import Grader
from .state_manager import StateManager
from models import (
    Action,
    BaselineResult,
    EpisodeScore,
    ResetRequest,
    TaskConfig,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OpenENV — Content Moderation Environment",
    description=(
        "A multi-step RL environment for AI content moderation agents. "
        "Agents receive partial observations and must investigate context, "
        "classify violations, and make final moderation decisions."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Open for HF Spaces + local dev
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single shared state manager (single-threaded MVP)
_state_manager = StateManager()
_grader = Grader()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status=HealthStatus.HEALTHY)


@app.get("/tasks")
def list_tasks() -> dict[str, TaskConfig]:
    return TASKS


@app.post("/reset", response_model=ResetResponse)
def reset(request: OEResetRequest | None = Body(default=None)) -> ResetResponse:
    # task_id passed as extra field; fall back to episode_id or default
    extra = (request.model_extra or {}) if request else {}
    task_id = extra.get("task_id") or (request.episode_id if request else None) or "easy_harassment"
    seed = (request.seed if request else None) or 42

    if task_id not in TASKS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown task_id '{task_id}'. Available: {list(TASKS.keys())}",
        )

    task = TASKS[task_id]
    task = task.model_copy(update={"seed": seed})

    obs = _state_manager.reset(task)
    return ResetResponse(observation=obs.model_dump(), reward=None, done=obs.done)


@app.post("/step", response_model=StepResponse)
def step(request: StepRequest) -> StepResponse:
    if not _state_manager.has_active_episode():
        raise HTTPException(status_code=400, detail="No active episode. Call /reset first.")

    try:
        action = Action(**request.action)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    try:
        result = _state_manager.step(action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    logger.info(
        "Step %d: action=%s reward=%.3f done=%s",
        result.observation.step,
        action.action_type.value,
        result.reward,
        result.done,
    )
    return StepResponse(
        observation=result.observation.model_dump(),
        reward=result.reward,
        done=result.done,
    )


@app.get("/state")
def get_state() -> dict:
    if not _state_manager.has_active_episode():
        raise HTTPException(status_code=400, detail="No active episode. Call /reset first.")
    return _state_manager.get_state().model_dump()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            try:
                raw = await websocket.receive_text()
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(
                    WSErrorResponse(data={"message": "Invalid JSON", "code": WSErrorCode.INVALID_JSON}).model_dump_json()
                )
                continue

            msg_type = data.get("type")

            if msg_type == "reset":
                reset_data = data.get("data", {})
                task_id = reset_data.get("task_id") or reset_data.get("episode_id") or "easy_harassment"
                seed = reset_data.get("seed") or 42

                if task_id not in TASKS:
                    await websocket.send_text(
                        WSErrorResponse(data={"message": f"Unknown task_id '{task_id}'", "code": WSErrorCode.VALIDATION_ERROR}).model_dump_json()
                    )
                    continue

                task = TASKS[task_id].model_copy(update={"seed": seed})
                obs = _state_manager.reset(task)
                await websocket.send_text(
                    WSObservationResponse(data={"observation": obs.model_dump(), "reward": None, "done": obs.done}).model_dump_json()
                )

            elif msg_type == "step":
                if not _state_manager.has_active_episode():
                    await websocket.send_text(
                        WSErrorResponse(data={"message": "No active episode. Send reset first.", "code": WSErrorCode.SESSION_ERROR}).model_dump_json()
                    )
                    continue

                action_data = data.get("data", {})
                try:
                    action = Action(**action_data)
                except Exception as exc:
                    await websocket.send_text(
                        WSErrorResponse(data={"message": str(exc), "code": WSErrorCode.VALIDATION_ERROR}).model_dump_json()
                    )
                    continue

                try:
                    result = _state_manager.step(action)
                except ValueError as exc:
                    await websocket.send_text(
                        WSErrorResponse(data={"message": str(exc), "code": WSErrorCode.EXECUTION_ERROR}).model_dump_json()
                    )
                    continue

                await websocket.send_text(
                    WSObservationResponse(data={"observation": result.observation.model_dump(), "reward": result.reward, "done": result.done}).model_dump_json()
                )

            elif msg_type == "state":
                if not _state_manager.has_active_episode():
                    await websocket.send_text(
                        WSErrorResponse(data={"message": "No active episode.", "code": WSErrorCode.SESSION_ERROR}).model_dump_json()
                    )
                    continue
                obs = _state_manager.get_state()
                await websocket.send_text(
                    WSStateResponse(data=obs.model_dump()).model_dump_json()
                )

            elif msg_type == "close":
                break

            else:
                await websocket.send_text(
                    WSErrorResponse(data={"message": f"Unknown message type: {msg_type!r}", "code": WSErrorCode.UNKNOWN_TYPE}).model_dump_json()
                )

    except WebSocketDisconnect:
        pass


@app.get("/grader", response_model=EpisodeScore)
def grade() -> EpisodeScore:
    if not _state_manager.has_active_episode():
        raise HTTPException(status_code=400, detail="No active episode. Call /reset first.")

    episode = _state_manager.get_episode_state()
    if not episode.observation.done:
        raise HTTPException(
            status_code=400,
            detail="Episode is not finished yet. Complete the episode before grading.",
        )

    score = _grader.score(episode)
    logger.info("Graded episode: total=%.4f", score.total)
    return score


@app.get("/baseline", response_model=BaselineResult)
def baseline(task_id: str = "easy_harassment", seed: int | None = None) -> BaselineResult:
    """Run the built-in rule-based baseline agent and return its score."""
    from baseline.agent import BaselineAgent

    if task_id not in TASKS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown task_id '{task_id}'. Available: {list(TASKS.keys())}",
        )

    task = TASKS[task_id]
    if seed is not None:
        task = task.model_copy(update={"seed": seed})

    agent = BaselineAgent(state_manager=_state_manager, grader=_grader)
    result = agent.run(task)
    return result


@app.post("/agent/run", response_model=BaselineResult)
def agent_run(request: ResetRequest) -> BaselineResult:
    """
    Run the selected LLM agent (OpenAI or Gemini) on a full episode and return the graded result.

    Requires OPENAI_API_KEY, or GOOGLE_API_KEY/GEMINI_API_KEY depending on LLM_PROVIDER.
    """
    import os

    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if request.task_id not in TASKS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown task_id '{request.task_id}'. Available: {list(TASKS.keys())}",
        )

    task = TASKS[request.task_id]
    if request.seed is not None:
        task = task.model_copy(update={"seed": request.seed})

    try:
        if provider == "gemini":
            from agent.gemini_agent import GeminiAgent
            agent = GeminiAgent(state_manager=_state_manager, grader=_grader)
        else:
            from agent.openai_agent import OpenAIAgent
            agent = OpenAIAgent(state_manager=_state_manager, grader=_grader)
    except EnvironmentError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    result = agent.run(task)
    logger.info(
        "%s agent finished: task=%s total=%.4f", provider.capitalize(), task.task_id, result.score.total
    )
    return result


# ---------------------------------------------------------------------------
# Web interface (Gradio) — mounted only when ENABLE_WEB_INTERFACE is set
# ---------------------------------------------------------------------------

def _build_web_interface():
    """Build and mount a Gradio playground UI at /web."""
    import gradio as gr
    from fastapi.responses import RedirectResponse
    from models import ActionType

    task_choices = list(TASKS.keys())
    action_choices = [a.value for a in ActionType]

    def _fmt_obs(obs_dict: dict) -> str:
        lines = []
        for k, v in obs_dict.items():
            if v is not None:
                lines.append(f"**{k}:** {v}")
        return "\n\n".join(lines) if lines else "*No observation yet*"

    def do_reset(task_id: str) -> tuple[str, str, str]:
        try:
            if task_id not in TASKS:
                return "", "", f"Unknown task_id: {task_id}"
            task = TASKS[task_id].model_copy(update={"seed": 42})
            obs = _state_manager.reset(task)
            obs_dict = obs.model_dump()
            return _fmt_obs(obs_dict), json.dumps(obs_dict, indent=2, default=str), "Reset successful."
        except Exception as exc:
            return "", "", f"Error: {exc}"

    def do_step(action_type: str, params_json: str) -> tuple[str, str, str]:
        if not _state_manager.has_active_episode():
            return "", "", "No active episode. Click Reset first."
        try:
            params = json.loads(params_json) if params_json.strip() else {}
        except json.JSONDecodeError as exc:
            return "", "", f"Invalid JSON params: {exc}"
        try:
            action = Action(action_type=ActionType(action_type), parameters=params)
            result = _state_manager.step(action)
            obs_dict = result.observation.model_dump()
            status = f"Reward: {result.reward:.3f} | Done: {result.done}"
            return _fmt_obs(obs_dict), json.dumps(obs_dict, indent=2, default=str), status
        except Exception as exc:
            return "", "", f"Error: {exc}"

    def do_state() -> str:
        if not _state_manager.has_active_episode():
            return "No active episode."
        try:
            return json.dumps(_state_manager.get_state().model_dump(), indent=2, default=str)
        except Exception as exc:
            return f"Error: {exc}"

    with gr.Blocks(title="OpenENV — Content Moderation Playground") as demo:
        gr.Markdown("# OpenENV Content Moderation Playground")
        gr.Markdown(
            "Interact with the content moderation environment. "
            "Select a task, click **Reset**, then send **Step** actions."
        )
        with gr.Row():
            with gr.Column(scale=2):
                obs_display = gr.Markdown(value="*Click Reset to start an episode.*")
            with gr.Column(scale=1):
                raw_json = gr.Code(label="Raw JSON", language="json", interactive=False)

        with gr.Row():
            task_dd = gr.Dropdown(
                choices=task_choices,
                value=task_choices[0] if task_choices else None,
                label="Task",
            )
            reset_btn = gr.Button("Reset", variant="secondary")

        with gr.Row():
            action_dd = gr.Dropdown(
                choices=action_choices,
                value=action_choices[0] if action_choices else None,
                label="Action type",
            )
            params_tb = gr.Textbox(
                label="Parameters (JSON)",
                placeholder='{"clause_id": "harassment_1"}',
                value="{}",
            )
            step_btn = gr.Button("Step", variant="primary")

        status_tb = gr.Textbox(label="Status", interactive=False)
        state_btn = gr.Button("Get state", variant="secondary")

        reset_btn.click(fn=do_reset, inputs=[task_dd], outputs=[obs_display, raw_json, status_tb])
        step_btn.click(fn=do_step, inputs=[action_dd, params_tb], outputs=[obs_display, raw_json, status_tb])
        state_btn.click(fn=do_state, outputs=[raw_json])

    return demo


if os.getenv("ENABLE_WEB_INTERFACE", "").lower() in ("true", "1", "yes"):
    try:
        import gradio as gr
        from fastapi.responses import RedirectResponse

        _gradio_demo = _build_web_interface()

        @app.get("/web", include_in_schema=False)
        async def _web_redirect():
            return RedirectResponse(url="/web/")

        app = gr.mount_gradio_app(app, _gradio_demo, path="/web")
        logger.info("Web interface mounted at /web")
    except ImportError:
        logger.warning("gradio not installed — ENABLE_WEB_INTERFACE=true has no effect")


def main() -> None:
    import uvicorn
    uvicorn.run(
        "server.app:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )
