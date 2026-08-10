from human_vector.orchestrator import SystemOrchestrator

_orchestrator = SystemOrchestrator()


def get_human_vector_core_status() -> dict:
    """Return the current HUMAN VECTOR core state without changing it."""
    return {
        "state": _orchestrator.state.value,
        "revision": _orchestrator.revision,
        "history_length": len(_orchestrator.history),
        "final_authority": "HUMAN",
    }
