from __future__ import annotations

from google.adk.cli.fast_api import get_fast_api_app


app = get_fast_api_app(
    agents_dir="/app/hv-adk",
    web=False,
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
    from fastapi import HTTPException

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
    from fastapi import HTTPException

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
    from fastapi import HTTPException

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
    from fastapi import HTTPException

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
