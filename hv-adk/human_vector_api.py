from __future__ import annotations

from google.adk.runners import InMemoryRunner
from google.genai import types
from human_vector_agent.agent import builder_v1_agent

from fastapi import HTTPException
from google.adk.cli.fast_api import get_fast_api_app


app = get_fast_api_app(
    agents_dir="/app/hv-adk",
    web=False,
)


from human_vector_agent.hv_core_bridge import (
    bind_orchestrator,
    advance_to_builder_v1_running,
    prepare_builder_v1_direction,
)

@app.get("/human-vector/health")
def human_vector_health() -> dict[str, object]:
    return {
        "ok": True,
        "service": "human-vector",
        "access_layer": True,
    }


from pydantic import BaseModel

from human_vector.session_controller import SessionController
from human_vector.orchestrator import S, Actor


session_controller = SessionController()


class CreateSessionRequest(BaseModel):
    user_id: str
    actor_id: str
    actor_role: str = "HUMAN"


@app.post("/human-vector/sessions")
def create_human_vector_session(
    request: CreateSessionRequest,
) -> dict[str, object]:
    context = session_controller.create_session(
        user_id=request.user_id,
        actor_id=request.actor_id,
        actor_role=request.actor_role,
    )

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "actor_id": context.actor_id,
        "actor_role": context.actor_role,
        "state": context.orchestrator.state.value,
        "revision": context.orchestrator.revision,
    }



class PersistSessionRequest(BaseModel):
    user_id: str
    path: str


@app.post("/human-vector/sessions/{session_id}/persist")
def persist_human_vector_session(
    session_id: str,
    request: PersistSessionRequest,
) -> dict[str, object]:

    try:
        session_controller.require_session_for_user(
            session_id=session_id,
            user_id=request.user_id,
        )
        session_controller.save_session(
            session_id=session_id,
            path=request.path,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": session_id,
        "persisted": True,
        "path": request.path,
    }



class LoadSessionRequest(BaseModel):
    path: str


@app.post("/human-vector/sessions/load")
def load_human_vector_session(
    request: LoadSessionRequest,
) -> dict[str, object]:

    try:
        context = session_controller.load_session(request.path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "actor_id": context.actor_id,
        "actor_role": context.actor_role,
        "state": context.orchestrator.state.value,
        "revision": context.orchestrator.revision,
        "loaded": True,
    }


@app.get("/human-vector/sessions/{session_id}")
def get_human_vector_session(
    session_id: str,
    user_id: str,
) -> dict[str, object]:

    try:
        context = session_controller.require_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "actor_id": context.actor_id,
        "actor_role": context.actor_role,
        "state": context.orchestrator.state.value,
        "revision": context.orchestrator.revision,
    }


@app.delete("/human-vector/sessions/{session_id}")
def close_human_vector_session(
    session_id: str,
    user_id: str,
) -> dict[str, object]:

    try:
        session_controller.close_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": session_id,
        "closed": True,
    }

@app.post("/human-vector/sessions/{session_id}/direction")
async def record_human_vector_direction(
    session_id: str,
    payload: dict[str, object],
):
    user_id = str(payload.get("user_id", "")).strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="USER_ID_REQUIRED")

    try:
        context = session_controller.require_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    orchestrator = context.orchestrator

    from human_vector.orchestrator import Actor
    from human_vector.states import HumanVectorState as S

    if orchestrator.state is not S.DIRECTION_DRAFT:
        orchestrator.transition(S.DIRECTION_DRAFT, Actor.ORCHESTRATOR)

    direction = orchestrator.record_human_direction_draft(
        objective=str(payload.get("objective", "")).strip(),
        context=str(payload.get("context", "")).strip(),
        criteria=str(payload.get("criteria", "")).strip(),
        limits=str(payload.get("limits", "")).strip(),
        actor=Actor.HUMAN,
    )

    return {
        "ok": True,
        "session_id": session_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "direction_type": type(direction).__name__,
    }



@app.post("/human-vector/sessions/{session_id}/direction/confirm")
def confirm_human_vector_direction(
    session_id: str,
    payload: dict[str, object],
) -> dict[str, object]:
    user_id = str(payload.get("user_id", "")).strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    try:
        context = session_controller.require_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    orchestrator = context.orchestrator

    try:
        if orchestrator.state is S.DIRECTION_DRAFT:
            orchestrator.transition(
                S.DIRECTION_VALIDATION_REQUIRED,
                Actor.ORCHESTRATOR,
            )

        if orchestrator.state is S.DIRECTION_VALIDATION_REQUIRED:
            orchestrator.transition(
                S.DIRECTION_CONFIRMATION_REQUIRED,
                Actor.ORCHESTRATOR,
            )

        direction = orchestrator.confirm_human_direction(
            actor=Actor.HUMAN,
        )
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "direction_status": direction.status,
        "final_authority": "HUMAN",
    }



