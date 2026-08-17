"""
HUMAN VECTOR — minimal end-to-end session coordinator.

Purpose:
- expose one deterministic routing surface for the canonical session;
- automate only technical / AI execution surfaces;
- stop explicitly at every HUMAN cognitive gate;
- never impersonate the HUMAN actor;
- never bypass CORE ownership, integrity, provenance, or state guards.

V44 rule:
execution autonomy != cognitive authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CoordinatorAction(str, Enum):
    HUMAN_REQUIRED = "HUMAN_REQUIRED"
    AI_EXECUTION_REQUIRED = "AI_EXECUTION_REQUIRED"
    TECHNICAL_EXECUTION_REQUIRED = "TECHNICAL_EXECUTION_REQUIRED"
    COMPLETE = "COMPLETE"
    HALTED = "HALTED"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class CoordinatorDecision:
    state: str
    action: CoordinatorAction
    phase: str
    reason: str
    suggested_operation: str | None = None


_HUMAN_GATES: dict[str, tuple[str, str]] = {
    "DIRECTION_DRAFT": (
        "HUMAN_DIRECTION",
        "HUMAN must provide or revise the Human Direction.",
    ),
    "DIRECTION_REVISION_REQUIRED": (
        "HUMAN_DIRECTION",
        "HUMAN must revise the Human Direction.",
    ),
    "DIRECTION_CONFIRMATION_REQUIRED": (
        "HUMAN_DIRECTION",
        "HUMAN must review and confirm the exact Human Direction.",
    ),
    "HUMAN_RESPONSE_DRAFT": (
        "HUMAN_COGNITIVE_RESPONSE",
        "HUMAN must provide an independent cognitive response to V1.",
    ),
    "HUMAN_RESPONSE_CONFIRMATION_REQUIRED": (
        "HUMAN_COGNITIVE_RESPONSE",
        "HUMAN must confirm the exact cognitive response.",
    ),
    "HUMAN_RESPONSE_REQUIRED": (
        "HUMAN_COGNITIVE_RESPONSE",
        "HUMAN must provide an independent cognitive response to V1.",
    ),
    "CRITIC_CLARIFICATION_REQUIRED": (
        "CRITIC_CLARIFICATION",
        "HUMAN clarification is required before the Critic path continues.",
    ),
    "CONFLICT_SPACE_READY": (
        "HUMAN_CRITIC_SELECTION",
        "HUMAN must evaluate the conflict space.",
    ),
    "HUMAN_CRITIC_SELECTION": (
        "HUMAN_CRITIC_SELECTION",
        "HUMAN must explicitly select/reject/contest Critic findings.",
    ),
    "ITERATION_DECISION_REQUIRED": (
        "HUMAN_ITERATION_DECISION",
        "HUMAN must decide the next cognitive iteration.",
    ),
    "BRANCH_CREATION_REQUIRED": (
        "HUMAN_BRANCH_DECISION",
        "HUMAN must decide whether the cognitive path branches.",
    ),
    "MANUAL_TRANSFER_PREPARATION": (
        "MANUAL_COGNITIVE_TRANSFER",
        "HUMAN must explicitly prepare the cognitive transfer.",
    ),
    "MANUAL_TRANSFER_IN_PROGRESS": (
        "MANUAL_COGNITIVE_TRANSFER",
        "HUMAN must explicitly construct the cognitive transfer.",
    ),
    "TRANSFER_CONFIRMATION_REQUIRED": (
        "MANUAL_COGNITIVE_TRANSFER",
        "HUMAN must confirm the exact transfer package.",
    ),
    "MEMORY_RETRIEVAL_FAILED": (
        "ACTIVE_AGENTIC_MEMORY",
        "HUMAN must explicitly resolve the failed retrieval outcome.",
    ),
    "NO_RELEVANT_MEMORY": (
        "ACTIVE_AGENTIC_MEMORY",
        "HUMAN must explicitly confirm the no-relevant-memory resolution.",
    ),
    "MEMORY_REVIEW_REQUIRED": (
        "ACTIVE_AGENTIC_MEMORY",
        "HUMAN must review retrieved memory candidates.",
    ),
    "MEMORY_SELECTION_CONFIRMATION_REQUIRED": (
        "ACTIVE_AGENTIC_MEMORY",
        "HUMAN must confirm the exact memory selection.",
    ),
    "RECONSTRUCTION_PACKAGE_CONFIRMATION_REQUIRED": (
        "FINAL_RECONSTRUCTION_PACKAGE",
        "HUMAN must confirm the exact reconstruction package.",
    ),
    "HUMAN_VERIFICATION_REQUIRED": (
        "HUMAN_VERIFICATION",
        "HUMAN must compare the reconstructed candidate against V1 and the confirmed direction.",
    ),
    "VF_HUMAN_DECLARATION": (
        "VF",
        "Only HUMAN may declare the final version.",
    ),
    "FINAL_REPORT_READY": (
        "FINAL_REPORT_REVIEW",
        "HUMAN must review the current FinalReport before archive.",
    ),
}


_AI_STAGES: dict[str, tuple[str, str]] = {
    "BUILDER_V1_RUNNING": (
        "BUILDER_V1",
        "record_builder_v1_from_state",
    ),
    "CRITIC_RUNNING": (
        "CRITIC",
        "record_critic_review_from_state",
    ),
    "RECONSTRUCTION_RUNNING": (
        "BUILDER_VN",
        "record_builder_vn_from_state",
    ),
}


_TECHNICAL_STAGES: dict[str, str] = {
    "SESSION_CREATED": "DIRECTION_INITIALIZATION",
    "DIRECTION_VALIDATION_REQUIRED": "DIRECTION_VALIDATION",
    "DIRECTION_LOCKED": "BUILDER_V1_PREPARATION",
    "BRANCH_CREATED": "BRANCH_HANDOFF",
    "BUILDER_V1_PACKAGE_PREPARATION": "BUILDER_V1_PREPARATION",
    "BUILDER_V1_READY": "BUILDER_V1_PREPARATION",
    "V1_GENERATED": "HUMAN_RESPONSE_HANDOFF",
    "HUMAN_RESPONSE_CAPTURED": "HUMAN_RESPONSE_HANDOFF",
    "CRITIC_PACKAGE_PREPARATION": "CRITIC_PREPARATION",
    "CRITIC_READY": "CRITIC_PREPARATION",
    "CRITIC_REVIEW_GENERATED": "CRITIC_HANDOFF",
    "TRANSFER_PACKAGE_LOCKED": "TRANSFER_HANDOFF",
    "MEMORY_RETRIEVAL_READY": "MEMORY_RETRIEVAL",
    "MEMORY_RETRIEVAL_RUNNING": "MEMORY_RETRIEVAL",
    "MEMORY_SELECTION_LOCKED": "MEMORY_HANDOFF",
    "RECONSTRUCTION_PACKAGE_PREPARATION": "RECONSTRUCTION_PREPARATION",
    "RECONSTRUCTION_PACKAGE_READY": "RECONSTRUCTION_HANDOFF",
    "VN_GENERATED": "VERSION_COMPARISON",
    "VERSION_COMPARISON_READY": "VERSION_COMPARISON",
    "VERSION_COMPARISON_GENERATED": "HUMAN_VERIFICATION_HANDOFF",
    "VF_PRECHECK_REQUIRED": "VF_PRECHECK",
    "VF_DECLARED": "VF_INTEGRITY_AND_LOCK",
    "VF_LOCKING_IN_PROGRESS": "VF_TECHNICAL_LOCK",
    "VF_LOCKED": "FINAL_REPORT_GENERATION",
    "FINAL_REPORT_GENERATION": "FINAL_REPORT_GENERATION",
}


_COMPLETE_STATES = {
    "SESSION_ARCHIVED",
}


_HALTED_STATES = {
    "SESSION_CANCELLED",
}


def _state_name(orchestrator: Any) -> str:
    state = getattr(orchestrator, "state", None)

    if state is None:
        raise ValueError("Orchestrator has no current state.")

    name = getattr(state, "name", None)

    if isinstance(name, str) and name:
        return name

    value = getattr(state, "value", None)

    if isinstance(value, str) and value:
        return value

    text = str(state)

    if "." in text:
        return text.rsplit(".", 1)[-1]

    return text


def next_action(orchestrator: Any) -> CoordinatorDecision:
    """
    Return the next canonical execution category.

    This function never performs a HUMAN action.
    It only routes the current CORE state.
    """

    state = _state_name(orchestrator)

    if state in _COMPLETE_STATES:
        return CoordinatorDecision(
            state=state,
            action=CoordinatorAction.COMPLETE,
            phase="ARCHIVE",
            reason="The HUMAN VECTOR session is archived.",
        )

    if state in _HALTED_STATES:
        return CoordinatorDecision(
            state=state,
            action=CoordinatorAction.HALTED,
            phase="SESSION_TERMINATED",
            reason="The session is cancelled and must not continue automatically.",
        )

    if state in _HUMAN_GATES:
        phase, reason = _HUMAN_GATES[state]

        return CoordinatorDecision(
            state=state,
            action=CoordinatorAction.HUMAN_REQUIRED,
            phase=phase,
            reason=reason,
        )

    if state in _AI_STAGES:
        phase, operation = _AI_STAGES[state]

        return CoordinatorDecision(
            state=state,
            action=CoordinatorAction.AI_EXECUTION_REQUIRED,
            phase=phase,
            reason=(
                "A validated Google ADK / Gemini execution stage "
                "is ready; HUMAN authority is not delegated."
            ),
            suggested_operation=operation,
        )

    if state in _TECHNICAL_STAGES:
        phase = _TECHNICAL_STAGES[state]

        return CoordinatorDecision(
            state=state,
            action=CoordinatorAction.TECHNICAL_EXECUTION_REQUIRED,
            phase=phase,
            reason=(
                "Technical execution may continue only through "
                "existing CORE ownership and integrity guards."
            ),
        )

    return CoordinatorDecision(
        state=state,
        action=CoordinatorAction.UNSUPPORTED,
        phase="UNMAPPED",
        reason=(
            "No coordinator route is declared for this state. "
            "Do not guess or bypass CORE."
        ),
    )


def human_action_required(orchestrator: Any) -> bool:
    return next_action(orchestrator).action is CoordinatorAction.HUMAN_REQUIRED
