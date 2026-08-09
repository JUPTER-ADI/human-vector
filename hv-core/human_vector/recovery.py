from .states import HumanVectorState as S


TECHNICAL_RECOVERY_TARGETS = {
    S.DIRECTION_VALIDATION_REQUIRED: S.DIRECTION_DRAFT,
    S.BUILDER_V1_PACKAGE_PREPARATION: S.DIRECTION_LOCKED,
    S.BUILDER_V1_READY: S.DIRECTION_LOCKED,
    S.CRITIC_PACKAGE_PREPARATION: S.HUMAN_RESPONSE_CAPTURED,
    S.CRITIC_READY: S.HUMAN_RESPONSE_CAPTURED,
    S.MEMORY_RETRIEVAL_READY: S.TRANSFER_PACKAGE_LOCKED,
    S.RECONSTRUCTION_PACKAGE_PREPARATION: S.MEMORY_SELECTION_LOCKED,
    S.RECONSTRUCTION_PACKAGE_CONFIRMATION_REQUIRED: S.MEMORY_SELECTION_LOCKED,
    S.RECONSTRUCTION_PACKAGE_READY: S.RECONSTRUCTION_PACKAGE_READY,
}

AI_RETRY_TARGETS = {
    S.BUILDER_V1_RUNNING: S.BUILDER_V1_READY,
    S.CRITIC_RUNNING: S.CRITIC_READY,
    S.RECONSTRUCTION_RUNNING: S.RECONSTRUCTION_PACKAGE_READY,
}

MEMORY_RETRY_TARGETS = {
    S.MEMORY_RETRIEVAL_RUNNING: S.MEMORY_RETRIEVAL_READY,
}


def resolve_recovery_target(failure_state: S, failed_from: S) -> S:
    if failure_state is S.TECHNICAL_ERROR:
        table = TECHNICAL_RECOVERY_TARGETS
    elif failure_state is S.AI_OPERATION_FAILED:
        table = AI_RETRY_TARGETS
    elif failure_state is S.MEMORY_RETRIEVAL_FAILED:
        table = MEMORY_RETRY_TARGETS
    else:
        raise ValueError(f"Unsupported failure state: {failure_state.value}")

    try:
        return table[failed_from]
    except KeyError as exc:
        raise ValueError(
            f"No authorized recovery target for "
            f"{failed_from.value} -> {failure_state.value}"
        ) from exc
