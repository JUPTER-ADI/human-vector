from uuid import UUID, uuid4
from google.adk.tools import ToolContext
from human_vector.orchestrator import Actor, SystemOrchestrator, TransitionRejected
from human_vector.states import HumanVectorState as S

_orchestrator = SystemOrchestrator()


def get_human_vector_core_status() -> dict:
    """Return the current HUMAN VECTOR core state without changing it."""
    return {
        "state": _orchestrator.state.value,
        "revision": _orchestrator.revision,
        "history_length": len(_orchestrator.history),
        "final_authority": "HUMAN",
    }


def start_direction_draft() -> dict:
    """Enter the direction-draft stage without setting or approving human direction."""
    if _orchestrator.state != S.SESSION_CREATED:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": "Direction draft can only start from SESSION_CREATED.",
            "final_authority": "HUMAN",
        }

    try:
        record = _orchestrator.transition(
            S.DIRECTION_DRAFT,
            Actor.ORCHESTRATOR,
            "Start HUMAN VECTOR direction draft",
        )
    except TransitionRejected as exc:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": str(exc),
            "final_authority": "HUMAN",
        }

    return {
        "ok": True,
        "state": _orchestrator.state.value,
        "revision": _orchestrator.revision,
        "history_length": len(_orchestrator.history),
        "actor": record.actor.value,
        "final_authority": "HUMAN",
    }

def advance_direction_to_human_confirmation() -> dict:
    """Advance only orchestrator-owned direction steps and stop at the human confirmation gate."""
    allowed_states = {
        S.DIRECTION_DRAFT,
        S.DIRECTION_VALIDATION_REQUIRED,
    }

    if _orchestrator.state not in allowed_states:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": "Direction can only advance from DIRECTION_DRAFT or DIRECTION_VALIDATION_REQUIRED.",
            "final_authority": "HUMAN",
        }

    try:
        if _orchestrator.state == S.DIRECTION_DRAFT:
            _orchestrator.transition(
                S.DIRECTION_VALIDATION_REQUIRED,
                Actor.ORCHESTRATOR,
                "Validate HUMAN VECTOR direction draft",
            )

        if _orchestrator.state == S.DIRECTION_VALIDATION_REQUIRED:
            _orchestrator.transition(
                S.DIRECTION_CONFIRMATION_REQUIRED,
                Actor.ORCHESTRATOR,
                "Prepare direction for explicit human confirmation",
            )

    except TransitionRejected as exc:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": str(exc),
            "final_authority": "HUMAN",
        }

    return {
        "ok": True,
        "state": _orchestrator.state.value,
        "revision": _orchestrator.revision,
        "history_length": len(_orchestrator.history),
        "actor": _orchestrator.history[-1].actor.value,
        "human_confirmation_required": True,
        "final_authority": "HUMAN",
    }

def advance_to_builder_v1_running() -> dict:
    """Advance only orchestrator-owned Builder V1 setup steps and stop before Builder AI generates V1."""
    allowed_states = {
        S.DIRECTION_LOCKED,
        S.BUILDER_V1_PACKAGE_PREPARATION,
        S.BUILDER_V1_READY,
    }

    if _orchestrator.state not in allowed_states:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": (
                "Builder V1 setup can only advance from DIRECTION_LOCKED, "
                "BUILDER_V1_PACKAGE_PREPARATION, or BUILDER_V1_READY."
            ),
            "final_authority": "HUMAN",
        }

    try:
        if _orchestrator.state == S.DIRECTION_LOCKED:
            _orchestrator.transition(
                S.BUILDER_V1_PACKAGE_PREPARATION,
                Actor.ORCHESTRATOR,
                "Prepare Builder V1 package",
            )

        if _orchestrator.state == S.BUILDER_V1_PACKAGE_PREPARATION:
            _orchestrator.transition(
                S.BUILDER_V1_READY,
                Actor.ORCHESTRATOR,
                "Builder V1 package ready",
            )

        if _orchestrator.state == S.BUILDER_V1_READY:
            _orchestrator.transition(
                S.BUILDER_V1_RUNNING,
                Actor.ORCHESTRATOR,
                "Start Builder V1 execution",
            )

    except TransitionRejected as exc:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": str(exc),
            "final_authority": "HUMAN",
        }

    return {
        "ok": True,
        "state": _orchestrator.state.value,
        "revision": _orchestrator.revision,
        "history_length": len(_orchestrator.history),
        "actor": _orchestrator.history[-1].actor.value,
        "builder_ai_required": True,
        "final_authority": "HUMAN",
    }

def record_builder_v1(v1_content: str, tool_context: ToolContext) -> dict:
    """Record the exact V1 produced by Builder AI and stop at the HUMAN response gate.

    Args:
        v1_content: The exact Builder AI V1 content. It must not be rewritten
            or summarized by the orchestrator before being recorded.
    """
    content = v1_content.strip()

    if _orchestrator.state is not S.BUILDER_V1_RUNNING:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": (
                "Builder V1 can only be recorded from "
                "BUILDER_V1_RUNNING."
            ),
            "final_authority": "HUMAN",
        }

    if not content:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": "Builder V1 content must be non-empty.",
            "final_authority": "HUMAN",
        }

    if any(
        version.version_label == "V1"
        for version in _orchestrator.result_versions.values()
    ):
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": "V1 already exists for this core session.",
            "final_authority": "HUMAN",
        }

    core_session_id = tool_context.state.get("hv_core_session_id")
    if not core_session_id:
        core_session_id = str(uuid4())
        tool_context.state["hv_core_session_id"] = core_session_id

    try:
        core_session_id = str(UUID(str(core_session_id).strip()))
    except ValueError:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": "Builder V1 requires a valid session UUID.",
            "final_authority": "HUMAN",
        }

    tool_context.state["hv_core_session_id"] = core_session_id

    if (
        _orchestrator.session_id is not None
        and _orchestrator.session_id != core_session_id
    ):
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": (
                "ADK session/core session mismatch. "
                "The current in-memory bridge is already bound "
                "to another HUMAN VECTOR session."
            ),
            "final_authority": "HUMAN",
        }

    try:
        _orchestrator.transition(
            S.V1_GENERATED,
            Actor.BUILDER_AI,
            "Builder AI generated V1.",
        )

        result = _orchestrator.record_result_version(
            session_id=core_session_id,
            version_label="V1",
            content=v1_content,
            actor=Actor.BUILDER_AI,
        )

        _orchestrator.transition(
            S.HUMAN_RESPONSE_REQUIRED,
            Actor.ORCHESTRATOR,
            "V1 recorded; HUMAN cognitive response is required.",
        )

    except TransitionRejected as exc:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": str(exc),
            "final_authority": "HUMAN",
        }

    return {
        "ok": True,
        "state": _orchestrator.state.value,
        "revision": _orchestrator.revision,
        "session_id": result.session_id,
        "version_id": result.version_id,
        "version_label": result.version_label,
        "content_hash": result.content_hash,
        "builder_actor": Actor.BUILDER_AI.value,
        "human_response_required": True,
        "final_authority": "HUMAN",
    }