@app.post("/human-vector/sessions/{session_id}/builder-v1")
async def run_human_vector_builder_v1(session_id: str, payload: dict):
    try:
        context = session_controller.require_session(session_id)
        session_controller.require_session_for_user(session_id=session_id, user_id=payload["user_id"])
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    orchestrator = context.orchestrator

    try:
        bind_orchestrator(orchestrator)
        advance_result = advance_to_builder_v1_running()
        if not advance_result.get("ok"):
            raise RuntimeError(
                advance_result.get("reason", "Builder V1 advance failed")
            )
        if orchestrator.state is not S.BUILDER_V1_RUNNING:
            raise RuntimeError(
                f"Builder V1 advance failed: state={orchestrator.state.value}"
            )
        class _BuilderV1ApiToolContext:
            def __init__(self):
                self.state = {}

        builder_tool_context = _BuilderV1ApiToolContext()
        builder_input = prepare_builder_v1_direction(builder_tool_context)

        runner = InMemoryRunner(agent=builder_v1_agent)
        adk_session = await runner.session_service.create_session(
            app_name=runner.app_name,
            user_id=context.user_id,
            state={
                "hv_builder_direction_package": builder_tool_context.state[
                    "hv_builder_direction_package"
                ]
            },
        )
        message = types.Content(
            role="user",
            parts=[types.Part(text=builder_tool_context.state["hv_builder_direction_package"])],
        )
        async for _event in runner.run_async(
            user_id=context.user_id,
            session_id=adk_session.id,
            new_message=message,
        ):
            pass

        builder_output = await runner.session_service.get_session(
            app_name=runner.app_name,
            user_id=context.user_id,
            session_id=adk_session.id,
        )
        builder_output = builder_output.state.get("hv_builder_v1_output")
        if not builder_output:
            raise RuntimeError("Builder V1 produced no exact ADK session output")
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "builder_v1_ready": True,
        "builder_input": builder_input,
        "required_next_operation": "ADK_BUILDER_V1",
        "human_authority_preserved": True,
    }



@app.post("/human-vector/sessions/{session_id}/conflict-space")
def build_human_vector_conflict_space(
    session_id: str,
    user_id: str,
) -> dict[str, object]:
    from dataclasses import asdict

    try:
        context = session_controller.require_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    orchestrator = context.orchestrator

    try:
        space = orchestrator.build_conflict_space(actor=Actor.SYSTEM)
        orchestrator.open_human_critic_selection(actor=Actor.ORCHESTRATOR)
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "conflict_space": asdict(space),
        "required_next_operation": "HUMAN_CRITIC_SELECTION",
        "final_authority": "HUMAN",
    }


class HumanCriticSelectionRequest(BaseModel):
    decisions: list[dict[str, str]]


@app.post("/human-vector/sessions/{session_id}/critic-selection")
def record_human_vector_critic_selection(
    session_id: str,
    user_id: str,
    payload: HumanCriticSelectionRequest,
) -> dict[str, object]:
    from dataclasses import asdict

    try:
        context = session_controller.require_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    orchestrator = context.orchestrator

    try:
        selection = orchestrator.record_human_critic_selection(
            actor=Actor.HUMAN,
            decisions=payload.decisions,
        )
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "human_critic_selection": asdict(selection),
        "final_authority": "HUMAN",
    }


@app.get("/human-vector/sessions/{session_id}/results")
def get_human_vector_session_results(
    session_id: str,
    user_id: str,
) -> dict[str, object]:
    from dataclasses import asdict, is_dataclass

    try:
        context = session_controller.require_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    orchestrator = context.orchestrator

    def serialize_artifact(value: object) -> object:
        if value is None:
            return None
        if is_dataclass(value):
            return asdict(value)
        return value

    baseline = getattr(
        orchestrator,
        "human_capability_baseline_artifact",
        None,
    )
    assessment = getattr(
        orchestrator,
        "human_capability_assessment_artifact",
        None,
    )
    gain = getattr(
        orchestrator,
        "human_capability_gain_artifact",
        None,
    )

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "human_capability": {
            "baseline": serialize_artifact(baseline),
            "assessment": serialize_artifact(assessment),
            "gain_evidence": serialize_artifact(gain),
            "baseline_available": baseline is not None,
            "assessment_available": assessment is not None,
            "gain_evidence_available": gain is not None,
        },
        "final_report_available": getattr(
            orchestrator,
            "final_report",
            None,
        ) is not None,
    }

