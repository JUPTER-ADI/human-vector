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
