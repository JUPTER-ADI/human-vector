from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum

from .states import HumanVectorState as S
from .transitions import (
    DYNAMIC_TRANSITION_STATES,
    is_static_transition_allowed,
)
from .recovery import resolve_recovery_target


class Actor(str, Enum):
    HUMAN = "HUMAN"
    BUILDER_AI = "BUILDER_AI"
    CRITIC_AI = "CRITIC_AI"
    MEMORY = "MEMORY"
    ORCHESTRATOR = "ORCHESTRATOR"
    SYSTEM = "SYSTEM"


class TransitionRejected(ValueError):
    pass


RETRIEVAL_CANDIDATES_FOUND = "CANDIDATES_FOUND"
RETRIEVAL_NO_RELEVANT_CANDIDATE_FOUND = "NO_RELEVANT_CANDIDATE_FOUND"
RETRIEVAL_TECHNICAL_ERROR = "TECHNICAL_ERROR"

MEMORY_RESOLUTION_NO_RELEVANT_MEMORY = "NO_RELEVANT_MEMORY"

NEGATIVE_REASON_NO_RELEVANT_CANDIDATE_FOUND = "NO_RELEVANT_CANDIDATE_FOUND"
NEGATIVE_REASON_ZERO_ITEMS_AUTHORIZED_AFTER_HUMAN_REVIEW = (
    "ZERO_ITEMS_AUTHORIZED_AFTER_HUMAN_REVIEW"
)


HUMAN_AUTHORITY_TRANSITIONS = frozenset({
    (S.DIRECTION_CONFIRMATION_REQUIRED, S.DIRECTION_LOCKED),

    (
        S.HUMAN_RESPONSE_CONFIRMATION_REQUIRED,
        S.HUMAN_RESPONSE_CAPTURED,
    ),

    (
        S.HUMAN_CRITIC_SELECTION,
        S.CRITIC_CLARIFICATION_REQUIRED,
    ),
    (
        S.CRITIC_CLARIFICATION_REQUIRED,
        S.HUMAN_CRITIC_SELECTION,
    ),
    (
        S.MANUAL_TRANSFER_PREPARATION,
        S.MANUAL_TRANSFER_IN_PROGRESS,
    ),
    (
        S.MANUAL_TRANSFER_IN_PROGRESS,
        S.TRANSFER_CONFIRMATION_REQUIRED,
    ),
    (
        S.MANUAL_TRANSFER_IN_PROGRESS,
        S.HUMAN_CRITIC_SELECTION,
    ),
    (
        S.TRANSFER_CONFIRMATION_REQUIRED,
        S.MANUAL_TRANSFER_IN_PROGRESS,
    ),
    (
        S.HUMAN_CRITIC_SELECTION,
        S.MANUAL_TRANSFER_PREPARATION,
    ),


    (
        S.MEMORY_RETRIEVAL_RUNNING,
        S.NO_RELEVANT_MEMORY,
    ),
    (
        S.MEMORY_REVIEW_REQUIRED,
        S.MEMORY_SELECTION_CONFIRMATION_REQUIRED,
    ),
    (
        S.MEMORY_REVIEW_REQUIRED,
        S.NO_RELEVANT_MEMORY,
    ),
    (
        S.MEMORY_REVIEW_REQUIRED,
        S.MEMORY_RETRIEVAL_READY,
    ),
    (
        S.MEMORY_SELECTION_CONFIRMATION_REQUIRED,
        S.MEMORY_REVIEW_REQUIRED,
    ),

    (
        S.RECONSTRUCTION_PACKAGE_CONFIRMATION_REQUIRED,
        S.RECONSTRUCTION_PACKAGE_PREPARATION,
    ),
    (
        S.RECONSTRUCTION_PACKAGE_CONFIRMATION_REQUIRED,
        S.MANUAL_TRANSFER_PREPARATION,
    ),
    (
        S.RECONSTRUCTION_PACKAGE_CONFIRMATION_REQUIRED,
        S.MEMORY_REVIEW_REQUIRED,
    ),

    (
        S.HUMAN_VERIFICATION_REQUIRED,
        S.VF_PRECHECK_REQUIRED,
    ),
})


AGENT_OWNED_TRANSITIONS = {
    (S.DIRECTION_LOCKED, S.BUILDER_V1_PACKAGE_PREPARATION): Actor.ORCHESTRATOR,
    (S.BUILDER_V1_PACKAGE_PREPARATION, S.BUILDER_V1_READY): Actor.ORCHESTRATOR,
    (S.BUILDER_V1_READY, S.BUILDER_V1_RUNNING): Actor.ORCHESTRATOR,
    (S.BUILDER_V1_RUNNING, S.V1_GENERATED): Actor.BUILDER_AI,
    (S.HUMAN_RESPONSE_CAPTURED, S.CRITIC_PACKAGE_PREPARATION): Actor.ORCHESTRATOR,
    (S.CRITIC_PACKAGE_PREPARATION, S.CRITIC_READY): Actor.ORCHESTRATOR,
    (S.CRITIC_READY, S.CRITIC_RUNNING): Actor.ORCHESTRATOR,
    (S.CRITIC_REVIEW_GENERATED, S.CONFLICT_SPACE_READY): Actor.SYSTEM,
    (S.CONFLICT_SPACE_READY, S.HUMAN_CRITIC_SELECTION): Actor.ORCHESTRATOR,
    (S.CRITIC_CLARIFICATION_REQUIRED, S.CRITIC_RUNNING): Actor.ORCHESTRATOR,
    (S.TRANSFER_CONFIRMATION_REQUIRED, S.TRANSFER_PACKAGE_LOCKED): Actor.SYSTEM,
    (S.TRANSFER_PACKAGE_LOCKED, S.MEMORY_RETRIEVAL_READY): Actor.ORCHESTRATOR,
    (S.CRITIC_RUNNING, S.CRITIC_REVIEW_GENERATED): Actor.CRITIC_AI,
    (S.MEMORY_RETRIEVAL_READY, S.MEMORY_RETRIEVAL_RUNNING): Actor.ORCHESTRATOR,
    (S.MEMORY_RETRIEVAL_RUNNING, S.MEMORY_REVIEW_REQUIRED): Actor.MEMORY,
    (S.MEMORY_RETRIEVAL_RUNNING, S.MEMORY_RETRIEVAL_FAILED): Actor.MEMORY,
    (S.MEMORY_SELECTION_CONFIRMATION_REQUIRED, S.MEMORY_SELECTION_LOCKED): Actor.SYSTEM,
    (S.MEMORY_SELECTION_LOCKED, S.RECONSTRUCTION_PACKAGE_PREPARATION): Actor.ORCHESTRATOR,
    (S.NO_RELEVANT_MEMORY, S.RECONSTRUCTION_PACKAGE_PREPARATION): Actor.ORCHESTRATOR,
    (S.RECONSTRUCTION_PACKAGE_PREPARATION, S.RECONSTRUCTION_PACKAGE_CONFIRMATION_REQUIRED): Actor.ORCHESTRATOR,
    (S.RECONSTRUCTION_PACKAGE_CONFIRMATION_REQUIRED, S.RECONSTRUCTION_PACKAGE_READY): Actor.SYSTEM,
    (S.RECONSTRUCTION_PACKAGE_READY, S.RECONSTRUCTION_RUNNING): Actor.ORCHESTRATOR,
    (S.RECONSTRUCTION_RUNNING, S.VN_GENERATED): Actor.BUILDER_AI,
    (S.VN_GENERATED, S.VERSION_COMPARISON_READY): Actor.ORCHESTRATOR,
    (S.VERSION_COMPARISON_READY, S.VERSION_COMPARISON_GENERATED): Actor.ORCHESTRATOR,
    (S.VERSION_COMPARISON_GENERATED, S.HUMAN_VERIFICATION_REQUIRED): Actor.ORCHESTRATOR,
    (S.VF_PRECHECK_REQUIRED, S.DIRECTION_DRAFT): Actor.SYSTEM,
    (S.VF_PRECHECK_REQUIRED, S.DIRECTION_VALIDATION_REQUIRED): Actor.SYSTEM,
    (S.VF_PRECHECK_REQUIRED, S.DIRECTION_CONFIRMATION_REQUIRED): Actor.SYSTEM,
    (S.VF_PRECHECK_REQUIRED, S.BUILDER_V1_PACKAGE_PREPARATION): Actor.SYSTEM,
    (S.VF_PRECHECK_REQUIRED, S.RECOVERY_REQUIRED): Actor.SYSTEM,
    (S.VF_PRECHECK_REQUIRED, S.HUMAN_RESPONSE_REQUIRED): Actor.SYSTEM,
    (S.VF_PRECHECK_REQUIRED, S.CRITIC_PACKAGE_PREPARATION): Actor.SYSTEM,
    (S.VF_PRECHECK_REQUIRED, S.CONFLICT_SPACE_READY): Actor.SYSTEM,
    (S.VF_PRECHECK_REQUIRED, S.HUMAN_CRITIC_SELECTION): Actor.SYSTEM,
    (S.VF_PRECHECK_REQUIRED, S.MANUAL_TRANSFER_PREPARATION): Actor.SYSTEM,
    (S.VF_PRECHECK_REQUIRED, S.MEMORY_RETRIEVAL_READY): Actor.SYSTEM,
    (S.VF_PRECHECK_REQUIRED, S.MEMORY_REVIEW_REQUIRED): Actor.SYSTEM,
    (S.VF_PRECHECK_REQUIRED, S.MEMORY_SELECTION_CONFIRMATION_REQUIRED): Actor.SYSTEM,
    (S.VF_PRECHECK_REQUIRED, S.NO_RELEVANT_MEMORY): Actor.SYSTEM,
    (S.VF_PRECHECK_REQUIRED, S.RECONSTRUCTION_PACKAGE_PREPARATION): Actor.SYSTEM,
    (S.VF_PRECHECK_REQUIRED, S.RECONSTRUCTION_PACKAGE_CONFIRMATION_REQUIRED): Actor.SYSTEM,
    (S.VF_PRECHECK_REQUIRED, S.RECONSTRUCTION_RUNNING): Actor.SYSTEM,
    (S.VF_PRECHECK_REQUIRED, S.VERSION_COMPARISON_READY): Actor.SYSTEM,
    (S.VF_PRECHECK_REQUIRED, S.HUMAN_VERIFICATION_REQUIRED): Actor.SYSTEM,
    (S.VF_PRECHECK_REQUIRED, S.VF_HUMAN_DECLARATION): Actor.SYSTEM,
    (S.VF_HUMAN_DECLARATION, S.VF_DECLARED): Actor.SYSTEM,
    (S.VF_DECLARED, S.VF_LOCKING_IN_PROGRESS): Actor.SYSTEM,
    (S.VF_LOCKING_IN_PROGRESS, S.VF_LOCKED): Actor.SYSTEM,
    (S.VF_LOCKED, S.FINAL_REPORT_GENERATION): Actor.SYSTEM,
    (S.FINAL_REPORT_GENERATION, S.FINAL_REPORT_READY): Actor.SYSTEM,
    (S.FINAL_REPORT_READY, S.FINAL_REPORT_GENERATION): Actor.SYSTEM,
    (S.FINAL_REPORT_READY, S.SESSION_ARCHIVED): Actor.SYSTEM,
}


SESSION_MODE_FULL_PROTOCOL = "FULL_PROTOCOL"
SESSION_MODE_DEMO_PROTOCOL = "DEMO_PROTOCOL"
SESSION_MODE_TECHNICAL_TEST = "TECHNICAL_TEST"
SESSION_MODE_RESEARCH_MODE = "RESEARCH_MODE"

VALID_SESSION_MODES = frozenset({
    SESSION_MODE_FULL_PROTOCOL,
    SESSION_MODE_DEMO_PROTOCOL,
    SESSION_MODE_TECHNICAL_TEST,
    SESSION_MODE_RESEARCH_MODE,
})

VF_PRECHECK_OK = "VF_PRECHECK_OK"
MODE_NOT_ELIGIBLE_FOR_VF = "MODE_NOT_ELIGIBLE_FOR_VF"

VF_PRECHECK_TARGET_BY_CODE = {
    "VF_PRECHECK_DIRECTION_MISSING": S.DIRECTION_DRAFT,
    "VF_PRECHECK_DIRECTION_VALIDATION_MISSING_OR_INVALID": S.DIRECTION_VALIDATION_REQUIRED,
    "VF_PRECHECK_DIRECTION_UNCONFIRMED": S.DIRECTION_CONFIRMATION_REQUIRED,
    "VF_PRECHECK_V1_MISSING": S.BUILDER_V1_PACKAGE_PREPARATION,
    "VF_PRECHECK_V1_INTEGRITY_INVALID": S.RECOVERY_REQUIRED,
    "VF_PRECHECK_HUMAN_RESPONSE_MISSING": S.HUMAN_RESPONSE_REQUIRED,
    "VF_PRECHECK_HUMAN_CONTRADICTION_OR_IDEA_MISSING": S.HUMAN_RESPONSE_REQUIRED,
    "VF_PRECHECK_CRITIC_MISSING": S.CRITIC_PACKAGE_PREPARATION,
    "VF_PRECHECK_CRITIC_INTEGRITY_INVALID": S.RECOVERY_REQUIRED,
    "VF_PRECHECK_CONFLICT_SPACE_MISSING": S.CONFLICT_SPACE_READY,
    "VF_PRECHECK_CONFLICT_SPACE_INTEGRITY_INVALID": S.RECOVERY_REQUIRED,
    "VF_PRECHECK_SELECTION_MISSING": S.HUMAN_CRITIC_SELECTION,
    "VF_PRECHECK_TRANSFER_MISSING": S.MANUAL_TRANSFER_PREPARATION,
    "VF_PRECHECK_TRANSFER_LOCK_OR_INTEGRITY_INVALID": S.RECOVERY_REQUIRED,
    "VF_PRECHECK_MEMORY_RETRIEVAL_NOT_EXECUTED": S.MEMORY_RETRIEVAL_READY,
    "VF_PRECHECK_MEMORY_REVIEW_PENDING": S.MEMORY_REVIEW_REQUIRED,
    "VF_PRECHECK_MEMORY_SELECTION_CONFIRMATION_MISSING": S.MEMORY_SELECTION_CONFIRMATION_REQUIRED,
    "VF_PRECHECK_MEMORY_TRANSFER_OR_LOCK_FAILED": S.RECOVERY_REQUIRED,
    "VF_PRECHECK_NO_RELEVANT_MEMORY_UNCONFIRMED": S.NO_RELEVANT_MEMORY,
    "VF_PRECHECK_RECONSTRUCTION_PACKAGE_MISSING": S.RECONSTRUCTION_PACKAGE_PREPARATION,
    "VF_PRECHECK_RECONSTRUCTION_PACKAGE_UNCONFIRMED": S.RECONSTRUCTION_PACKAGE_CONFIRMATION_REQUIRED,
    "VF_PRECHECK_RECONSTRUCTION_PACKAGE_LOCK_OR_INTEGRITY_INVALID": S.RECOVERY_REQUIRED,
    "VF_PRECHECK_RECONSTRUCTION_MISSING_WITH_READY_PACKAGE": S.RECONSTRUCTION_RUNNING,
    "VF_PRECHECK_COMPARISON_MISSING": S.VERSION_COMPARISON_READY,
    "VF_PRECHECK_PROVENANCE_OR_INTEGRITY_INVALID": S.RECOVERY_REQUIRED,
    "VF_PRECHECK_HUMAN_VERIFICATION_MISSING_OR_EVIDENCE_INSUFFICIENT": S.HUMAN_VERIFICATION_REQUIRED,
    VF_PRECHECK_OK: S.VF_HUMAN_DECLARATION,
}


@dataclass(frozen=True)
class ResultVersion:
    version_id: str
    session_id: str
    version_label: str
    content: str
    content_hash: str
    status: str
    created_revision: int


@dataclass(frozen=True)
class VFFinalIntegrityResult:
    declaration_persisted: bool
    actor_persisted: bool
    moment_persisted: bool
    provenance_persisted: bool
    selected_version_bound: bool
    no_unresolved_technical_error: bool
    reason: str
    checked_revision: int


@dataclass(frozen=True)
class VersionComparison:
    comparison_id: str
    session_id: str
    base_version_id: str
    base_version_label: str
    base_content_hash: str
    candidate_version_id: str
    candidate_version_label: str
    candidate_content_hash: str
    content_changed: bool
    unified_diff: str
    status: str
    generated_revision: int


@dataclass(frozen=True)
class HumanVerification:
    verification_id: str
    session_id: str
    comparison_id: str
    candidate_version_id: str
    candidate_version_label: str
    candidate_content_hash: str
    evidence_sufficient: bool
    verification_note: str
    verified_by: str
    status: str
    verified_revision: int


@dataclass(frozen=True)
class VFHumanDeclaration:
    selected_version: str
    selected_version_id: str
    selected_version_content_hash: str
    choice_reason: str
    relation_to_initial_direction: str
    decisive_human_contribution: str
    integrated_builder_elements: str
    decisive_critics: str
    rejected_critics: str
    memory_basis: str
    verifications_performed: str
    remaining_risks_and_uncertainties: str
    preserved_contradictions: str
    intended_use: str
    decision_assumption: str
    declared_revision: int



from dataclasses import replace as _hv_mem_replace
from datetime import datetime as _hv_mem_datetime, timezone as _hv_mem_timezone
from uuid import uuid4 as _hv_mem_uuid4


def _hv_memory_now() -> str:
    return _hv_mem_datetime.now(_hv_mem_timezone.utc).isoformat()


def _hv_memory_hash(payload: dict) -> str:
    import hashlib
    import json

    raw = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MemoryCandidate:
    candidate_id: str
    source_id: str
    source_type: str
    source_actor: str
    source_session_id: str
    original_content: str
    provenance: str
    retrieval_reason: str
    relevance_score: float | None
    warnings: tuple[str, ...]
    retrieved_at: str
    content_hash: str


@dataclass(frozen=True)
class MemoryRetrievalArtifact:
    retrieval_id: str
    session_id: str
    manual_transfer_package_id: str
    query_basis: str
    candidates: tuple[MemoryCandidate, ...]
    retrieval_outcome: str
    actor: str
    created_at: str
    content_hash: str


@dataclass(frozen=True)
class MemorySelectionItem:
    selection_item_id: str
    candidate_id: str
    decision: str
    accepted_fragment: str
    human_transformed_content: str
    reason: str
    conditions: str
    destination: str
    authorized_effect: str
    status: str
    content_hash: str


@dataclass(frozen=True)
class MemorySelection:
    selection_id: str
    session_id: str
    retrieval_id: str
    items: tuple[MemorySelectionItem, ...]
    status: str
    confirmed_by: str
    confirmed_at: str
    confirmed_content_hash: str
    confirmation_note: str
    locked_by: str
    locked_at: str
    content_hash: str
    created_at: str


@dataclass(frozen=True)
class MemoryTransferItem:
    transfer_item_id: str
    selection_item_id: str
    candidate_id: str
    source_id: str
    source_actor: str
    original_content: str
    selected_fragment: str
    human_transformed_content: str
    reason: str
    conditions: str
    destination: str
    authorized_effect: str
    provenance: str
    content_hash: str


@dataclass(frozen=True)
class MemoryTransferPackage:
    package_id: str
    session_id: str
    retrieval_id: str
    selection_id: str
    package_type: str
    items: tuple[MemoryTransferItem, ...]
    status: str
    confirmed_by: str
    confirmed_at: str
    confirmed_content_hash: str
    confirmation_note: str
    locked_by: str
    locked_at: str
    content_hash: str
    created_at: str


def _hv_memory_candidate_hash(item: MemoryCandidate) -> str:
    return _hv_memory_hash({
        "source_id": item.source_id,
        "source_type": item.source_type,
        "source_actor": item.source_actor,
        "source_session_id": item.source_session_id,
        "original_content": item.original_content,
        "provenance": item.provenance,
        "retrieval_reason": item.retrieval_reason,
        "relevance_score": item.relevance_score,
        "warnings": list(item.warnings),
    })


def _hv_memory_retrieval_hash(
    artifact: MemoryRetrievalArtifact,
) -> str:
    return _hv_memory_hash({
        "session_id": artifact.session_id,
        "manual_transfer_package_id":
            artifact.manual_transfer_package_id,
        "query_basis": artifact.query_basis,
        "retrieval_outcome": artifact.retrieval_outcome,
        "actor": artifact.actor,
        "candidates": [
            {
                "candidate_id": item.candidate_id,
                "content_hash": item.content_hash,
            }
            for item in artifact.candidates
        ],
    })


def _hv_memory_selection_item_hash(
    item: MemorySelectionItem,
) -> str:
    return _hv_memory_hash({
        "candidate_id": item.candidate_id,
        "decision": item.decision,
        "accepted_fragment": item.accepted_fragment,
        "human_transformed_content":
            item.human_transformed_content,
        "reason": item.reason,
        "conditions": item.conditions,
        "destination": item.destination,
        "authorized_effect": item.authorized_effect,
    })


def _hv_memory_selection_hash(
    artifact: MemorySelection,
) -> str:
    return _hv_memory_hash({
        "session_id": artifact.session_id,
        "retrieval_id": artifact.retrieval_id,
        "items": [
            {
                "selection_item_id": item.selection_item_id,
                "content_hash": item.content_hash,
            }
            for item in artifact.items
        ],
    })


def _hv_memory_transfer_item_hash(
    item: MemoryTransferItem,
) -> str:
    return _hv_memory_hash({
        "selection_item_id": item.selection_item_id,
        "candidate_id": item.candidate_id,
        "source_id": item.source_id,
        "source_actor": item.source_actor,
        "original_content": item.original_content,
        "selected_fragment": item.selected_fragment,
        "human_transformed_content":
            item.human_transformed_content,
        "reason": item.reason,
        "conditions": item.conditions,
        "destination": item.destination,
        "authorized_effect": item.authorized_effect,
        "provenance": item.provenance,
    })


def _hv_memory_transfer_hash(
    artifact: MemoryTransferPackage,
) -> str:
    return _hv_memory_hash({
        "session_id": artifact.session_id,
        "retrieval_id": artifact.retrieval_id,
        "selection_id": artifact.selection_id,
        "package_type": artifact.package_type,
        "items": [
            {
                "transfer_item_id": item.transfer_item_id,
                "content_hash": item.content_hash,
            }
            for item in artifact.items
        ],
    })



from copy import deepcopy as _hv_rc_deepcopy
from dataclasses import (
    asdict as _hv_rc_asdict,
    is_dataclass as _hv_rc_is_dataclass,
    replace as _hv_rc_replace,
)
from datetime import (
    datetime as _hv_rc_datetime,
    timezone as _hv_rc_timezone,
)
from uuid import uuid4 as _hv_rc_uuid4


def _hv_rc_now() -> str:
    return _hv_rc_datetime.now(_hv_rc_timezone.utc).isoformat()


def _hv_rc_snapshot(value):
    if value is None:
        return None

    if _hv_rc_is_dataclass(value):
        return _hv_rc_asdict(value)

    if isinstance(value, dict):
        return _hv_rc_deepcopy(value)

    if hasattr(value, "__dict__"):
        return _hv_rc_deepcopy(vars(value))

    raise TypeError(
        f"Unsupported Final Reconstruction snapshot type: "
        f"{type(value).__name__}"
    )


def _hv_rc_hash(payload: dict) -> str:
    import hashlib
    import json

    raw = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class FinalReconstructionPackage:
    package_id: str
    session_id: str
    package_revision: int

    source_version_id: str
    source_version_label: str
    source_version_content_hash: str

    human_direction: dict
    human_response: dict
    human_critic_selection: dict

    conflict_space_id: str
    critic_review_id: str

    manual_transfer: dict

    memory_mode: str
    memory_selection: dict | None
    memory_transfer: dict | None
    no_relevant_memory_reason: str

    builder_use_contract: str

    status: str

    confirmed_by: str
    confirmed_at: str
    confirmed_content_hash: str
    confirmation_note: str

    locked_by: str
    locked_at: str

    content_hash: str
    created_at: str
    created_revision: int


def _hv_rc_package_hash(
    package: FinalReconstructionPackage,
) -> str:
    return _hv_rc_hash({
        "session_id": package.session_id,
        "package_revision": package.package_revision,

        "source_version_id": package.source_version_id,
        "source_version_label": package.source_version_label,
        "source_version_content_hash":
            package.source_version_content_hash,

        "human_direction": package.human_direction,
        "human_response": package.human_response,
        "human_critic_selection":
            package.human_critic_selection,

        "conflict_space_id": package.conflict_space_id,
        "critic_review_id": package.critic_review_id,

        "manual_transfer": package.manual_transfer,

        "memory_mode": package.memory_mode,
        "memory_selection": package.memory_selection,
        "memory_transfer": package.memory_transfer,
        "no_relevant_memory_reason":
            package.no_relevant_memory_reason,

        "builder_use_contract":
            package.builder_use_contract,
    })


@dataclass(frozen=True)
class MemoryEffectVerification:
    memory_selection_item_id: str
    outcome: str
    reason: str
    verified_revision: int


@dataclass(frozen=True)
class FinalReport:
    report_version: int
    session_id: str
    vf_version_id: str
    vf_version_label: str
    vf_content_hash: str
    vf_content: str
    version_path: tuple[str, ...]
    choice_reason: str
    relation_to_initial_direction: str
    decisive_human_contribution: str
    integrated_builder_elements: str
    decisive_critics: str
    rejected_critics: str
    memory_basis: str
    memory_effect_evidence: tuple[str, ...]
    verifications_performed: str
    remaining_risks_and_uncertainties: str
    preserved_contradictions: str
    intended_use: str
    decision_assumption: str
    declaration_persisted: bool
    actor_persisted: bool
    moment_persisted: bool
    provenance_persisted: bool
    selected_version_bound: bool
    no_unresolved_technical_error: bool
    integrity_reasons: str
    supersedes_report_version: int | None
    human_review_basis_outcome: str | None
    human_review_basis_note: str | None
    revision_response: str | None
    human_declaration_revision: int
    integrity_checked_revision: int
    generated_revision: int


@dataclass(frozen=True)
class FinalReportReview:
    report_version: int
    outcome: str
    review_note: str
    report_generated_revision: int
    reviewed_revision: int


@dataclass(frozen=True)
class TransitionRecord:
    revision: int
    source: S
    target: S
    actor: Actor
    reason: str
    occurred_at: str


@dataclass(frozen=True)
class HumanDirection:
    direction_id: str
    objective: str
    context: str
    criteria: str
    limits: str
    facts: str
    assumptions: str
    intended_use: str
    status: str
    created_revision: int
    confirmed_revision: int | None = None


@dataclass(frozen=True)
class HumanCognitiveResponse:
    response_id: str
    session_id: str
    source_version_id: str
    source_version_label: str
    source_content_hash: str
    observation: str
    contradiction: str
    own_idea: str
    risks: str
    critic_questions: str
    status: str
    created_revision: int
    confirmed_revision: int | None = None


@dataclass(frozen=True)
class CriticAnalysisPackage:
    package_id: str
    session_id: str
    direction_id: str
    direction_confirmed_revision: int
    v1_version_id: str
    v1_content_hash: str
    human_response_id: str
    human_response_confirmed_revision: int
    verified_elements: str
    unverified_elements: str
    human_questions: str
    relevant_principles: str
    separation_requirement: str
    package_content: str
    package_hash: str
    status: str
    created_revision: int
    ready_revision: int | None = None


@dataclass(frozen=True)
class Criticism:
    criticism_id: str
    review_id: str
    session_id: str
    source_version_id: str
    source_content_hash: str
    human_response_id: str
    object: str
    criticism_type: str
    explanation: str
    basis: str
    risk: str
    severity: str
    question: str
    verification_required: str
    correction_direction: str
    provenance: str
    status: str
    created_revision: int


@dataclass(frozen=True)
class CriticReview:
    review_id: str
    package_id: str
    session_id: str
    source_version_id: str
    source_content_hash: str
    human_response_id: str
    raw_output: str
    raw_output_hash: str
    criticisms: tuple[Criticism, ...]
    actor: str
    created_revision: int


HUMAN_CRITIC_DECISIONS = frozenset({
    "ACCEPTED",
    "REJECTED",
    "PARTIALLY_ACCEPTED",
    "NEEDS_CLARIFICATION",
    "NEEDS_EXTERNAL_VERIFICATION",
    "KEEP_AS_UNRESOLVED",
    "TRANSFER_APPROVED",
    "RETURN_TO_CRITIC",
})


@dataclass(frozen=True)
class ConflictEntry:
    conflict_id: str
    conflict_type: str
    source_actor: str
    target_actor: str
    source_object_type: str
    source_object_id: str
    target_object_type: str
    target_object_id: str
    title: str
    central_issue: str
    source_position: str
    target_position: str
    criticism: Criticism | None
    basis: str
    risk: str
    severity: str
    question: str
    verification_required: str
    correction_direction: str
    status: str
    provenance: str
    created_revision: int


@dataclass(frozen=True)
class ConflictSpace:
    space_id: str
    session_id: str
    source_version_id: str
    source_content_hash: str
    human_response_id: str
    critic_review_id: str
    human_direction: HumanDirection
    source_version: ResultVersion
    human_response: HumanCognitiveResponse
    critic_review: CriticReview
    entries: tuple[ConflictEntry, ...]
    memory_reference_ids: tuple[str, ...]
    status: str
    actor: str
    created_revision: int


@dataclass(frozen=True)
class HumanCriticDecision:
    decision_id: str
    space_id: str
    criticism_id: str
    decision: str
    reason: str
    human_observation: str
    verification_performed: str
    source_consulted: str
    identified_limit: str
    required_change: str
    integration_condition: str
    link_to_human_idea: str
    risk_position: str
    actor: str
    created_revision: int


@dataclass(frozen=True)
class HumanCriticSelection:
    selection_id: str
    space_id: str
    session_id: str
    decisions: tuple[HumanCriticDecision, ...]
    actor: str
    created_revision: int



import dataclasses as _hv_dc
import hashlib as _hv_hashlib
import json as _hv_json
import uuid as _hv_uuid
from datetime import datetime as _hv_datetime, timezone as _hv_timezone


def _hv_manual_transfer_now() -> str:
    return _hv_datetime.now(_hv_timezone.utc).isoformat()


def _hv_manual_transfer_scalar(value) -> str:
    if hasattr(value, "value"):
        value = value.value
    if value is None:
        return ""
    return str(value)


def _hv_manual_transfer_as_data(value):
    if _hv_dc.is_dataclass(value):
        return _hv_dc.asdict(value)
    if isinstance(value, dict):
        return {
            str(k): _hv_manual_transfer_as_data(v)
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_hv_manual_transfer_as_data(v) for v in value]
    if hasattr(value, "value"):
        return value.value
    return value


def _hv_manual_transfer_collect_strings(value) -> set[str]:
    values: set[str] = set()

    if isinstance(value, dict):
        for item in value.values():
            values.update(_hv_manual_transfer_collect_strings(item))
        return values

    if isinstance(value, (list, tuple)):
        for item in value:
            values.update(_hv_manual_transfer_collect_strings(item))
        return values

    scalar = _hv_manual_transfer_scalar(value)
    if scalar:
        values.add(scalar)
    return values


def _hv_manual_transfer_find_id_containers(value, source_id: str) -> list[dict]:
    found: list[dict] = []

    if isinstance(value, dict):
        direct_scalars = {
            _hv_manual_transfer_scalar(v)
            for v in value.values()
            if not isinstance(v, (dict, list, tuple))
        }
        if source_id in direct_scalars:
            found.append(value)

        for child in value.values():
            found.extend(
                _hv_manual_transfer_find_id_containers(child, source_id)
            )

    elif isinstance(value, (list, tuple)):
        for child in value:
            found.extend(
                _hv_manual_transfer_find_id_containers(child, source_id)
            )

    return found


@dataclass(frozen=True)
class ManualTransferItem:
    item_id: str
    source_object_type: str
    source_object_id: str
    source_actor_type: str
    transfer_type: str
    original_content: str
    selected_fragment: str
    human_transformed_content: str
    reason: str
    expected_effect: str
    conditions: str
    destination: str
    target_version_label: str
    status: str
    created_at: str
    content_hash: str


@dataclass(frozen=True)
class ManualTransferPackage:
    package_id: str
    session_id: str
    branch_id: str
    cycle_id: str
    package_type: str
    version_number: int
    source_version_id: str
    conflict_space_id: str
    human_selection_id: str
    target_type: str
    target_version_label: str
    items: tuple[ManualTransferItem, ...]
    status: str
    confirmed_by: str
    confirmed_at: str
    confirmed_content_hash: str
    human_confirmation_note: str
    locked_by: str
    locked_at: str
    content_hash: str
    created_at: str


def _hv_manual_transfer_item_hash(item: ManualTransferItem) -> str:
    payload = {
        "source_object_type": item.source_object_type,
        "source_object_id": item.source_object_id,
        "source_actor_type": item.source_actor_type,
        "transfer_type": item.transfer_type,
        "original_content": item.original_content,
        "selected_fragment": item.selected_fragment,
        "human_transformed_content": item.human_transformed_content,
        "reason": item.reason,
        "expected_effect": item.expected_effect,
        "conditions": item.conditions,
        "destination": item.destination,
        "target_version_label": item.target_version_label,
        "status": item.status,
    }
    raw = _hv_json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return _hv_hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _hv_manual_transfer_package_hash(
    package: ManualTransferPackage,
) -> str:
    payload = {
        "session_id": package.session_id,
        "branch_id": package.branch_id,
        "cycle_id": package.cycle_id,
        "package_type": package.package_type,
        "source_version_id": package.source_version_id,
        "conflict_space_id": package.conflict_space_id,
        "human_selection_id": package.human_selection_id,
        "target_type": package.target_type,
        "target_version_label": package.target_version_label,
        "items": [
            {
                "item_id": item.item_id,
                "content_hash": item.content_hash,
            }
            for item in package.items
        ],
    }
    raw = _hv_json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return _hv_hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class SystemOrchestrator:
    state: S = S.SESSION_CREATED
    revision: int = 0
    history: list[TransitionRecord] = field(default_factory=list)
    session_id: str | None = None
    result_versions: dict[str, ResultVersion] = field(default_factory=dict)
    version_comparison_artifact: VersionComparison | None = None
    version_comparison_history: list[VersionComparison] = field(
        default_factory=list
    )
    human_verification_artifact: HumanVerification | None = None
    human_verification_history: list[HumanVerification] = field(
        default_factory=list
    )
    human_direction_artifact: HumanDirection | None = None
    human_direction_history: list[HumanDirection] = field(default_factory=list)
    human_response_artifact: HumanCognitiveResponse | None = None
    human_response_history: list[HumanCognitiveResponse] = field(default_factory=list)
    critic_package_artifact: CriticAnalysisPackage | None = None
    critic_package_history: list[CriticAnalysisPackage] = field(default_factory=list)
    critic_review_artifact: CriticReview | None = None
    critic_review_history: list[CriticReview] = field(default_factory=list)
    conflict_space_artifact: ConflictSpace | None = None
    conflict_space_history: list[ConflictSpace] = field(default_factory=list)
    human_critic_selection_artifact: HumanCriticSelection | None = None
    human_critic_selection_history: list[HumanCriticSelection] = field(default_factory=list)
    manual_transfer_artifact: ManualTransferPackage | None = None
    manual_transfer_history: list[ManualTransferPackage] = field(default_factory=list)
    _manual_transfer_lock_authorization_hash: str | None = field(
        default=None,
        repr=False,
    )

    vf_locked_version_id: str | None = None
    vf_locked_content_hash: str | None = None
    memory_retrieval_artifact: MemoryRetrievalArtifact | None = None
    memory_retrieval_history: list[MemoryRetrievalArtifact] = field(
        default_factory=list
    )
    memory_selection_artifact: MemorySelection | None = None
    memory_selection_history: list[MemorySelection] = field(
        default_factory=list
    )
    memory_transfer_artifact: MemoryTransferPackage | None = None
    memory_transfer_history: list[MemoryTransferPackage] = field(
        default_factory=list
    )
    memory_negative_human_reason: str | None = None
    _memory_selection_lock_authorization_hash: str | None = field(
        default=None,
        repr=False,
    )
    _memory_negative_resolution_authorized: bool = field(
        default=False,
        repr=False,
    )
    retrieval_outcome: str | None = None
    outcome_reason: str = ""
    memory_resolution_outcome: str | None = None
    negative_result_reason: str = ""
    session_mode: str | None = None
    vf_precheck_code: str | None = None
    vf_precheck_condition: str = ""
    vf_precheck_target: S | None = None
    vf_precheck_reason: str = ""
    vf_precheck_revision: int | None = None
    reconstruction_package_artifact: FinalReconstructionPackage | None = None
    reconstruction_package_history: list[FinalReconstructionPackage] = field(
        default_factory=list
    )
    _reconstruction_package_lock_authorization_hash: str | None = field(
        default=None,
        repr=False,
    )

    memory_effect_verifications: list[MemoryEffectVerification] = field(
        default_factory=list
    )
    vf_human_declaration: VFHumanDeclaration | None = None
    vf_human_declaration_revision: int | None = None
    vf_final_integrity_result: VFFinalIntegrityResult | None = None
    vf_final_integrity_revision: int | None = None
    final_reports: list[FinalReport] = field(default_factory=list)
    final_report: FinalReport | None = None
    final_report_revision: int | None = None
    final_report_reviews: list[FinalReportReview] = field(default_factory=list)
    final_report_review: FinalReportReview | None = None
    final_report_review_revision: int | None = None

    def record_human_direction_draft(
        self,
        *,
        objective: str,
        context: str,
        criteria: str,
        limits: str,
        facts: str = "",
        assumptions: str = "",
        intended_use: str = "",
        actor: Actor,
    ) -> HumanDirection:
        from uuid import uuid4

        if actor is not Actor.HUMAN:
            raise TransitionRejected(
                "Human Direction requires HUMAN actor."
            )

        if self.state is not S.DIRECTION_DRAFT:
            raise TransitionRejected(
                "Human Direction draft requires DIRECTION_DRAFT."
            )

        required = {
            "objective": objective,
            "context": context,
            "criteria": criteria,
            "limits": limits,
        }

        missing = [
            name
            for name, value in required.items()
            if not isinstance(value, str) or not value.strip()
        ]

        if missing:
            raise TransitionRejected(
                "Human Direction missing required fields: "
                + ", ".join(sorted(missing))
            )

        for name, value in {
            "facts": facts,
            "assumptions": assumptions,
            "intended_use": intended_use,
        }.items():
            if not isinstance(value, str):
                raise TransitionRejected(
                    f"Human Direction {name} must be text."
                )

        current = self.human_direction_artifact

        if current is not None and current.status == "CONFIRMED":
            raise TransitionRejected(
                "Confirmed Human Direction is locked."
            )

        artifact = HumanDirection(
            direction_id=str(uuid4()),
            objective=objective,
            context=context,
            criteria=criteria,
            limits=limits,
            facts=facts,
            assumptions=assumptions,
            intended_use=intended_use,
            status="DRAFT",
            created_revision=self.revision,
        )

        self.human_direction_artifact = artifact
        self.human_direction_history.append(artifact)
        return artifact

    def confirm_human_direction(
        self,
        *,
        actor: Actor,
    ) -> HumanDirection:
        if actor is not Actor.HUMAN:
            raise TransitionRejected(
                "Human Direction confirmation requires HUMAN actor."
            )

        if self.state is not S.DIRECTION_CONFIRMATION_REQUIRED:
            raise TransitionRejected(
                "Human Direction confirmation requires "
                "DIRECTION_CONFIRMATION_REQUIRED."
            )

        direction = self.human_direction_artifact

        if direction is None or direction.status != "DRAFT":
            raise TransitionRejected(
                "Human Direction confirmation requires a current draft."
            )

        self.transition(
            S.DIRECTION_LOCKED,
            Actor.HUMAN,
            "HUMAN explicitly confirmed and locked direction.",
        )

        confirmed = replace(
            direction,
            status="CONFIRMED",
            confirmed_revision=self.revision,
        )

        self.human_direction_artifact = confirmed
        self.human_direction_history.append(confirmed)
        return confirmed

    def _resolve_v1_for_human_response(self) -> ResultVersion:
        versions = [
            version
            for version in self.result_versions.values()
            if version.version_label == "V1"
        ]

        if len(versions) != 1:
            raise TransitionRejected(
                "HUMAN cognitive response requires exactly one recorded V1."
            )

        version = versions[0]

        if (
            self.session_id is None
            or version.session_id != self.session_id
        ):
            raise TransitionRejected(
                "HUMAN cognitive response V1 must belong to the current session."
            )

        return version

    def record_human_response_draft(
        self,
        *,
        observation: str,
        contradiction: str,
        own_idea: str,
        risks: str = "",
        critic_questions: str = "",
        actor: Actor,
    ) -> HumanCognitiveResponse:
        from uuid import uuid4

        if actor is not Actor.HUMAN:
            raise TransitionRejected(
                "HUMAN cognitive response requires HUMAN actor."
            )

        if self.state not in {
            S.HUMAN_RESPONSE_REQUIRED,
            S.HUMAN_RESPONSE_DRAFT,
            S.HUMAN_RESPONSE_CONFIRMATION_REQUIRED,
        }:
            raise TransitionRejected(
                "HUMAN cognitive response draft is not allowed "
                f"from {self.state.value}."
            )

        current = self.human_response_artifact
        if current is not None and current.status == "CONFIRMED":
            raise TransitionRejected(
                "Confirmed HUMAN cognitive response is locked."
            )

        required = {
            "observation": observation,
            "contradiction": contradiction,
            "own_idea": own_idea,
        }

        missing = [
            name
            for name, value in required.items()
            if not isinstance(value, str) or not value.strip()
        ]

        if missing:
            raise TransitionRejected(
                "HUMAN cognitive response missing required fields: "
                + ", ".join(sorted(missing))
            )

        if not isinstance(risks, str):
            raise TransitionRejected(
                "HUMAN cognitive response risks must be text."
            )

        if not isinstance(critic_questions, str):
            raise TransitionRejected(
                "HUMAN cognitive response critic_questions must be text."
            )

        source_v1 = self._resolve_v1_for_human_response()

        if self.state is S.HUMAN_RESPONSE_CONFIRMATION_REQUIRED:
            self.transition(
                S.HUMAN_RESPONSE_DRAFT,
                Actor.HUMAN,
                "HUMAN returned cognitive response for revision.",
            )

        if self.state is S.HUMAN_RESPONSE_REQUIRED:
            self.transition(
                S.HUMAN_RESPONSE_DRAFT,
                Actor.HUMAN,
                "HUMAN began independent cognitive response to V1.",
            )

        response = HumanCognitiveResponse(
            response_id=str(uuid4()),
            session_id=source_v1.session_id,
            source_version_id=source_v1.version_id,
            source_version_label=source_v1.version_label,
            source_content_hash=source_v1.content_hash,
            observation=observation,
            contradiction=contradiction,
            own_idea=own_idea,
            risks=risks,
            critic_questions=critic_questions,
            status="DRAFT",
            created_revision=self.revision,
        )

        self.human_response_artifact = response
        self.human_response_history.append(response)
        return response

    def request_human_response_confirmation(
        self,
        *,
        actor: Actor,
    ) -> HumanCognitiveResponse:
        if actor is not Actor.HUMAN:
            raise TransitionRejected(
                "HUMAN response confirmation request requires HUMAN actor."
            )

        if self.state is not S.HUMAN_RESPONSE_DRAFT:
            raise TransitionRejected(
                "HUMAN response confirmation requires HUMAN_RESPONSE_DRAFT."
            )

        response = self.human_response_artifact

        if response is None or response.status != "DRAFT":
            raise TransitionRejected(
                "HUMAN response confirmation requires a current draft."
            )

        self.transition(
            S.HUMAN_RESPONSE_CONFIRMATION_REQUIRED,
            Actor.HUMAN,
            "HUMAN submitted cognitive response for explicit confirmation.",
        )

        return response

    def confirm_human_response(
        self,
        *,
        actor: Actor,
    ) -> HumanCognitiveResponse:
        if actor is not Actor.HUMAN:
            raise TransitionRejected(
                "HUMAN response capture requires HUMAN actor."
            )

        if self.state is not S.HUMAN_RESPONSE_CONFIRMATION_REQUIRED:
            raise TransitionRejected(
                "HUMAN response capture requires "
                "HUMAN_RESPONSE_CONFIRMATION_REQUIRED."
            )

        response = self.human_response_artifact

        if response is None or response.status != "DRAFT":
            raise TransitionRejected(
                "HUMAN response capture requires a current draft."
            )

        self.transition(
            S.HUMAN_RESPONSE_CAPTURED,
            Actor.HUMAN,
            "HUMAN explicitly confirmed cognitive response to V1.",
        )

        confirmed = replace(
            response,
            status="CONFIRMED",
            confirmed_revision=self.revision,
        )

        self.human_response_artifact = confirmed
        self.human_response_history.append(confirmed)
        return confirmed

    def prepare_critic_package(
        self,
        *,
        verified_elements: str,
        unverified_elements: str,
        relevant_principles: str,
        actor: Actor,
    ) -> CriticAnalysisPackage:
        from hashlib import sha256
        from uuid import uuid4

        if actor is not Actor.ORCHESTRATOR:
            raise TransitionRejected(
                "Critic package preparation requires ORCHESTRATOR actor."
            )

        if self.state is not S.HUMAN_RESPONSE_CAPTURED:
            raise TransitionRejected(
                "Critic package preparation requires "
                "HUMAN_RESPONSE_CAPTURED."
            )

        if self.critic_package_artifact is not None:
            raise TransitionRejected(
                "Critic analysis package already exists."
            )

        direction = self.human_direction_artifact
        response = self.human_response_artifact
        source_v1 = self._resolve_v1_for_human_response()

        if (
            direction is None
            or direction.status != "CONFIRMED"
            or direction.confirmed_revision is None
        ):
            raise TransitionRejected(
                "Critic package requires confirmed Human Direction."
            )

        if (
            response is None
            or response.status != "CONFIRMED"
            or response.confirmed_revision is None
        ):
            raise TransitionRejected(
                "Critic package requires confirmed HUMAN cognitive response."
            )

        if response.source_version_id != source_v1.version_id:
            raise TransitionRejected(
                "Confirmed HUMAN response is not bound to current V1."
            )

        if response.source_content_hash != source_v1.content_hash:
            raise TransitionRejected(
                "Confirmed HUMAN response V1 hash mismatch."
            )

        for name, value in {
            "verified_elements": verified_elements,
            "unverified_elements": unverified_elements,
            "relevant_principles": relevant_principles,
        }.items():
            if not isinstance(value, str) or not value.strip():
                raise TransitionRejected(
                    f"Critic package {name} must be non-empty text."
                )

        separation_requirement = (
            "Critic AI must explicitly distinguish FACTS, ASSUMPTIONS, "
            "INTERPRETATIONS, and UNVERIFIED CLAIMS. It must not confirm "
            "Builder AI or HUMAN by default and must not modify V1 or "
            "rewrite the HUMAN contribution."
        )

        package_content = (
            "HUMAN VECTOR — INDEPENDENT CRITIC PACKAGE\n"
            f"SESSION_ID: {source_v1.session_id}\n"
            f"DIRECTION_ID: {direction.direction_id}\n"
            f"DIRECTION_CONFIRMED_REVISION: "
            f"{direction.confirmed_revision}\n"
            f"V1_VERSION_ID: {source_v1.version_id}\n"
            f"V1_CONTENT_HASH: {source_v1.content_hash}\n"
            f"HUMAN_RESPONSE_ID: {response.response_id}\n"
            f"HUMAN_RESPONSE_CONFIRMED_REVISION: "
            f"{response.confirmed_revision}\n"
            "\n--- HUMAN DIRECTION ---\n"
            f"OBJECTIVE:\n{direction.objective}\n"
            f"CONTEXT:\n{direction.context}\n"
            f"CRITERIA:\n{direction.criteria}\n"
            f"LIMITS:\n{direction.limits}\n"
            f"FACTS:\n{direction.facts}\n"
            f"ASSUMPTIONS:\n{direction.assumptions}\n"
            f"INTENDED_USE:\n{direction.intended_use}\n"
            "\n--- EXACT BUILDER V1 ---\n"
            f"{source_v1.content}\n"
            "\n--- CONFIRMED HUMAN COGNITIVE RESPONSE ---\n"
            f"OBSERVATION:\n{response.observation}\n"
            f"CONTRADICTION:\n{response.contradiction}\n"
            f"OWN_IDEA:\n{response.own_idea}\n"
            f"RISKS:\n{response.risks}\n"
            f"HUMAN_QUESTIONS_TO_CRITIC:\n"
            f"{response.critic_questions}\n"
            "\n--- VERIFICATION CONTEXT ---\n"
            f"VERIFIED_ELEMENTS:\n{verified_elements}\n"
            f"UNVERIFIED_ELEMENTS:\n{unverified_elements}\n"
            f"RELEVANT_HUMAN_VECTOR_PRINCIPLES:\n"
            f"{relevant_principles}\n"
            f"SEPARATION_REQUIREMENT:\n"
            f"{separation_requirement}\n"
        )

        package_hash = sha256(
            package_content.encode("utf-8")
        ).hexdigest()

        package_id = str(uuid4())

        self.transition(
            S.CRITIC_PACKAGE_PREPARATION,
            Actor.ORCHESTRATOR,
            "Prepare independent Critic AI package from confirmed artefacts.",
        )

        package = CriticAnalysisPackage(
            package_id=package_id,
            session_id=source_v1.session_id,
            direction_id=direction.direction_id,
            direction_confirmed_revision=direction.confirmed_revision,
            v1_version_id=source_v1.version_id,
            v1_content_hash=source_v1.content_hash,
            human_response_id=response.response_id,
            human_response_confirmed_revision=response.confirmed_revision,
            verified_elements=verified_elements,
            unverified_elements=unverified_elements,
            human_questions=response.critic_questions,
            relevant_principles=relevant_principles,
            separation_requirement=separation_requirement,
            package_content=package_content,
            package_hash=package_hash,
            status="PREPARED",
            created_revision=self.revision,
        )

        self.critic_package_artifact = package
        self.critic_package_history.append(package)

        return package

    def mark_critic_ready(
        self,
        *,
        actor: Actor,
    ) -> CriticAnalysisPackage:
        if actor is not Actor.ORCHESTRATOR:
            raise TransitionRejected(
                "CRITIC_READY requires ORCHESTRATOR actor."
            )

        if self.state is not S.CRITIC_PACKAGE_PREPARATION:
            raise TransitionRejected(
                "CRITIC_READY requires CRITIC_PACKAGE_PREPARATION."
            )

        package = self.critic_package_artifact

        if package is None or package.status != "PREPARED":
            raise TransitionRejected(
                "CRITIC_READY requires a prepared Critic package."
            )

        self.transition(
            S.CRITIC_READY,
            Actor.ORCHESTRATOR,
            "Independent Critic package complete and ready.",
        )

        ready = replace(
            package,
            status="READY",
            ready_revision=self.revision,
        )

        self.critic_package_artifact = ready
        self.critic_package_history.append(ready)

        return ready

    def start_critic_running(
        self,
        *,
        actor: Actor,
    ) -> CriticAnalysisPackage:
        if actor is not Actor.ORCHESTRATOR:
            raise TransitionRejected(
                "CRITIC_RUNNING setup requires ORCHESTRATOR actor."
            )

        if self.state is not S.CRITIC_READY:
            raise TransitionRejected(
                "CRITIC_RUNNING requires CRITIC_READY."
            )

        package = self.critic_package_artifact

        if package is None or package.status != "READY":
            raise TransitionRejected(
                "CRITIC_RUNNING requires a READY Critic package."
            )

        self.transition(
            S.CRITIC_RUNNING,
            Actor.ORCHESTRATOR,
            "Start independent Critic AI execution.",
        )

        return package

    def record_critic_review(
        self,
        *,
        criticisms: list[dict[str, str]],
        raw_output: str,
        actor: Actor,
    ) -> CriticReview:
        from hashlib import sha256
        from uuid import uuid4

        if actor is not Actor.CRITIC_AI:
            raise TransitionRejected(
                "Critic review recording requires CRITIC_AI actor."
            )

        if self.state is not S.CRITIC_RUNNING:
            raise TransitionRejected(
                "Critic review recording requires CRITIC_RUNNING."
            )

        if self.critic_review_artifact is not None:
            raise TransitionRejected(
                "Critic review already recorded."
            )

        package = self.critic_package_artifact

        if package is None or package.status != "READY":
            raise TransitionRejected(
                "Critic review requires the exact READY Critic package."
            )

        if not isinstance(raw_output, str) or not raw_output.strip():
            raise TransitionRejected(
                "Critic review requires non-empty raw output."
            )

        if not isinstance(criticisms, list) or not criticisms:
            raise TransitionRejected(
                "Critic review requires at least one structured criticism."
            )

        required_fields = (
            "object",
            "type",
            "explanation",
            "basis",
            "risk",
            "severity",
            "question",
            "verification_required",
            "correction_direction",
        )

        normalized: list[dict[str, str]] = []

        for index, item in enumerate(criticisms, start=1):
            if not isinstance(item, dict):
                raise TransitionRejected(
                    f"Criticism {index} must be a mapping."
                )

            missing = [
                field_name
                for field_name in required_fields
                if (
                    field_name not in item
                    or not isinstance(item[field_name], str)
                    or not item[field_name].strip()
                )
            ]

            if missing:
                raise TransitionRejected(
                    f"Criticism {index} missing required fields: "
                    + ", ".join(sorted(missing))
                )

            target_object = item["object"].strip()
            if target_object not in {
                "BUILDER_V1",
                "HUMAN_COGNITIVE_RESPONSE",
            }:
                raise TransitionRejected(
                    f"Criticism {index} object must be exactly "
                    "BUILDER_V1 or HUMAN_COGNITIVE_RESPONSE."
                )

            normalized.append(
                {
                    field_name: item[field_name]
                    for field_name in required_fields
                }
            )

        review_id = str(uuid4())
        raw_output_hash = sha256(
            raw_output.encode("utf-8")
        ).hexdigest()

        criticism_ids = [
            str(uuid4())
            for _ in normalized
        ]

        self.transition(
            S.CRITIC_REVIEW_GENERATED,
            Actor.CRITIC_AI,
            "Independent Critic AI review generated and recorded.",
        )

        structured = tuple(
            Criticism(
                criticism_id=criticism_id,
                review_id=review_id,
                session_id=package.session_id,
                source_version_id=package.v1_version_id,
                source_content_hash=package.v1_content_hash,
                human_response_id=package.human_response_id,
                object=item["object"],
                criticism_type=item["type"],
                explanation=item["explanation"],
                basis=item["basis"],
                risk=item["risk"],
                severity=item["severity"],
                question=item["question"],
                verification_required=item["verification_required"],
                correction_direction=item["correction_direction"],
                provenance=Actor.CRITIC_AI.value,
                status="UNREVIEWED",
                created_revision=self.revision,
            )
            for criticism_id, item
            in zip(criticism_ids, normalized)
        )

        review = CriticReview(
            review_id=review_id,
            package_id=package.package_id,
            session_id=package.session_id,
            source_version_id=package.v1_version_id,
            source_content_hash=package.v1_content_hash,
            human_response_id=package.human_response_id,
            raw_output=raw_output,
            raw_output_hash=raw_output_hash,
            criticisms=structured,
            actor=Actor.CRITIC_AI.value,
            created_revision=self.revision,
        )

        self.critic_review_artifact = review
        self.critic_review_history.append(review)

        return review

    def build_conflict_space(self, actor: Actor) -> ConflictSpace:
        from uuid import uuid4
        if actor is not Actor.SYSTEM:
            raise TransitionRejected(
                "Conflict Space construction requires SYSTEM actor."
            )

        if self.state is not S.CRITIC_REVIEW_GENERATED:
            raise TransitionRejected(
                "Conflict Space construction requires CRITIC_REVIEW_GENERATED."
            )

        if self.conflict_space_artifact is not None:
            raise TransitionRejected(
                "Conflict Space already recorded for the current review."
            )

        review = self.critic_review_artifact
        direction = self.human_direction_artifact
        human_response = self.human_response_artifact

        if review is None:
            raise TransitionRejected(
                "Conflict Space requires a persisted CriticReview."
            )

        if direction is None:
            raise TransitionRejected(
                "Conflict Space requires the confirmed Human Direction artifact."
            )

        if human_response is None:
            raise TransitionRejected(
                "Conflict Space requires the confirmed Human Cognitive Response."
            )

        source_version = self.result_versions.get(review.source_version_id)
        if source_version is None:
            raise TransitionRejected(
                "Conflict Space requires the exact source ResultVersion."
            )

        if review.human_response_id != human_response.response_id:
            raise TransitionRejected(
                "Conflict Space Human Response does not match CriticReview."
            )

        if not review.criticisms:
            raise TransitionRejected(
                "Conflict Space requires at least one persisted criticism."
            )

        next_revision = self.revision + 1

        if human_response.source_version_id != review.source_version_id:
            raise TransitionRejected(
                "Conflict Space Human Response source version does not match CriticReview."
            )

        if human_response.source_content_hash != review.source_content_hash:
            raise TransitionRejected(
                "Conflict Space Human Response source hash does not match CriticReview."
            )

        if not isinstance(human_response.contradiction, str) or not human_response.contradiction.strip():
            raise TransitionRejected(
                "Conflict Space requires the confirmed HUMAN contradiction."
            )

        human_builder_conflict = ConflictEntry(
            conflict_id=str(uuid4()),
            conflict_type="HUMAN_BUILDER_CONFLICT",
            source_actor=Actor.HUMAN.value,
            target_actor=Actor.BUILDER_AI.value,
            source_object_type="HUMAN_COGNITIVE_RESPONSE",
            source_object_id=human_response.response_id,
            target_object_type="BUILDER_V1",
            target_object_id=source_version.version_id,
            title="HUMAN contradiction to Builder V1",
            central_issue=human_response.contradiction,
            source_position=human_response.contradiction,
            target_position=source_version.content,
            criticism=None,
            basis=human_response.observation,
            risk=human_response.risks,
            severity="NOT_ASSIGNED",
            question=human_response.critic_questions,
            verification_required="",
            correction_direction=human_response.own_idea,
            status="UNRESOLVED",
            provenance=Actor.HUMAN.value,
            created_revision=next_revision,
        )

        critic_conflicts: list[ConflictEntry] = []

        for criticism in review.criticisms:
            target = criticism.object.strip().upper()

            if target == "BUILDER_V1":
                conflict_type = "CRITIC_BUILDER_CONFLICT"
                target_actor = Actor.BUILDER_AI.value
                target_object_type = "BUILDER_V1"
                target_object_id = source_version.version_id
                target_position = source_version.content

            elif target == "HUMAN_COGNITIVE_RESPONSE":
                conflict_type = "CRITIC_HUMAN_CONFLICT"
                target_actor = Actor.HUMAN.value
                target_object_type = "HUMAN_COGNITIVE_RESPONSE"
                target_object_id = human_response.response_id
                target_position = (
                    "OBSERVATION: " + human_response.observation
                    + "\nCONTRADICTION: " + human_response.contradiction
                    + "\nOWN_IDEA: " + human_response.own_idea
                )

            else:
                raise TransitionRejected(
                    "Criticism object must be canonical: "
                    "BUILDER_V1 or HUMAN_COGNITIVE_RESPONSE."
                )

            critic_conflicts.append(
                ConflictEntry(
                    conflict_id=str(uuid4()),
                    conflict_type=conflict_type,
                    source_actor=Actor.CRITIC_AI.value,
                    target_actor=target_actor,
                    source_object_type="CRITICISM",
                    source_object_id=criticism.criticism_id,
                    target_object_type=target_object_type,
                    target_object_id=target_object_id,
                    title=f"{conflict_type}: {criticism.criticism_type}",
                    central_issue=criticism.explanation,
                    source_position=criticism.explanation,
                    target_position=target_position,
                    criticism=criticism,
                    basis=criticism.basis,
                    risk=criticism.risk,
                    severity=criticism.severity,
                    question=criticism.question,
                    verification_required=criticism.verification_required,
                    correction_direction=criticism.correction_direction,
                    status="UNRESOLVED",
                    provenance=criticism.provenance,
                    created_revision=next_revision,
                )
            )

        entries = (
            human_builder_conflict,
            *critic_conflicts,
        )


        space = ConflictSpace(
            space_id=str(uuid4()),
            session_id=self.session_id,
            source_version_id=review.source_version_id,
            source_content_hash=review.source_content_hash,
            human_response_id=review.human_response_id,
            critic_review_id=review.review_id,
            human_direction=direction,
            source_version=source_version,
            human_response=human_response,
            critic_review=review,
            entries=entries,
            memory_reference_ids=(),
            status="READY",
            actor=Actor.SYSTEM.value,
            created_revision=next_revision,
        )

        # Persist first so the generic transition guard can prove that the
        # comparative artifact exists. Roll back atomically if transition fails.
        self.conflict_space_artifact = space
        self.conflict_space_history.append(space)

        try:
            self.transition(
                S.CONFLICT_SPACE_READY,
                Actor.SYSTEM,
                "Structured Conflict Space built from exact HUMAN / Builder / Critic artifacts.",
            )
        except Exception:
            self.conflict_space_artifact = None
            if self.conflict_space_history and self.conflict_space_history[-1] is space:
                self.conflict_space_history.pop()
            raise

        return space

    def open_human_critic_selection(self, actor: Actor) -> None:
        if actor is not Actor.ORCHESTRATOR:
            raise TransitionRejected(
                "Opening HUMAN Critic Selection requires ORCHESTRATOR actor."
            )

        if self.state is not S.CONFLICT_SPACE_READY:
            raise TransitionRejected(
                "HUMAN Critic Selection requires CONFLICT_SPACE_READY."
            )

        if self.conflict_space_artifact is None:
            raise TransitionRejected(
                "HUMAN Critic Selection requires a persisted Conflict Space."
            )

        self.transition(
            S.HUMAN_CRITIC_SELECTION,
            Actor.ORCHESTRATOR,
            "Conflict Space presented for explicit HUMAN criticism selection.",
        )

    def record_human_critic_selection(
        self,
        actor: Actor,
        decisions: list[dict[str, str]],
    ) -> HumanCriticSelection:
        from uuid import uuid4
        if actor is not Actor.HUMAN:
            raise TransitionRejected(
                "Criticism selection requires HUMAN actor."
            )

        if self.state is not S.HUMAN_CRITIC_SELECTION:
            raise TransitionRejected(
                "Criticism selection requires HUMAN_CRITIC_SELECTION."
            )

        space = self.conflict_space_artifact
        if space is None:
            raise TransitionRejected(
                "HUMAN Critic Selection requires the persisted Conflict Space."
            )

        if self.human_critic_selection_artifact is not None:
            raise TransitionRejected(
                "HUMAN Critic Selection already recorded."
            )

        if not isinstance(decisions, list) or not decisions:
            raise TransitionRejected(
                "HUMAN Critic Selection requires explicit decisions."
            )

        expected_ids = {
            entry.criticism.criticism_id
            for entry in space.entries
            if entry.criticism is not None
        }

        normalized: list[dict[str, str]] = []
        supplied_ids: list[str] = []

        optional_fields = (
            "reason",
            "human_observation",
            "verification_performed",
            "source_consulted",
            "identified_limit",
            "required_change",
            "integration_condition",
            "link_to_human_idea",
            "risk_position",
        )

        for index, item in enumerate(decisions, start=1):
            if not isinstance(item, dict):
                raise TransitionRejected(
                    f"HUMAN decision {index} must be a mapping."
                )

            criticism_id = item.get("criticism_id")
            decision = item.get("decision")

            if not isinstance(criticism_id, str) or not criticism_id.strip():
                raise TransitionRejected(
                    f"HUMAN decision {index} requires criticism_id."
                )

            if not isinstance(decision, str) or not decision.strip():
                raise TransitionRejected(
                    f"HUMAN decision {index} requires an explicit decision."
                )

            criticism_id = criticism_id.strip()
            decision = decision.strip().upper()

            if decision not in HUMAN_CRITIC_DECISIONS:
                raise TransitionRejected(
                    f"Invalid HUMAN Critic decision: {decision}."
                )

            clean: dict[str, str] = {
                "criticism_id": criticism_id,
                "decision": decision,
            }

            for field_name in optional_fields:
                value = item.get(field_name, "")
                if value is None:
                    value = ""
                if not isinstance(value, str):
                    raise TransitionRejected(
                        f"HUMAN decision field {field_name} must be text."
                    )
                clean[field_name] = value

            supplied_ids.append(criticism_id)
            normalized.append(clean)

        if len(supplied_ids) != len(set(supplied_ids)):
            raise TransitionRejected(
                "Each criticism may receive only one HUMAN decision."
            )

        supplied_set = set(supplied_ids)

        if supplied_set != expected_ids:
            missing = sorted(expected_ids - supplied_set)
            unknown = sorted(supplied_set - expected_ids)
            raise TransitionRejected(
                "Every criticism requires an explicit HUMAN decision; "
                f"missing={missing}, unknown={unknown}."
            )

        decision_records = tuple(
            HumanCriticDecision(
                decision_id=str(uuid4()),
                space_id=space.space_id,
                criticism_id=item["criticism_id"],
                decision=item["decision"],
                reason=item["reason"],
                human_observation=item["human_observation"],
                verification_performed=item["verification_performed"],
                source_consulted=item["source_consulted"],
                identified_limit=item["identified_limit"],
                required_change=item["required_change"],
                integration_condition=item["integration_condition"],
                link_to_human_idea=item["link_to_human_idea"],
                risk_position=item["risk_position"],
                actor=Actor.HUMAN.value,
                created_revision=self.revision,
            )
            for item in normalized
        )

        selection = HumanCriticSelection(
            selection_id=str(uuid4()),
            space_id=space.space_id,
            session_id=self.session_id,
            decisions=decision_records,
            actor=Actor.HUMAN.value,
            created_revision=self.revision,
        )

        self.human_critic_selection_artifact = selection
        self.human_critic_selection_history.append(selection)

        return selection

    def _vf_final_integrity_allows_locking(
        self,
        source: S,
        target: S,
    ) -> bool:
        if not (
            source is S.VF_DECLARED
            and target is S.VF_LOCKING_IN_PROGRESS
        ):
            return True

        result = self.vf_final_integrity_result

        return (
            result is not None
            and self.vf_final_integrity_revision == self.revision
            and result.checked_revision == self.revision
            and result.declaration_persisted
            and result.actor_persisted
            and result.moment_persisted
            and result.provenance_persisted
            and result.selected_version_bound
            and result.no_unresolved_technical_error
        )

    def _final_report_allows_ready(
        self,
        source: S,
        target: S,
    ) -> bool:
        if not (
            source is S.FINAL_REPORT_GENERATION
            and target is S.FINAL_REPORT_READY
        ):
            return True

        report = self.final_report

        if (
            report is None
            or self.final_report_revision != self.revision
            or self.session_id is None
            or self.vf_locked_version_id is None
            or self.vf_locked_content_hash is None
        ):
            return False

        selected = self.result_versions.get(
            self.vf_locked_version_id
        )

        if selected is None:
            return False

        from hashlib import sha256

        actual_content_hash = sha256(
            selected.content.encode("utf-8")
        ).hexdigest()

        return (
            report.session_id == self.session_id
            and report.vf_version_id == self.vf_locked_version_id
            and report.vf_content_hash == self.vf_locked_content_hash
            and report.generated_revision == self.revision
            and selected.session_id == self.session_id
            and selected.version_id == report.vf_version_id
            and selected.version_label == report.vf_version_label
            and selected.content == report.vf_content
            and selected.content_hash == report.vf_content_hash
            and actual_content_hash == selected.content_hash
        )

    def record_final_report(
        self,
        *,
        actor: Actor,
        revision_response: str | None = None,
    ) -> FinalReport:
        if self.state is not S.FINAL_REPORT_GENERATION:
            raise TransitionRejected(
                "Final report can only be generated in "
                "FINAL_REPORT_GENERATION."
            )

        if actor is not Actor.SYSTEM:
            raise TransitionRejected(
                "Final report generation requires SYSTEM actor."
            )

        if self.final_report_revision == self.revision:
            raise TransitionRejected(
                "Final report is already recorded for this revision."
            )

        if (
            self.session_id is None
            or self.vf_locked_version_id is None
            or self.vf_locked_content_hash is None
        ):
            raise TransitionRejected(
                "Final report requires a locked VF artifact."
            )

        declaration = self.vf_human_declaration
        integrity = self.vf_final_integrity_result

        if (
            declaration is None
            or self.vf_human_declaration_revision is None
        ):
            raise TransitionRejected(
                "Final report requires the persisted HUMAN VF declaration."
            )

        if (
            integrity is None
            or self.vf_final_integrity_revision is None
        ):
            raise TransitionRejected(
                "Final report requires the persisted final integrity result."
            )

        if not (
            integrity.declaration_persisted
            and integrity.actor_persisted
            and integrity.moment_persisted
            and integrity.provenance_persisted
            and integrity.selected_version_bound
            and integrity.no_unresolved_technical_error
        ):
            raise TransitionRejected(
                "Final report requires a complete positive final integrity result."
            )

        selected = self.result_versions.get(
            self.vf_locked_version_id
        )

        if selected is None:
            raise TransitionRejected(
                "Locked VF ResultVersion is not available."
            )

        from hashlib import sha256

        actual_content_hash = sha256(
            selected.content.encode("utf-8")
        ).hexdigest()

        if not (
            selected.session_id == self.session_id
            and selected.version_id == self.vf_locked_version_id
            and selected.version_id == declaration.selected_version_id
            and selected.version_label == declaration.selected_version
            and selected.content_hash == self.vf_locked_content_hash
            and selected.content_hash
            == declaration.selected_version_content_hash
            and actual_content_hash == selected.content_hash
        ):
            raise TransitionRejected(
                "Final report source does not match the exact locked "
                "HUMAN-selected VF artifact."
            )

        ordered_versions = sorted(
            (
                result
                for result in self.result_versions.values()
                if result.session_id == self.session_id
            ),
            key=lambda result: (
                result.created_revision,
                result.version_label,
                result.version_id,
            ),
        )

        version_path = tuple(
            f"{result.version_label}:{result.version_id}"
            for result in ordered_versions
        )

        memory_effect_evidence = tuple(
            (
                f"{evidence.memory_selection_item_id}|"
                f"{evidence.outcome}|"
                f"{evidence.reason}|"
                f"revision={evidence.verified_revision}"
            )
            for evidence in self.memory_effect_verifications
        )

        review_basis = None
        supersedes_report_version = None
        normalized_revision_response = None

        if self.final_report is not None:
            review_basis = self.final_report_review

            if (
                review_basis is None
                or self.final_report_review_revision != self.revision - 1
                or review_basis.reviewed_revision != self.revision - 1
                or review_basis.report_version
                != self.final_report.report_version
                or review_basis.report_generated_revision
                != self.final_report.generated_revision
                or review_basis.outcome not in {
                    "CORRECTED",
                    "CONTESTED",
                }
            ):
                raise TransitionRejected(
                    "Revised FinalReport requires the immediately prior "
                    "HUMAN CORRECTED or CONTESTED review."
                )

            normalized_revision_response = (
                revision_response or ""
            ).strip()

            if not normalized_revision_response:
                raise TransitionRejected(
                    "Revised FinalReport requires a non-empty SYSTEM "
                    "response to the HUMAN review."
                )

            supersedes_report_version = (
                self.final_report.report_version
            )

        elif revision_response is not None and revision_response.strip():
            raise TransitionRejected(
                "Initial FinalReport cannot carry a revision response "
                "without a prior HUMAN review."
            )

        report = FinalReport(
            report_version=len(self.final_reports) + 1,
            session_id=self.session_id,
            vf_version_id=selected.version_id,
            vf_version_label=selected.version_label,
            vf_content_hash=selected.content_hash,
            vf_content=selected.content,
            version_path=version_path,
            choice_reason=declaration.choice_reason,
            relation_to_initial_direction=(
                declaration.relation_to_initial_direction
            ),
            decisive_human_contribution=(
                declaration.decisive_human_contribution
            ),
            integrated_builder_elements=(
                declaration.integrated_builder_elements
            ),
            decisive_critics=declaration.decisive_critics,
            rejected_critics=declaration.rejected_critics,
            memory_basis=declaration.memory_basis,
            memory_effect_evidence=memory_effect_evidence,
            verifications_performed=(
                declaration.verifications_performed
            ),
            remaining_risks_and_uncertainties=(
                declaration.remaining_risks_and_uncertainties
            ),
            preserved_contradictions=(
                declaration.preserved_contradictions
            ),
            intended_use=declaration.intended_use,
            decision_assumption=declaration.decision_assumption,
            declaration_persisted=integrity.declaration_persisted,
            actor_persisted=integrity.actor_persisted,
            moment_persisted=integrity.moment_persisted,
            provenance_persisted=integrity.provenance_persisted,
            selected_version_bound=integrity.selected_version_bound,
            no_unresolved_technical_error=(
                integrity.no_unresolved_technical_error
            ),
            integrity_reasons=integrity.reason,
            supersedes_report_version=supersedes_report_version,
            human_review_basis_outcome=(
                review_basis.outcome
                if review_basis is not None
                else None
            ),
            human_review_basis_note=(
                review_basis.review_note
                if review_basis is not None
                else None
            ),
            revision_response=normalized_revision_response,
            human_declaration_revision=(
                self.vf_human_declaration_revision
            ),
            integrity_checked_revision=integrity.checked_revision,
            generated_revision=self.revision,
        )

        self.final_reports.append(report)
        self.final_report = report
        self.final_report_revision = self.revision

        return report

    def _final_report_review_allows_regeneration(
        self,
        source: S,
        target: S,
    ) -> bool:
        if not (
            source is S.FINAL_REPORT_READY
            and target is S.FINAL_REPORT_GENERATION
        ):
            return True

        review = self.final_report_review
        report = self.final_report

        if (
            review is None
            or report is None
            or self.final_report_review_revision != self.revision
        ):
            return False

        return (
            review.report_version == report.report_version
            and review.report_generated_revision
            == report.generated_revision
            and review.reviewed_revision == self.revision
            and review.outcome in {
                "CORRECTED",
                "CONTESTED",
            }
        )

    def _final_report_review_allows_archive(
        self,
        source: S,
        target: S,
    ) -> bool:
        if not (
            source is S.FINAL_REPORT_READY
            and target is S.SESSION_ARCHIVED
        ):
            return True

        review = self.final_report_review
        report = self.final_report

        if (
            review is None
            or report is None
            or self.final_report_review_revision != self.revision
        ):
            return False

        return (
            review.report_version == report.report_version
            and review.report_generated_revision == report.generated_revision
            and review.reviewed_revision == self.revision
            and review.outcome == "CONFIRMED"
        )

    def record_final_report_review(
        self,
        *,
        outcome: str,
        review_note: str,
        actor: Actor,
    ) -> FinalReportReview:
        if self.state is not S.FINAL_REPORT_READY:
            raise TransitionRejected(
                "Final report review requires FINAL_REPORT_READY."
            )

        if actor is not Actor.HUMAN:
            raise TransitionRejected(
                "Final report review requires HUMAN actor."
            )

        report = self.final_report

        if report is None:
            raise TransitionRejected(
                "Final report review requires an existing FinalReport."
            )

        if self.final_report_review_revision == self.revision:
            raise TransitionRejected(
                "Final report review is already recorded for this revision."
            )

        normalized_outcome = outcome.strip().upper()

        if normalized_outcome not in {
            "CONFIRMED",
            "CORRECTED",
            "CONTESTED",
        }:
            raise TransitionRejected(
                "Final report review outcome must be "
                "CONFIRMED, CORRECTED, or CONTESTED."
            )

        normalized_note = review_note.strip()

        if not normalized_note:
            raise TransitionRejected(
                "Final report review requires a non-empty HUMAN review note."
            )

        review = FinalReportReview(
            report_version=report.report_version,
            outcome=normalized_outcome,
            review_note=normalized_note,
            report_generated_revision=report.generated_revision,
            reviewed_revision=self.revision,
        )

        self.final_report_reviews.append(review)
        self.final_report_review = review
        self.final_report_review_revision = self.revision

        return review

    def _vf_selected_result_allows_locked(
        self,
        source: S,
        target: S,
    ) -> bool:
        if not (
            source is S.VF_LOCKING_IN_PROGRESS
            and target is S.VF_LOCKED
        ):
            return True

        declaration = self.vf_human_declaration

        if declaration is None or self.session_id is None:
            return False

        selected = self.result_versions.get(
            declaration.selected_version_id
        )

        if selected is None:
            return False

        from hashlib import sha256

        actual_content_hash = sha256(
            selected.content.encode("utf-8")
        ).hexdigest()

        return (
            selected.session_id == self.session_id
            and selected.version_id
            == declaration.selected_version_id
            and selected.version_label
            == declaration.selected_version
            and selected.content_hash
            == declaration.selected_version_content_hash
            and actual_content_hash
            == selected.content_hash
        )


    def _vf_human_declaration_allows_declared(
        self,
        source: S,
        target: S,
    ) -> bool:
        if not (
            source is S.VF_HUMAN_DECLARATION
            and target is S.VF_DECLARED
        ):
            return True

        return (
            self.vf_human_declaration is not None
            and self.vf_human_declaration_revision == self.revision
            and self.vf_human_declaration.declared_revision == self.revision
        )

    def _vf_precheck_transition_allowed(
        self,
        source: S,
        target: S,
    ) -> bool:
        if source is not S.VF_PRECHECK_REQUIRED:
            return True

        return (
            self.vf_precheck_revision == self.revision
            and self.vf_precheck_target is not None
            and target is self.vf_precheck_target
        )

    def can_transition(
        self,
        target: S,
        actor: Actor,
    ) -> bool:
        if not is_static_transition_allowed(self.state, target):
            return False

        if (
            (self.state, target) in HUMAN_AUTHORITY_TRANSITIONS
            and actor is not Actor.HUMAN
        ):
            return False

        required_actor = AGENT_OWNED_TRANSITIONS.get((self.state, target))
        if required_actor is not None and actor is not required_actor:
            return False

        if self.state is S.MEMORY_RETRIEVAL_RUNNING:
            if (
                target is S.MEMORY_REVIEW_REQUIRED
                and self.retrieval_outcome != RETRIEVAL_CANDIDATES_FOUND
            ):
                return False

            if (
                target is S.NO_RELEVANT_MEMORY
                and self.retrieval_outcome
                != RETRIEVAL_NO_RELEVANT_CANDIDATE_FOUND
            ):
                return False

            if (
                target is S.MEMORY_RETRIEVAL_FAILED
                and self.retrieval_outcome != RETRIEVAL_TECHNICAL_ERROR
            ):
                return False

        if (
            self.state is S.MEMORY_REVIEW_REQUIRED
            and target is S.NO_RELEVANT_MEMORY
            and self.retrieval_outcome != RETRIEVAL_CANDIDATES_FOUND
        ):
            return False

        if not self._vf_final_integrity_allows_locking(
            self.state,
            target,
        ):
            return False

        if not self._vf_selected_result_allows_locked(
            self.state,
            target,
        ):
            return False

        if not self._vf_human_declaration_allows_declared(
            self.state,
            target,
        ):
            return False

        if not self._vf_precheck_transition_allowed(
            self.state,
            target,
        ):
            return False

        if not self._final_report_allows_ready(
            self.state,
            target,
        ):
            return False

        if not self._final_report_review_allows_archive(
            self.state,
            target,
        ):
            return False

        if not self._final_report_review_allows_regeneration(
            self.state,
            target,
        ):
            return False

        return True

    def record_result_version(
        self,
        *,
        session_id: str,
        version_label: str,
        content: str,
        actor: Actor,
    ) -> ResultVersion:
        from hashlib import sha256
        from uuid import UUID, uuid4

        if self.state not in {S.V1_GENERATED, S.VN_GENERATED}:
            raise TransitionRejected(
                "Result version can only be recorded after Builder generation."
            )

        if actor is not Actor.BUILDER_AI:
            raise TransitionRejected(
                "Result version requires BUILDER_AI actor."
            )

        try:
            normalized_session_id = str(UUID(session_id.strip()))
        except (ValueError, AttributeError):
            raise TransitionRejected(
                "Result version requires a valid session UUID."
            )

        label = version_label.strip()
        if not label:
            raise TransitionRejected(
                "Result version requires a version label."
            )

        if not content.strip():
            raise TransitionRejected(
                "Result version requires non-empty content."
            )

        if self.session_id is None:
            self.session_id = normalized_session_id
        elif self.session_id != normalized_session_id:
            raise TransitionRejected(
                "Result version session UUID does not match orchestrator session."
            )

        if any(
            version.version_label == label
            for version in self.result_versions.values()
        ):
            raise TransitionRejected(
                "Result version label already exists in this session."
            )

        version_id = str(uuid4())
        content_hash = sha256(content.encode("utf-8")).hexdigest()

        result = ResultVersion(
            version_id=version_id,
            session_id=normalized_session_id,
            version_label=label,
            content=content,
            content_hash=content_hash,
            status="VERSION_GENERATED",
            created_revision=self.revision,
        )

        self.result_versions[version_id] = result
        return result

    def record_vf_final_integrity_result(
        self,
        *,
        declaration_persisted: bool,
        actor_persisted: bool,
        moment_persisted: bool,
        provenance_persisted: bool,
        selected_version_bound: bool,
        no_unresolved_technical_error: bool,
        reason: str,
        actor: Actor,
    ) -> None:
        if self.state is not S.VF_DECLARED:
            raise TransitionRejected(
                "VF final integrity check requires VF_DECLARED."
            )

        if actor is not Actor.SYSTEM:
            raise TransitionRejected(
                "VF final integrity check requires SYSTEM actor."
            )

        if self.vf_final_integrity_revision == self.revision:
            raise TransitionRejected(
                "VF final integrity result is already recorded for this revision."
            )

        if not reason.strip():
            raise TransitionRejected(
                "VF final integrity result requires a reason."
            )

        self.vf_final_integrity_result = VFFinalIntegrityResult(
            declaration_persisted=declaration_persisted,
            actor_persisted=actor_persisted,
            moment_persisted=moment_persisted,
            provenance_persisted=provenance_persisted,
            selected_version_bound=selected_version_bound,
            no_unresolved_technical_error=no_unresolved_technical_error,
            reason=reason.strip(),
            checked_revision=self.revision,
        )
        self.vf_final_integrity_revision = self.revision

    def record_vf_human_declaration(
        self,
        *,
        selected_version: str,
        choice_reason: str,
        relation_to_initial_direction: str,
        decisive_human_contribution: str,
        integrated_builder_elements: str,
        decisive_critics: str,
        rejected_critics: str,
        memory_basis: str,
        verifications_performed: str,
        remaining_risks_and_uncertainties: str,
        preserved_contradictions: str,
        intended_use: str,
        decision_assumption: str,
        actor: Actor,
    ) -> None:
        if self.state is not S.VF_HUMAN_DECLARATION:
            raise TransitionRejected(
                "VF human declaration requires VF_HUMAN_DECLARATION."
            )

        if actor is not Actor.HUMAN:
            raise TransitionRejected(
                "VF human declaration requires HUMAN actor."
            )

        if self.vf_human_declaration_revision == self.revision:
            raise TransitionRejected(
                "VF human declaration is already recorded for this revision."
            )

        values = {
            "selected_version": selected_version,
            "choice_reason": choice_reason,
            "relation_to_initial_direction": relation_to_initial_direction,
            "decisive_human_contribution": decisive_human_contribution,
            "integrated_builder_elements": integrated_builder_elements,
            "decisive_critics": decisive_critics,
            "rejected_critics": rejected_critics,
            "memory_basis": memory_basis,
            "verifications_performed": verifications_performed,
            "remaining_risks_and_uncertainties": remaining_risks_and_uncertainties,
            "preserved_contradictions": preserved_contradictions,
            "intended_use": intended_use,
            "decision_assumption": decision_assumption,
        }

        missing = [
            name
            for name, value in values.items()
            if not isinstance(value, str) or not value.strip()
        ]

        if missing:
            raise TransitionRejected(
                "VF human declaration missing required fields: "
                + ", ".join(sorted(missing))
            )

        selected_version_label = selected_version.strip()

        matching_versions = [
            version
            for version in self.result_versions.values()
            if version.version_label == selected_version_label
        ]

        if len(matching_versions) != 1:
            raise TransitionRejected(
                "VF selected_version must resolve to exactly one recorded "
                "ResultVersion."
            )

        selected_result_version = matching_versions[0]

        if (
            self.session_id is None
            or selected_result_version.session_id != self.session_id
        ):
            raise TransitionRejected(
                "VF selected_version must belong to the orchestrator session."
            )

        self.vf_human_declaration = VFHumanDeclaration(
            selected_version=selected_version_label,
            selected_version_id=selected_result_version.version_id,
            selected_version_content_hash=selected_result_version.content_hash,
            choice_reason=choice_reason.strip(),
            relation_to_initial_direction=relation_to_initial_direction.strip(),
            decisive_human_contribution=decisive_human_contribution.strip(),
            integrated_builder_elements=integrated_builder_elements.strip(),
            decisive_critics=decisive_critics.strip(),
            rejected_critics=rejected_critics.strip(),
            memory_basis=memory_basis.strip(),
            verifications_performed=verifications_performed.strip(),
            remaining_risks_and_uncertainties=remaining_risks_and_uncertainties.strip(),
            preserved_contradictions=preserved_contradictions.strip(),
            intended_use=intended_use.strip(),
            decision_assumption=decision_assumption.strip(),
            declared_revision=self.revision,
        )
        self.vf_human_declaration_revision = self.revision

    def generate_version_comparison(
        self,
        *,
        base_version_id: str,
        candidate_version_id: str,
        actor: Actor,
    ) -> VersionComparison:
        from difflib import unified_diff
        from hashlib import sha256
        from uuid import uuid4

        if actor is not Actor.ORCHESTRATOR:
            raise TransitionRejected(
                "Version Comparison requires ORCHESTRATOR actor."
            )

        if self.state not in {
            S.VN_GENERATED,
            S.VERSION_COMPARISON_READY,
        }:
            raise TransitionRejected(
                "Version Comparison requires VN_GENERATED or "
                "VERSION_COMPARISON_READY."
            )

        base = self.result_versions.get(base_version_id)
        candidate = self.result_versions.get(candidate_version_id)

        if base is None or candidate is None:
            raise TransitionRejected(
                "Version Comparison requires two persisted ResultVersions."
            )

        if base.session_id != self.session_id:
            raise TransitionRejected(
                "Base ResultVersion does not belong to this session."
            )

        if candidate.session_id != self.session_id:
            raise TransitionRejected(
                "Candidate ResultVersion does not belong to this session."
            )

        if base.version_id == candidate.version_id:
            raise TransitionRejected(
                "Version Comparison requires distinct ResultVersions."
            )

        if base.version_label != "V1":
            raise TransitionRejected(
                "Canonical Version Comparison base must be V1."
            )

        if candidate.version_label == "V1":
            raise TransitionRejected(
                "Version Comparison candidate must be a reconstructed Vn."
            )

        base_hash = sha256(
            base.content.encode("utf-8")
        ).hexdigest()

        candidate_hash = sha256(
            candidate.content.encode("utf-8")
        ).hexdigest()

        if base_hash != base.content_hash:
            raise TransitionRejected(
                "Canonical V1 content hash integrity check failed."
            )

        if candidate_hash != candidate.content_hash:
            raise TransitionRejected(
                "Candidate Vn content hash integrity check failed."
            )

        if self.state is S.VN_GENERATED:
            self.transition(
                S.VERSION_COMPARISON_READY,
                Actor.ORCHESTRATOR,
                reason=(
                    "ORCHESTRATOR opens deterministic Version Comparison."
                ),
            )

        diff_text = "".join(
            unified_diff(
                base.content.splitlines(keepends=True),
                candidate.content.splitlines(keepends=True),
                fromfile=base.version_label,
                tofile=candidate.version_label,
            )
        )

        comparison = VersionComparison(
            comparison_id=str(uuid4()),
            session_id=self.session_id,
            base_version_id=base.version_id,
            base_version_label=base.version_label,
            base_content_hash=base.content_hash,
            candidate_version_id=candidate.version_id,
            candidate_version_label=candidate.version_label,
            candidate_content_hash=candidate.content_hash,
            content_changed=(base.content != candidate.content),
            unified_diff=diff_text,
            status="GENERATED",
            generated_revision=self.revision,
        )

        self.version_comparison_artifact = comparison
        self.version_comparison_history.append(comparison)

        self.transition(
            S.VERSION_COMPARISON_GENERATED,
            Actor.ORCHESTRATOR,
            reason=(
                "Deterministic Version Comparison persisted for exact "
                f"{base.version_label} -> {candidate.version_label}."
            ),
        )

        self.transition(
            S.HUMAN_VERIFICATION_REQUIRED,
            Actor.ORCHESTRATOR,
            reason=(
                "Version Comparison generated; HUMAN verification required."
            ),
        )

        return comparison

    def record_human_verification(
        self,
        *,
        comparison_id: str,
        candidate_version_id: str,
        candidate_content_hash: str,
        evidence_sufficient: bool,
        verification_note: str,
        actor: Actor,
    ) -> HumanVerification:
        from hashlib import sha256
        from uuid import uuid4

        if self.state is not S.HUMAN_VERIFICATION_REQUIRED:
            raise TransitionRejected(
                "Human Verification requires HUMAN_VERIFICATION_REQUIRED."
            )

        if actor is not Actor.HUMAN:
            raise TransitionRejected(
                "Human Verification requires HUMAN actor."
            )

        if not verification_note.strip():
            raise TransitionRejected(
                "Human Verification requires an explicit HUMAN note."
            )

        comparison = self.version_comparison_artifact

        if comparison is None:
            raise TransitionRejected(
                "Human Verification requires a persisted Version Comparison."
            )

        if comparison.status != "GENERATED":
            raise TransitionRejected(
                "Human Verification requires a generated Version Comparison."
            )

        if comparison.comparison_id != comparison_id:
            raise TransitionRejected(
                "Human Verification comparison_id mismatch."
            )

        if comparison.candidate_version_id != candidate_version_id:
            raise TransitionRejected(
                "Human Verification candidate version mismatch."
            )

        if comparison.candidate_content_hash != candidate_content_hash:
            raise TransitionRejected(
                "Human Verification candidate hash mismatch."
            )

        candidate = self.result_versions.get(candidate_version_id)

        if candidate is None:
            raise TransitionRejected(
                "Human Verification candidate ResultVersion is missing."
            )

        live_hash = sha256(
            candidate.content.encode("utf-8")
        ).hexdigest()

        if (
            candidate.content_hash != candidate_content_hash
            or live_hash != candidate_content_hash
        ):
            raise TransitionRejected(
                "Human Verification candidate integrity check failed."
            )

        verification = HumanVerification(
            verification_id=str(uuid4()),
            session_id=self.session_id,
            comparison_id=comparison.comparison_id,
            candidate_version_id=candidate.version_id,
            candidate_version_label=candidate.version_label,
            candidate_content_hash=candidate.content_hash,
            evidence_sufficient=bool(evidence_sufficient),
            verification_note=verification_note.strip(),
            verified_by=Actor.HUMAN.value,
            status=(
                "VERIFIED"
                if evidence_sufficient
                else "EVIDENCE_INSUFFICIENT"
            ),
            verified_revision=self.revision,
        )

        self.human_verification_artifact = verification
        self.human_verification_history.append(verification)

        if evidence_sufficient:
            self.transition(
                S.VF_PRECHECK_REQUIRED,
                Actor.HUMAN,
                reason=(
                    "HUMAN verified the exact compared Vn and authorized "
                    "VF technical precheck."
                ),
            )

        return verification

    def record_vf_precheck_result(
        self,
        *,
        code: str,
        actor: Actor,
        condition: str = "",
        reason: str = "",
    ) -> None:
        if self.state is not S.VF_PRECHECK_REQUIRED:
            raise TransitionRejected(
                "VF precheck result requires VF_PRECHECK_REQUIRED."
            )

        if actor is not Actor.SYSTEM:
            raise TransitionRejected(
                "VF precheck result requires SYSTEM actor."
            )

        if code == VF_PRECHECK_OK:
            from hashlib import sha256

            comparison = self.version_comparison_artifact
            verification = self.human_verification_artifact

            if comparison is None:
                raise TransitionRejected(
                    "VF_PRECHECK_OK requires persisted Version Comparison."
                )

            if verification is None:
                raise TransitionRejected(
                    "VF_PRECHECK_OK requires persisted HUMAN Verification."
                )

            if comparison.status != "GENERATED":
                raise TransitionRejected(
                    "VF_PRECHECK_OK requires generated Version Comparison."
                )

            if (
                verification.status != "VERIFIED"
                or not verification.evidence_sufficient
            ):
                raise TransitionRejected(
                    "VF_PRECHECK_OK requires sufficient HUMAN Verification."
                )

            if verification.verified_by != Actor.HUMAN.value:
                raise TransitionRejected(
                    "VF_PRECHECK_OK requires HUMAN-owned verification."
                )

            if verification.comparison_id != comparison.comparison_id:
                raise TransitionRejected(
                    "VF_PRECHECK_OK comparison/verification binding failed."
                )

            if (
                verification.candidate_version_id
                != comparison.candidate_version_id
            ):
                raise TransitionRejected(
                    "VF_PRECHECK_OK candidate version binding failed."
                )

            if (
                verification.candidate_content_hash
                != comparison.candidate_content_hash
            ):
                raise TransitionRejected(
                    "VF_PRECHECK_OK candidate hash binding failed."
                )

            candidate = self.result_versions.get(
                comparison.candidate_version_id
            )

            if candidate is None:
                raise TransitionRejected(
                    "VF_PRECHECK_OK candidate ResultVersion is missing."
                )

            live_hash = sha256(
                candidate.content.encode("utf-8")
            ).hexdigest()

            if (
                candidate.content_hash
                != comparison.candidate_content_hash
                or live_hash
                != comparison.candidate_content_hash
            ):
                raise TransitionRejected(
                    "VF_PRECHECK_OK candidate integrity check failed."
                )

        if self.session_mode not in VALID_SESSION_MODES:
            raise TransitionRejected(
                "VF precheck requires an explicit valid session_mode."
            )

        if self.session_mode == SESSION_MODE_TECHNICAL_TEST:
            if code != MODE_NOT_ELIGIBLE_FOR_VF:
                raise TransitionRejected(
                    "TECHNICAL_TEST requires MODE_NOT_ELIGIBLE_FOR_VF."
                )
            if not condition.strip() or not reason.strip():
                raise TransitionRejected(
                    "MODE_NOT_ELIGIBLE_FOR_VF requires condition and reason."
                )

            self.vf_precheck_code = code
            self.vf_precheck_condition = condition.strip()
            self.vf_precheck_target = None
            self.vf_precheck_reason = reason.strip()
            self.vf_precheck_revision = self.revision
            return

        if code == MODE_NOT_ELIGIBLE_FOR_VF:
            raise TransitionRejected(
                "MODE_NOT_ELIGIBLE_FOR_VF is reserved for TECHNICAL_TEST."
            )

        target = VF_PRECHECK_TARGET_BY_CODE.get(code)
        if target is None:
            raise TransitionRejected(
                f"Unknown VF precheck code: {code}"
            )

        if (
            code == VF_PRECHECK_OK
            and self.session_mode == SESSION_MODE_DEMO_PROTOCOL
            and not self._has_demo_positive_memory_evidence()
        ):
            raise TransitionRejected(
                "DEMO_PROTOCOL requires positive memory evidence "
                "before VF_PRECHECK_OK."
            )

        if code != VF_PRECHECK_OK:
            if not condition.strip() or not reason.strip():
                raise TransitionRejected(
                    "Failed VF precheck requires condition and reason."
                )

        self.vf_precheck_code = code
        self.vf_precheck_condition = (
            condition.strip()
            if condition.strip()
            else "ALL_CANONICAL_CONDITIONS_SATISFIED"
        )
        self.vf_precheck_target = target
        self.vf_precheck_reason = reason.strip()
        self.vf_precheck_revision = self.revision


    def _manual_transfer_source_artifacts(self) -> tuple[object, ...]:
        names = (
            "human_direction_artifact",
            "human_response_artifact",
            "critic_review_artifact",
            "conflict_space_artifact",
            "human_critic_selection_artifact",
        )
        return tuple(
            artifact
            for name in names
            if (artifact := getattr(self, name, None)) is not None
        )

    def _manual_transfer_source_version_id(self) -> str:
        versions = getattr(self, "result_versions", {}) or {}

        candidates = []
        if isinstance(versions, dict):
            if "V1" in versions:
                candidates.append(versions["V1"])
            candidates.extend(
                value
                for key, value in versions.items()
                if key != "V1"
            )

        for candidate in candidates:
            data = _hv_manual_transfer_as_data(candidate)
            if not isinstance(data, dict):
                continue

            label = _hv_manual_transfer_scalar(
                data.get("version_label")
                or data.get("label")
                or data.get("version")
            )
            if label and label != "V1":
                continue

            for key in (
                "version_id",
                "result_version_id",
                "version_uuid",
                "id",
            ):
                value = _hv_manual_transfer_scalar(data.get(key))
                if value:
                    return value

        return ""

    def _manual_transfer_validate_source(
        self,
        *,
        source_object_type: str,
        source_object_id: str,
        source_actor_type: str,
        original_content: str,
        selected_fragment: str,
        conditions: str,
    ) -> None:
        source_type = source_object_type.strip().upper()

        allowed_source_types = {
            "HUMAN_DIRECTION",
            "HUMAN_COGNITIVE_RESPONSE",
            "CRITICISM",
            "CONFLICT",
            "HUMAN_SELECTION",
            "VERIFICATION_RESULT",
        }

        if source_type not in allowed_source_types:
            raise TransitionRejected(
                f"Manual Transfer source type {source_type!r} is not authorized."
            )

        if "MEMORY" in source_type:
            raise TransitionRejected(
                "Memory cannot enter the preliminary Manual Transfer package."
            )

        artifacts = self._manual_transfer_source_artifacts()
        source_containers: list[dict] = []

        for artifact in artifacts:
            data = _hv_manual_transfer_as_data(artifact)
            source_containers.extend(
                _hv_manual_transfer_find_id_containers(
                    data,
                    source_object_id,
                )
            )

        if not source_containers:
            raise TransitionRejected(
                "Manual Transfer source object is not present in canonical artifacts."
            )

        source_strings: set[str] = set()
        for container in source_containers:
            source_strings.update(
                _hv_manual_transfer_collect_strings(container)
            )

        if original_content not in source_strings:
            raise TransitionRejected(
                "Manual Transfer original content does not match the canonical source."
            )

        if selected_fragment not in original_content:
            raise TransitionRejected(
                "Selected fragment must be contained in the original content."
            )

        actor_value = source_actor_type.strip()
        actor_variants = {
            actor_value,
            actor_value.upper(),
            f"Actor.{actor_value.upper()}",
        }

        if not actor_variants.intersection(source_strings):
            # Conflict Space can legitimately preserve positions from
            # multiple actors. For all other objects provenance must be
            # directly observable in the source container.
            if source_type != "CONFLICT":
                raise TransitionRejected(
                    "Manual Transfer source actor/provenance does not match "
                    "the canonical source."
                )

        if source_type == "CRITICISM":
            selection = getattr(
                self,
                "human_critic_selection_artifact",
                None,
            )
            if selection is None:
                raise TransitionRejected(
                    "Criticism cannot transfer without HUMAN selection."
                )

            selection_data = _hv_manual_transfer_as_data(selection)
            decision_containers = (
                _hv_manual_transfer_find_id_containers(
                    selection_data,
                    source_object_id,
                )
            )

            if not decision_containers:
                raise TransitionRejected(
                    "Criticism is not covered by the current HUMAN selection."
                )

            decisions = set()
            for container in decision_containers:
                for key in ("decision", "status", "selection"):
                    if key in container:
                        decisions.add(
                            _hv_manual_transfer_scalar(
                                container[key]
                            ).upper()
                        )

            transferable = {
                "ACCEPTED",
                "PARTIALLY_ACCEPTED",
                "TRANSFER_APPROVED",
                "KEEP_AS_UNRESOLVED",
                "NEEDS_EXTERNAL_VERIFICATION",
            }

            if not decisions.intersection(transferable):
                raise TransitionRejected(
                    "Criticism is not HUMAN-authorized for preliminary transfer."
                )

            if (
                "NEEDS_EXTERNAL_VERIFICATION" in decisions
                and not conditions.strip()
            ):
                raise TransitionRejected(
                    "Externally unverified criticism requires a transfer condition."
                )

    def _manual_transfer_validate_integrity(
        self,
        package: ManualTransferPackage,
    ) -> None:
        if not package.items:
            raise TransitionRejected(
                "Manual Transfer package cannot be empty."
            )

        for item in package.items:
            expected = _hv_manual_transfer_item_hash(item)
            if item.content_hash != expected:
                raise TransitionRejected(
                    f"Manual Transfer item integrity failed: {item.item_id}"
                )

        expected_package_hash = _hv_manual_transfer_package_hash(
            package
        )
        if package.content_hash != expected_package_hash:
            raise TransitionRejected(
                "Manual Transfer package integrity check failed."
            )

    def open_manual_transfer(
        self,
        actor: Actor,
    ) -> None:
        if actor is not Actor.HUMAN:
            raise TransitionRejected(
                "Only HUMAN can enter Manual Transfer editing."
            )
        if self.state is not S.MANUAL_TRANSFER_PREPARATION:
            raise TransitionRejected(
                "Manual Transfer can start only from "
                "MANUAL_TRANSFER_PREPARATION."
            )

        self.transition(
            S.MANUAL_TRANSFER_IN_PROGRESS,
            actor,
        )

    def build_manual_transfer_package(
        self,
        *,
        actor: Actor,
        items: list[dict],
        source_version_id: str = "",
        target_version_label: str = "V2",
        branch_id: str = "",
        cycle_id: str = "",
    ) -> ManualTransferPackage:
        if actor is not Actor.HUMAN:
            raise TransitionRejected(
                "Only HUMAN can construct the Manual Transfer package."
            )

        if self.state is not S.MANUAL_TRANSFER_IN_PROGRESS:
            raise TransitionRejected(
                "Manual Transfer package can be constructed only in "
                "MANUAL_TRANSFER_IN_PROGRESS."
            )

        if self.conflict_space_artifact is None:
            raise TransitionRejected(
                "Conflict Space is required before Manual Transfer."
            )

        if self.human_critic_selection_artifact is None:
            raise TransitionRejected(
                "HUMAN Critic Selection is required before Manual Transfer."
            )

        if not isinstance(items, list) or not items:
            raise TransitionRejected(
                "Manual Transfer requires at least one HUMAN-selected item."
            )

        if not target_version_label.strip():
            raise TransitionRejected(
                "Manual Transfer target version label is required."
            )

        transfer_types = {
            "FULL",
            "PARTIAL",
            "CONDITIONAL",
            "TRANSFORMED",
            "UNRESOLVED",
        }

        built_items: list[ManualTransferItem] = []
        duplicate_keys: set[tuple[str, str, str, str]] = set()

        for index, raw in enumerate(items, start=1):
            if not isinstance(raw, dict):
                raise TransitionRejected(
                    f"Manual Transfer item {index} must be a mapping."
                )

            def required(name: str) -> str:
                value = raw.get(name, "")
                if not isinstance(value, str) or not value.strip():
                    raise TransitionRejected(
                        f"Manual Transfer item {index}: "
                        f"{name} is required."
                    )
                return value.strip()

            source_object_type = required("source_object_type")
            source_object_id = required("source_object_id")
            source_actor_type = required("source_actor_type")
            transfer_type = required("transfer_type").upper()
            original_content = required("original_content")
            selected_fragment = required("selected_fragment")
            reason = required("reason")
            expected_effect = required("expected_effect")
            destination = required("destination")

            human_transformed_content = raw.get(
                "human_transformed_content",
                "",
            )
            conditions = raw.get("conditions", "")

            if not isinstance(human_transformed_content, str):
                raise TransitionRejected(
                    f"Manual Transfer item {index}: "
                    "human_transformed_content must be text."
                )
            if not isinstance(conditions, str):
                raise TransitionRejected(
                    f"Manual Transfer item {index}: "
                    "conditions must be text."
                )

            human_transformed_content = (
                human_transformed_content.strip()
            )
            conditions = conditions.strip()

            if transfer_type not in transfer_types:
                raise TransitionRejected(
                    f"Manual Transfer item {index}: "
                    f"unsupported transfer_type {transfer_type!r}."
                )

            if (
                transfer_type == "CONDITIONAL"
                and not conditions
            ):
                raise TransitionRejected(
                    f"Manual Transfer item {index}: "
                    "CONDITIONAL transfer requires conditions."
                )

            if (
                transfer_type == "TRANSFORMED"
                and not human_transformed_content
            ):
                raise TransitionRejected(
                    f"Manual Transfer item {index}: "
                    "TRANSFORMED transfer requires HUMAN transformed content."
                )

            self._manual_transfer_validate_source(
                source_object_type=source_object_type,
                source_object_id=source_object_id,
                source_actor_type=source_actor_type,
                original_content=original_content,
                selected_fragment=selected_fragment,
                conditions=conditions,
            )

            duplicate_key = (
                source_object_type.upper(),
                source_object_id,
                selected_fragment,
                destination,
            )
            if duplicate_key in duplicate_keys:
                raise TransitionRejected(
                    f"Duplicate Manual Transfer item at position {index}."
                )
            duplicate_keys.add(duplicate_key)

            item = ManualTransferItem(
                item_id=str(_hv_uuid.uuid4()),
                source_object_type=source_object_type.upper(),
                source_object_id=source_object_id,
                source_actor_type=source_actor_type,
                transfer_type=transfer_type,
                original_content=original_content,
                selected_fragment=selected_fragment,
                human_transformed_content=human_transformed_content,
                reason=reason,
                expected_effect=expected_effect,
                conditions=conditions,
                destination=destination,
                target_version_label=target_version_label.strip(),
                status="TRANSFER_APPROVED",
                created_at=_hv_manual_transfer_now(),
                content_hash="",
            )

            item = _hv_dc.replace(
                item,
                content_hash=_hv_manual_transfer_item_hash(item),
            )
            built_items.append(item)

        canonical_source_version_id = self._manual_transfer_source_version_id()

        if not canonical_source_version_id:
            raise TransitionRejected(
                "Manual Transfer requires an exact canonical V1 version identifier."
            )

        supplied_source_version_id = source_version_id.strip()

        if (
            supplied_source_version_id
            and supplied_source_version_id != canonical_source_version_id
        ):
            raise TransitionRejected(
                "Manual Transfer source_version_id does not match canonical V1."
            )

        resolved_source_version_id = canonical_source_version_id

        space_id = _hv_manual_transfer_scalar(
            getattr(self.conflict_space_artifact, "space_id", "")
        )
        selection_id = _hv_manual_transfer_scalar(
            getattr(
                self.human_critic_selection_artifact,
                "selection_id",
                "",
            )
        )
        session_id = _hv_manual_transfer_scalar(
            getattr(self, "session_id", "")
        )

        if not session_id or not space_id or not selection_id:
            raise TransitionRejected(
                "Manual Transfer canonical session/Conflict Space/"
                "HUMAN Selection linkage is incomplete."
            )

        package = ManualTransferPackage(
            package_id="",
            session_id=session_id,
            branch_id=branch_id.strip(),
            cycle_id=cycle_id.strip(),
            package_type="PRELIMINARY_TRANSFER",
            version_number=0,
            source_version_id=resolved_source_version_id,
            conflict_space_id=space_id,
            human_selection_id=selection_id,
            target_type="MEMORY_RETRIEVAL_CONTEXT",
            target_version_label=target_version_label.strip(),
            items=tuple(built_items),
            status="DRAFT",
            confirmed_by="",
            confirmed_at="",
            confirmed_content_hash="",
            human_confirmation_note="",
            locked_by="",
            locked_at="",
            content_hash="",
            created_at=_hv_manual_transfer_now(),
        )

        package = _hv_dc.replace(
            package,
            content_hash=_hv_manual_transfer_package_hash(package),
        )

        # Transition occurs only after every validation succeeded.
        self.transition(
            S.TRANSFER_CONFIRMATION_REQUIRED,
            actor,
        )

        self.manual_transfer_artifact = package
        self.manual_transfer_history.append(package)
        return package

    def confirm_manual_transfer_package(
        self,
        *,
        actor: Actor,
        package_content_hash: str,
        confirmation_note: str,
    ) -> ManualTransferPackage:
        if actor is not Actor.HUMAN:
            raise TransitionRejected(
                "Only HUMAN can confirm the preliminary Manual Transfer package."
            )

        if self.state is not S.TRANSFER_CONFIRMATION_REQUIRED:
            raise TransitionRejected(
                "Manual Transfer confirmation is allowed only in "
                "TRANSFER_CONFIRMATION_REQUIRED."
            )

        package = self.manual_transfer_artifact
        if package is None:
            raise TransitionRejected(
                "No Manual Transfer package exists to confirm."
            )

        if package.status != "DRAFT":
            raise TransitionRejected(
                "Manual Transfer package is not awaiting HUMAN confirmation."
            )

        if not isinstance(confirmation_note, str):
            raise TransitionRejected(
                "HUMAN confirmation note must be text."
            )

        confirmation_note = confirmation_note.strip()
        if len(confirmation_note) < 8:
            raise TransitionRejected(
                "HUMAN confirmation must be explicit, not silence or "
                "a generic implicit acceptance."
            )

        self._manual_transfer_validate_integrity(package)

        if package_content_hash.strip() != package.content_hash:
            raise TransitionRejected(
                "HUMAN confirmation does not reference the exact package hash."
            )

        confirmed = _hv_dc.replace(
            package,
            status="HUMAN_CONFIRMED",
            confirmed_by=Actor.HUMAN.value,
            confirmed_at=_hv_manual_transfer_now(),
            confirmed_content_hash=package.content_hash,
            human_confirmation_note=confirmation_note,
        )

        self.manual_transfer_artifact = confirmed
        self.manual_transfer_history.append(confirmed)
        return confirmed

    def lock_manual_transfer_package(
        self,
        *,
        actor: Actor,
    ) -> ManualTransferPackage:
        if actor is not Actor.SYSTEM:
            raise TransitionRejected(
                "Only SYSTEM can execute the technical Manual Transfer lock."
            )

        if self.state is not S.TRANSFER_CONFIRMATION_REQUIRED:
            raise TransitionRejected(
                "SYSTEM lock is allowed only after HUMAN confirmation "
                "at TRANSFER_CONFIRMATION_REQUIRED."
            )

        package = self.manual_transfer_artifact
        if package is None:
            raise TransitionRejected(
                "No Manual Transfer package exists to lock."
            )

        if package.status != "HUMAN_CONFIRMED":
            raise TransitionRejected(
                "SYSTEM cannot lock Manual Transfer without explicit "
                "HUMAN confirmation."
            )

        if package.confirmed_by != Actor.HUMAN.value:
            raise TransitionRejected(
                "Manual Transfer confirmation provenance is not HUMAN."
            )

        self._manual_transfer_validate_integrity(package)

        if package.confirmed_content_hash != package.content_hash:
            raise TransitionRejected(
                "Manual Transfer content changed after HUMAN confirmation."
            )

        locked_versions = [
            snapshot.version_number
            for snapshot in self.manual_transfer_history
            if snapshot.status == "LOCKED"
            and snapshot.version_number > 0
        ]
        next_version = max(locked_versions, default=0) + 1

        locked = _hv_dc.replace(
            package,
            package_id=str(_hv_uuid.uuid4()),
            version_number=next_version,
            status="LOCKED",
            locked_by=Actor.SYSTEM.value,
            locked_at=_hv_manual_transfer_now(),
        )

        # SYSTEM performs only the technical lock.
        # A one-shot authorization binds transition() to this canonical
        # method and to the exact HUMAN-confirmed package hash.
        self._manual_transfer_lock_authorization_hash = package.content_hash
        try:
            self.transition(
                S.TRANSFER_PACKAGE_LOCKED,
                actor,
            )
        finally:
            self._manual_transfer_lock_authorization_hash = None

        self.manual_transfer_artifact = locked
        self.manual_transfer_history.append(locked)
        return locked


    def _find_result_version_by_id(
        self,
        version_id: str,
    ):
        if not isinstance(version_id, str) or not version_id.strip():
            raise TransitionRejected(
                "Final Reconstruction requires source_version_id."
            )

        for version in self.result_versions.values():
            candidate_id = (
                getattr(version, "version_id", None)
                if not isinstance(version, dict)
                else version.get("version_id")
            )

            if candidate_id == version_id.strip():
                return version

        raise TransitionRejected(
            "Final Reconstruction source ResultVersion does not exist."
        )

    def _resolve_final_reconstruction_memory_mode(self) -> str:
        latest_source = None

        if self.history:
            latest = self.history[-1]
            if latest.target is S.RECONSTRUCTION_PACKAGE_PREPARATION:
                latest_source = latest.source

        if latest_source is S.MEMORY_SELECTION_LOCKED:
            return "MEMORY_TRANSFER"

        if latest_source is S.NO_RELEVANT_MEMORY:
            return "NO_RELEVANT_MEMORY"

        memory_selection = self.memory_selection_artifact
        memory_transfer = self.memory_transfer_artifact

        if (
            memory_selection is not None
            and memory_transfer is not None
            and memory_selection.status == "LOCKED"
            and memory_transfer.status == "LOCKED"
        ):
            return "MEMORY_TRANSFER"

        if (
            self.memory_resolution_outcome
            == MEMORY_RESOLUTION_NO_RELEVANT_MEMORY
            and self.memory_negative_human_reason
        ):
            return "NO_RELEVANT_MEMORY"

        raise TransitionRejected(
            "Final Reconstruction requires either a locked MEMORY_TRANSFER "
            "or explicit HUMAN NO_RELEVANT_MEMORY resolution."
        )

    def _collect_final_reconstruction_sources(
        self,
        *,
        memory_mode: str,
    ) -> dict:
        direction = self.human_direction_artifact
        response = self.human_response_artifact
        critic_review = self.critic_review_artifact
        conflict = self.conflict_space_artifact
        human_selection = self.human_critic_selection_artifact
        manual_transfer = self.manual_transfer_artifact

        if direction is None:
            raise TransitionRejected(
                "Final Reconstruction requires confirmed Human Direction."
            )

        if getattr(direction, "status", None) != "CONFIRMED":
            raise TransitionRejected(
                "Final Reconstruction requires CONFIRMED Human Direction."
            )

        if response is None:
            raise TransitionRejected(
                "Final Reconstruction requires Human Cognitive Response."
            )

        if critic_review is None:
            raise TransitionRejected(
                "Final Reconstruction requires CriticReview."
            )

        if conflict is None:
            raise TransitionRejected(
                "Final Reconstruction requires Conflict Space."
            )

        if human_selection is None:
            raise TransitionRejected(
                "Final Reconstruction requires HUMAN Critic Selection."
            )

        selection_actor = getattr(
            human_selection,
            "actor",
            None,
        )

        if selection_actor != Actor.HUMAN.value:
            raise TransitionRejected(
                "Final Reconstruction Critic Selection provenance "
                "must be HUMAN."
            )

        if manual_transfer is None:
            raise TransitionRejected(
                "Final Reconstruction requires Manual Transfer."
            )

        if (
            getattr(manual_transfer, "status", None) != "LOCKED"
            or getattr(
                manual_transfer,
                "confirmed_by",
                None,
            ) != Actor.HUMAN.value
            or getattr(
                manual_transfer,
                "locked_by",
                None,
            ) != Actor.SYSTEM.value
        ):
            raise TransitionRejected(
                "Final Reconstruction requires the exact HUMAN-confirmed, "
                "SYSTEM-locked Manual Transfer package."
            )

        source_version_id = getattr(
            manual_transfer,
            "source_version_id",
            "",
        )

        source_version = self._find_result_version_by_id(
            source_version_id
        )

        version_label = (
            getattr(source_version, "version_label", None)
            if not isinstance(source_version, dict)
            else source_version.get("version_label")
        )

        version_content_hash = (
            getattr(source_version, "content_hash", None)
            if not isinstance(source_version, dict)
            else source_version.get("content_hash")
        )

        if version_label != "V1":
            raise TransitionRejected(
                "Final Reconstruction must be bound to canonical V1."
            )

        if (
            not isinstance(version_content_hash, str)
            or not version_content_hash.strip()
        ):
            raise TransitionRejected(
                "Canonical V1 must have a content hash."
            )

        response_source_version_id = getattr(
            response,
            "source_version_id",
            None,
        )

        if response_source_version_id != source_version_id:
            raise TransitionRejected(
                "Human Cognitive Response is not bound to canonical V1."
            )

        critic_source_version_id = getattr(
            critic_review,
            "source_version_id",
            None,
        )

        if critic_source_version_id != source_version_id:
            raise TransitionRejected(
                "CriticReview is not bound to canonical V1."
            )

        conflict_source_version_id = getattr(
            conflict,
            "source_version_id",
            None,
        )

        if conflict_source_version_id != source_version_id:
            raise TransitionRejected(
                "Conflict Space is not bound to canonical V1."
            )

        human_selection_source_version_id = getattr(
            human_selection,
            "source_version_id",
            None,
        )

        if (
            human_selection_source_version_id is not None
            and human_selection_source_version_id
            != source_version_id
        ):
            raise TransitionRejected(
                "HUMAN Critic Selection is not bound to canonical V1."
            )

        memory_selection_snapshot = None
        memory_transfer_snapshot = None
        no_relevant_reason = ""

        if memory_mode == "MEMORY_TRANSFER":
            memory_selection = self.memory_selection_artifact
            memory_transfer = self.memory_transfer_artifact

            if memory_selection is None or memory_transfer is None:
                raise TransitionRejected(
                    "Final Reconstruction MEMORY_TRANSFER branch requires "
                    "Memory Selection and Memory Transfer."
                )

            if (
                memory_selection.status != "LOCKED"
                or memory_transfer.status != "LOCKED"
                or memory_selection.confirmed_by
                != Actor.HUMAN.value
                or memory_transfer.confirmed_by
                != Actor.HUMAN.value
                or memory_selection.locked_by
                != Actor.SYSTEM.value
                or memory_transfer.locked_by
                != Actor.SYSTEM.value
            ):
                raise TransitionRejected(
                    "Final Reconstruction requires exact HUMAN-confirmed, "
                    "SYSTEM-locked memory artifacts."
                )

            self._validate_memory_selection_integrity(
                memory_selection
            )
            self._validate_memory_transfer_integrity(
                memory_transfer
            )

            memory_selection_snapshot = _hv_rc_snapshot(
                memory_selection
            )
            memory_transfer_snapshot = _hv_rc_snapshot(
                memory_transfer
            )

        elif memory_mode == "NO_RELEVANT_MEMORY":
            if (
                self.memory_resolution_outcome
                != MEMORY_RESOLUTION_NO_RELEVANT_MEMORY
                or not self.memory_negative_human_reason
            ):
                raise TransitionRejected(
                    "NO_RELEVANT_MEMORY branch requires explicit HUMAN "
                    "memory resolution and persisted reason."
                )

            no_relevant_reason = (
                self.memory_negative_human_reason.strip()
            )

            if self.memory_selection_artifact is not None:
                memory_selection_snapshot = _hv_rc_snapshot(
                    self.memory_selection_artifact
                )

        else:
            raise TransitionRejected(
                f"Unsupported Final Reconstruction memory mode: "
                f"{memory_mode!r}."
            )

        return {
            "source_version_id": source_version_id,
            "source_version_label": version_label,
            "source_version_content_hash":
                version_content_hash,

            "human_direction":
                _hv_rc_snapshot(direction),

            "human_response":
                _hv_rc_snapshot(response),

            "human_critic_selection":
                _hv_rc_snapshot(human_selection),

            "conflict_space_id":
                str(getattr(conflict, "space_id", "")),

            "critic_review_id":
                str(getattr(critic_review, "review_id", "")),

            "manual_transfer":
                _hv_rc_snapshot(manual_transfer),

            "memory_selection":
                memory_selection_snapshot,

            "memory_transfer":
                memory_transfer_snapshot,

            "no_relevant_memory_reason":
                no_relevant_reason,
        }

    def _validate_final_reconstruction_package_integrity(
        self,
        package: FinalReconstructionPackage,
        *,
        verify_live_sources: bool = True,
    ) -> None:
        if package.content_hash != _hv_rc_package_hash(package):
            raise TransitionRejected(
                "Final Reconstruction Package integrity check failed."
            )

        if not verify_live_sources:
            return

        current = self._collect_final_reconstruction_sources(
            memory_mode=package.memory_mode,
        )

        checks = {
            "source_version_id":
                package.source_version_id,
            "source_version_label":
                package.source_version_label,
            "source_version_content_hash":
                package.source_version_content_hash,
            "human_direction":
                package.human_direction,
            "human_response":
                package.human_response,
            "human_critic_selection":
                package.human_critic_selection,
            "conflict_space_id":
                package.conflict_space_id,
            "critic_review_id":
                package.critic_review_id,
            "manual_transfer":
                package.manual_transfer,
            "memory_selection":
                package.memory_selection,
            "memory_transfer":
                package.memory_transfer,
            "no_relevant_memory_reason":
                package.no_relevant_memory_reason,
        }

        for name, expected in checks.items():
            if current[name] != expected:
                raise TransitionRejected(
                    "Final Reconstruction live-source integrity "
                    f"check failed: {name}."
                )

    def build_final_reconstruction_package(
        self,
        *,
        actor: Actor,
    ) -> FinalReconstructionPackage:
        if actor is not Actor.ORCHESTRATOR:
            raise TransitionRejected(
                "Only ORCHESTRATOR can build Final Reconstruction Package."
            )

        if self.state is not S.RECONSTRUCTION_PACKAGE_PREPARATION:
            raise TransitionRejected(
                "Final Reconstruction Package can be built only in "
                "RECONSTRUCTION_PACKAGE_PREPARATION."
            )

        memory_mode = (
            self._resolve_final_reconstruction_memory_mode()
        )

        sources = self._collect_final_reconstruction_sources(
            memory_mode=memory_mode,
        )

        previous_revisions = [
            item.package_revision
            for item in self.reconstruction_package_history
        ]

        package_revision = (
            max(previous_revisions) + 1
            if previous_revisions
            else 1
        )

        package = FinalReconstructionPackage(
            package_id=str(_hv_rc_uuid4()),
            session_id=str(self.session_id or ""),
            package_revision=package_revision,

            source_version_id=
                sources["source_version_id"],
            source_version_label=
                sources["source_version_label"],
            source_version_content_hash=
                sources["source_version_content_hash"],

            human_direction=
                sources["human_direction"],
            human_response=
                sources["human_response"],
            human_critic_selection=
                sources["human_critic_selection"],

            conflict_space_id=
                sources["conflict_space_id"],
            critic_review_id=
                sources["critic_review_id"],

            manual_transfer=
                sources["manual_transfer"],

            memory_mode=memory_mode,
            memory_selection=
                sources["memory_selection"],
            memory_transfer=
                sources["memory_transfer"],
            no_relevant_memory_reason=
                sources["no_relevant_memory_reason"],

            builder_use_contract=(
                "Builder Reconstruction MUST preserve confirmed Human "
                "Direction and canonical V1. Cognitive modifications may "
                "use ONLY the explicitly authorized items in the locked "
                "Manual Transfer package and, when memory_mode is "
                "MEMORY_TRANSFER, ONLY the explicitly authorized items "
                "in the locked MEMORY_TRANSFER package. Human Response "
                "and HUMAN Critic Selection are included for traceability "
                "and provenance, not as blanket authorization to import "
                "unselected material."
            ),

            status="DRAFT",

            confirmed_by="",
            confirmed_at="",
            confirmed_content_hash="",
            confirmation_note="",

            locked_by="",
            locked_at="",

            content_hash="",
            created_at=_hv_rc_now(),
            created_revision=self.revision,
        )

        package = _hv_rc_replace(
            package,
            content_hash=_hv_rc_package_hash(package),
        )

        self._validate_final_reconstruction_package_integrity(
            package,
            verify_live_sources=True,
        )

        old_artifact = self.reconstruction_package_artifact
        old_history_len = len(
            self.reconstruction_package_history
        )

        self.reconstruction_package_artifact = package
        self.reconstruction_package_history.append(package)

        try:
            self.transition(
                S.RECONSTRUCTION_PACKAGE_CONFIRMATION_REQUIRED,
                actor,
            )
        except Exception:
            self.reconstruction_package_artifact = old_artifact
            del self.reconstruction_package_history[
                old_history_len:
            ]
            raise

        return package

    def confirm_final_reconstruction_package(
        self,
        *,
        actor: Actor,
        package_content_hash: str,
        confirmation_note: str,
    ) -> FinalReconstructionPackage:
        if actor is not Actor.HUMAN:
            raise TransitionRejected(
                "Only HUMAN can confirm Final Reconstruction Package."
            )

        if (
            self.state
            is not S.RECONSTRUCTION_PACKAGE_CONFIRMATION_REQUIRED
        ):
            raise TransitionRejected(
                "Final Reconstruction confirmation is allowed only in "
                "RECONSTRUCTION_PACKAGE_CONFIRMATION_REQUIRED."
            )

        package = self.reconstruction_package_artifact

        if package is None:
            raise TransitionRejected(
                "No Final Reconstruction Package exists."
            )

        if package.status != "DRAFT":
            raise TransitionRejected(
                "Final Reconstruction Package is not awaiting "
                "HUMAN confirmation."
            )

        if (
            not isinstance(package_content_hash, str)
            or package_content_hash.strip()
            != package.content_hash
        ):
            raise TransitionRejected(
                "HUMAN confirmation must reference the exact Final "
                "Reconstruction Package hash."
            )

        if (
            not isinstance(confirmation_note, str)
            or len(confirmation_note.strip()) < 8
        ):
            raise TransitionRejected(
                "Final Reconstruction confirmation must be explicit."
            )

        self._validate_final_reconstruction_package_integrity(
            package,
            verify_live_sources=True,
        )

        confirmed = _hv_rc_replace(
            package,
            status="HUMAN_CONFIRMED",
            confirmed_by=Actor.HUMAN.value,
            confirmed_at=_hv_rc_now(),
            confirmed_content_hash=package.content_hash,
            confirmation_note=confirmation_note.strip(),
        )

        self.reconstruction_package_artifact = confirmed
        self.reconstruction_package_history.append(confirmed)

        return confirmed

    def lock_final_reconstruction_package(
        self,
        *,
        actor: Actor,
    ) -> FinalReconstructionPackage:
        if actor is not Actor.SYSTEM:
            raise TransitionRejected(
                "Only SYSTEM can technically lock "
                "Final Reconstruction Package."
            )

        if (
            self.state
            is not S.RECONSTRUCTION_PACKAGE_CONFIRMATION_REQUIRED
        ):
            raise TransitionRejected(
                "Final Reconstruction technical lock requires "
                "RECONSTRUCTION_PACKAGE_CONFIRMATION_REQUIRED."
            )

        package = self.reconstruction_package_artifact

        if package is None:
            raise TransitionRejected(
                "Final Reconstruction technical lock requires package."
            )

        if (
            package.status != "HUMAN_CONFIRMED"
            or package.confirmed_by != Actor.HUMAN.value
        ):
            raise TransitionRejected(
                "SYSTEM cannot lock Final Reconstruction Package "
                "before explicit HUMAN confirmation."
            )

        self._validate_final_reconstruction_package_integrity(
            package,
            verify_live_sources=True,
        )

        if (
            package.confirmed_content_hash
            != package.content_hash
        ):
            raise TransitionRejected(
                "Final Reconstruction content changed after "
                "HUMAN confirmation."
            )

        self._reconstruction_package_lock_authorization_hash = (
            package.content_hash
        )

        try:
            self.transition(
                S.RECONSTRUCTION_PACKAGE_READY,
                actor,
            )
        finally:
            self._reconstruction_package_lock_authorization_hash = None

        locked = _hv_rc_replace(
            package,
            status="LOCKED",
            locked_by=Actor.SYSTEM.value,
            locked_at=_hv_rc_now(),
        )

        self.reconstruction_package_artifact = locked
        self.reconstruction_package_history.append(locked)

        return locked


    def _has_demo_positive_memory_evidence(self) -> bool:
        if self.retrieval_outcome != RETRIEVAL_CANDIDATES_FOUND:
            return False

        locked_index = None
        vn_index = None

        for index, record in enumerate(self.history):
            if (
                locked_index is None
                and record.target is S.MEMORY_SELECTION_LOCKED
            ):
                locked_index = index

            if (
                locked_index is not None
                and index > locked_index
                and record.target is S.VN_GENERATED
            ):
                vn_index = index
                break

        if locked_index is None or vn_index is None:
            return False

        return any(
            evidence.outcome == "OBSERVABLE_EFFECT"
            for evidence in self.memory_effect_verifications
        )

    def record_memory_effect_verification(
        self,
        *,
        memory_selection_item_id: str,
        outcome: str,
        actor: Actor,
        reason: str,
    ) -> None:
        if actor is not Actor.HUMAN:
            raise TransitionRejected(
                "Memory effect verification requires HUMAN actor."
            )

        allowed_outcomes = {
            "OBSERVABLE_EFFECT",
            "DISTORTION",
            "NOT_INTEGRATED",
            "COMPARISON_ONLY",
        }

        normalized = outcome.strip().upper()
        if normalized not in allowed_outcomes:
            raise TransitionRejected(
                "Invalid memory effect verification outcome."
            )

        if not memory_selection_item_id.strip():
            raise TransitionRejected(
                "memory_selection_item_id is required."
            )

        if not reason.strip():
            raise TransitionRejected(
                "Memory effect verification requires a reason."
            )

        vn_exists = any(
            record.target is S.VN_GENERATED
            for record in self.history
        )
        if not vn_exists:
            raise TransitionRejected(
                "Memory effect cannot be verified before VN_GENERATED."
            )

        self.memory_effect_verifications.append(
            MemoryEffectVerification(
                memory_selection_item_id=memory_selection_item_id.strip(),
                outcome=normalized,
                reason=reason.strip(),
                verified_revision=self.revision,
            )
        )


    @staticmethod
    def _memory_active_decisions() -> set[str]:
        return {
            "ACTIVATE",
            "ACTIVATE_PARTIAL",
            "ACTIVATE_CONDITIONAL",
        }

    def _memory_candidate_map(self) -> dict[str, MemoryCandidate]:
        artifact = self.memory_retrieval_artifact
        if artifact is None:
            return {}
        return {
            candidate.candidate_id: candidate
            for candidate in artifact.candidates
        }

    def _validate_memory_retrieval_integrity(
        self,
        artifact: MemoryRetrievalArtifact,
    ) -> None:
        if not artifact.candidates:
            raise TransitionRejected(
                "Positive memory retrieval must contain candidates."
            )

        for candidate in artifact.candidates:
            if candidate.content_hash != _hv_memory_candidate_hash(candidate):
                raise TransitionRejected(
                    "Memory candidate integrity check failed."
                )

        if artifact.content_hash != _hv_memory_retrieval_hash(artifact):
            raise TransitionRejected(
                "Memory retrieval artifact integrity check failed."
            )

    def _validate_memory_selection_integrity(
        self,
        artifact: MemorySelection,
    ) -> None:
        if not artifact.items:
            raise TransitionRejected(
                "Memory Selection cannot be empty."
            )

        for item in artifact.items:
            if (
                item.content_hash
                != _hv_memory_selection_item_hash(item)
            ):
                raise TransitionRejected(
                    "Memory Selection item integrity check failed."
                )

        if artifact.content_hash != _hv_memory_selection_hash(artifact):
            raise TransitionRejected(
                "Memory Selection integrity check failed."
            )

    def _validate_memory_transfer_integrity(
        self,
        artifact: MemoryTransferPackage,
    ) -> None:
        if not artifact.items:
            raise TransitionRejected(
                "MEMORY_TRANSFER package cannot be empty."
            )

        for item in artifact.items:
            if (
                item.content_hash
                != _hv_memory_transfer_item_hash(item)
            ):
                raise TransitionRejected(
                    "Memory Transfer item integrity check failed."
                )

        if artifact.content_hash != _hv_memory_transfer_hash(artifact):
            raise TransitionRejected(
                "MEMORY_TRANSFER package integrity check failed."
            )

    def record_memory_candidates(
        self,
        *,
        actor: Actor,
        query_basis: str,
        candidates: list[dict],
    ) -> MemoryRetrievalArtifact:
        if actor is not Actor.MEMORY:
            raise TransitionRejected(
                "Only Active Agentic Memory can record retrieval candidates."
            )

        if self.state is not S.MEMORY_RETRIEVAL_RUNNING:
            raise TransitionRejected(
                "Memory candidates can be recorded only while "
                "MEMORY_RETRIEVAL_RUNNING is active."
            )

        manual_transfer = self.manual_transfer_artifact
        if (
            manual_transfer is None
            or manual_transfer.status != "LOCKED"
            or manual_transfer.confirmed_by != Actor.HUMAN.value
            or manual_transfer.locked_by != Actor.SYSTEM.value
        ):
            raise TransitionRejected(
                "Memory retrieval requires the locked preliminary "
                "Manual Transfer package."
            )

        if not isinstance(query_basis, str) or not query_basis.strip():
            raise TransitionRejected(
                "Memory retrieval query basis is required."
            )

        if not isinstance(candidates, list) or not candidates:
            raise TransitionRejected(
                "record_memory_candidates requires at least one candidate. "
                "Use the negative retrieval outcome for zero candidates."
            )

        built: list[MemoryCandidate] = []
        duplicates: set[tuple[str, str]] = set()

        for index, raw in enumerate(candidates, start=1):
            if not isinstance(raw, dict):
                raise TransitionRejected(
                    f"Memory candidate {index} must be a mapping."
                )

            def required(name: str) -> str:
                value = raw.get(name, "")
                if not isinstance(value, str) or not value.strip():
                    raise TransitionRejected(
                        f"Memory candidate {index}: {name} is required."
                    )
                return value.strip()

            source_id = required("source_id")
            source_type = required("source_type")
            source_actor = required("source_actor")
            source_session_id = required("source_session_id")
            original_content = required("original_content")
            provenance = required("provenance")
            retrieval_reason = required("retrieval_reason")

            score = raw.get("relevance_score")
            if score is not None:
                if not isinstance(score, (int, float)):
                    raise TransitionRejected(
                        f"Memory candidate {index}: relevance_score "
                        "must be numeric."
                    )
                score = float(score)
                if score < 0.0 or score > 1.0:
                    raise TransitionRejected(
                        f"Memory candidate {index}: relevance_score "
                        "must be between 0 and 1."
                    )

            warnings_raw = raw.get("warnings", [])
            if not isinstance(warnings_raw, list):
                raise TransitionRejected(
                    f"Memory candidate {index}: warnings must be a list."
                )

            warnings = []
            for warning in warnings_raw:
                if not isinstance(warning, str) or not warning.strip():
                    raise TransitionRejected(
                        f"Memory candidate {index}: invalid warning."
                    )
                warnings.append(warning.strip())

            duplicate_key = (source_id, original_content)
            if duplicate_key in duplicates:
                raise TransitionRejected(
                    f"Duplicate memory candidate at position {index}."
                )
            duplicates.add(duplicate_key)

            candidate = MemoryCandidate(
                candidate_id=str(_hv_mem_uuid4()),
                source_id=source_id,
                source_type=source_type,
                source_actor=source_actor,
                source_session_id=source_session_id,
                original_content=original_content,
                provenance=provenance,
                retrieval_reason=retrieval_reason,
                relevance_score=score,
                warnings=tuple(warnings),
                retrieved_at=_hv_memory_now(),
                content_hash="",
            )

            candidate = _hv_mem_replace(
                candidate,
                content_hash=_hv_memory_candidate_hash(candidate),
            )
            built.append(candidate)

        artifact = MemoryRetrievalArtifact(
            retrieval_id=str(_hv_mem_uuid4()),
            session_id=str(self.session_id or ""),
            manual_transfer_package_id=manual_transfer.package_id,
            query_basis=query_basis.strip(),
            candidates=tuple(built),
            retrieval_outcome=RETRIEVAL_CANDIDATES_FOUND,
            actor=Actor.MEMORY.value,
            created_at=_hv_memory_now(),
            content_hash="",
        )

        artifact = _hv_mem_replace(
            artifact,
            content_hash=_hv_memory_retrieval_hash(artifact),
        )

        old_outcome = self.retrieval_outcome
        old_reason = getattr(self, "outcome_reason", None)

        self.retrieval_outcome = RETRIEVAL_CANDIDATES_FOUND
        self.outcome_reason = (
            f"{len(built)} memory candidate(s) retrieved with provenance."
        )

        try:
            self.transition(
                S.MEMORY_REVIEW_REQUIRED,
                actor,
            )
        except Exception:
            self.retrieval_outcome = old_outcome
            self.outcome_reason = old_reason
            raise

        self.memory_retrieval_artifact = artifact
        self.memory_retrieval_history.append(artifact)
        return artifact

    def review_memory_candidates(
        self,
        *,
        actor: Actor,
        decisions: list[dict],
    ) -> MemorySelection:
        if actor is not Actor.HUMAN:
            raise TransitionRejected(
                "Only HUMAN can review and activate memory candidates."
            )

        if self.state is not S.MEMORY_REVIEW_REQUIRED:
            raise TransitionRejected(
                "Memory review is allowed only in MEMORY_REVIEW_REQUIRED."
            )

        retrieval = self.memory_retrieval_artifact
        if retrieval is None:
            raise TransitionRejected(
                "No persisted memory retrieval artifact exists."
            )

        self._validate_memory_retrieval_integrity(retrieval)

        if self.retrieval_outcome != RETRIEVAL_CANDIDATES_FOUND:
            raise TransitionRejected(
                "HUMAN memory review requires CANDIDATES_FOUND."
            )

        if not isinstance(decisions, list) or not decisions:
            raise TransitionRejected(
                "HUMAN must explicitly review every memory candidate."
            )

        candidate_map = self._memory_candidate_map()

        decision_ids = []
        for raw in decisions:
            if not isinstance(raw, dict):
                raise TransitionRejected(
                    "Each HUMAN memory decision must be a mapping."
                )
            candidate_id = raw.get("candidate_id", "")
            if not isinstance(candidate_id, str) or not candidate_id.strip():
                raise TransitionRejected(
                    "Every HUMAN memory decision requires candidate_id."
                )
            decision_ids.append(candidate_id.strip())

        if len(set(decision_ids)) != len(decision_ids):
            raise TransitionRejected(
                "Duplicate HUMAN memory decisions are not allowed."
            )

        if set(decision_ids) != set(candidate_map):
            raise TransitionRejected(
                "HUMAN must explicitly review every retrieved candidate; "
                "silence is not acceptance."
            )

        allowed = {
            "ACTIVATE",
            "ACTIVATE_PARTIAL",
            "ACTIVATE_CONDITIONAL",
            "REJECT",
            "COMPARE_ONLY",
            "IRRELEVANT",
            "OUTDATED",
            "KEEP_UNRESOLVED",
        }

        active = self._memory_active_decisions()
        built: list[MemorySelectionItem] = []

        for index, raw in enumerate(decisions, start=1):
            candidate_id = raw["candidate_id"].strip()
            candidate = candidate_map[candidate_id]

            decision = raw.get("decision", "")
            reason = raw.get("reason", "")

            if not isinstance(decision, str):
                raise TransitionRejected(
                    f"Memory decision {index}: decision must be text."
                )
            if not isinstance(reason, str) or not reason.strip():
                raise TransitionRejected(
                    f"Memory decision {index}: reason is required."
                )

            decision = decision.strip().upper()
            reason = reason.strip()

            if decision not in allowed:
                raise TransitionRejected(
                    f"Unsupported HUMAN memory decision: {decision!r}."
                )

            accepted_fragment = raw.get("accepted_fragment", "")
            human_transformed_content = raw.get(
                "human_transformed_content",
                "",
            )
            conditions = raw.get("conditions", "")
            destination = raw.get("destination", "")
            authorized_effect = raw.get("authorized_effect", "")

            for name, value in (
                ("accepted_fragment", accepted_fragment),
                ("human_transformed_content", human_transformed_content),
                ("conditions", conditions),
                ("destination", destination),
                ("authorized_effect", authorized_effect),
            ):
                if not isinstance(value, str):
                    raise TransitionRejected(
                        f"Memory decision {index}: {name} must be text."
                    )

            accepted_fragment = accepted_fragment.strip()
            human_transformed_content = human_transformed_content.strip()
            conditions = conditions.strip()
            destination = destination.strip()
            authorized_effect = authorized_effect.strip()

            if decision in active:
                if not accepted_fragment:
                    raise TransitionRejected(
                        f"Memory decision {index}: active memory requires "
                        "an explicit accepted_fragment."
                    )
                if accepted_fragment not in candidate.original_content:
                    raise TransitionRejected(
                        f"Memory decision {index}: accepted fragment "
                        "does not match the retrieved candidate."
                    )
                if not destination:
                    raise TransitionRejected(
                        f"Memory decision {index}: destination is required."
                    )
                if not authorized_effect:
                    raise TransitionRejected(
                        f"Memory decision {index}: authorized_effect "
                        "is required."
                    )
                if (
                    decision == "ACTIVATE_CONDITIONAL"
                    and not conditions
                ):
                    raise TransitionRejected(
                        f"Memory decision {index}: conditional activation "
                        "requires conditions."
                    )

            item = MemorySelectionItem(
                selection_item_id=str(_hv_mem_uuid4()),
                candidate_id=candidate_id,
                decision=decision,
                accepted_fragment=accepted_fragment,
                human_transformed_content=human_transformed_content,
                reason=reason,
                conditions=conditions,
                destination=destination,
                authorized_effect=authorized_effect,
                status="HUMAN_REVIEWED",
                content_hash="",
            )

            item = _hv_mem_replace(
                item,
                content_hash=_hv_memory_selection_item_hash(item),
            )
            built.append(item)

        selection = MemorySelection(
            selection_id=str(_hv_mem_uuid4()),
            session_id=str(self.session_id or ""),
            retrieval_id=retrieval.retrieval_id,
            items=tuple(built),
            status="DRAFT",
            confirmed_by="",
            confirmed_at="",
            confirmed_content_hash="",
            confirmation_note="",
            locked_by="",
            locked_at="",
            content_hash="",
            created_at=_hv_memory_now(),
        )

        selection = _hv_mem_replace(
            selection,
            content_hash=_hv_memory_selection_hash(selection),
        )

        active_count = sum(
            1 for item in built if item.decision in active
        )

        if active_count > 0:
            self.transition(
                S.MEMORY_SELECTION_CONFIRMATION_REQUIRED,
                actor,
            )

        self.memory_selection_artifact = selection
        self.memory_selection_history.append(selection)
        return selection

    def build_memory_transfer_package(
        self,
        *,
        actor: Actor,
        transfers: list[dict],
    ) -> MemoryTransferPackage:
        if actor is not Actor.HUMAN:
            raise TransitionRejected(
                "Only HUMAN can construct the MEMORY_TRANSFER package."
            )

        if self.state is not S.MEMORY_SELECTION_CONFIRMATION_REQUIRED:
            raise TransitionRejected(
                "MEMORY_TRANSFER can be constructed only in "
                "MEMORY_SELECTION_CONFIRMATION_REQUIRED."
            )

        selection = self.memory_selection_artifact
        retrieval = self.memory_retrieval_artifact

        if selection is None or retrieval is None:
            raise TransitionRejected(
                "Memory Selection and retrieval artifacts are required."
            )

        self._validate_memory_selection_integrity(selection)
        self._validate_memory_retrieval_integrity(retrieval)

        active = self._memory_active_decisions()
        active_items = {
            item.selection_item_id: item
            for item in selection.items
            if item.decision in active
        }

        if not active_items:
            raise TransitionRejected(
                "MEMORY_TRANSFER requires at least one HUMAN-activated item."
            )

        if not isinstance(transfers, list) or not transfers:
            raise TransitionRejected(
                "HUMAN must manually authorize each active memory transfer."
            )

        supplied_ids = []
        for raw in transfers:
            if not isinstance(raw, dict):
                raise TransitionRejected(
                    "Every MEMORY_TRANSFER item must be a mapping."
                )
            selection_item_id = raw.get("selection_item_id", "")
            if (
                not isinstance(selection_item_id, str)
                or not selection_item_id.strip()
            ):
                raise TransitionRejected(
                    "Every MEMORY_TRANSFER item requires selection_item_id."
                )
            supplied_ids.append(selection_item_id.strip())

        if len(set(supplied_ids)) != len(supplied_ids):
            raise TransitionRejected(
                "Duplicate MEMORY_TRANSFER items are not allowed."
            )

        if set(supplied_ids) != set(active_items):
            raise TransitionRejected(
                "Every HUMAN-activated memory item must be transferred "
                "explicitly; silence is not transfer authorization."
            )

        candidate_map = self._memory_candidate_map()
        built: list[MemoryTransferItem] = []

        for index, raw in enumerate(transfers, start=1):
            selection_item_id = raw["selection_item_id"].strip()
            selected = active_items[selection_item_id]
            candidate = candidate_map[selected.candidate_id]

            selected_fragment = raw.get("selected_fragment", "")
            human_transformed_content = raw.get(
                "human_transformed_content",
                "",
            )
            reason = raw.get("reason", "")
            conditions = raw.get("conditions", "")
            destination = raw.get("destination", "")
            authorized_effect = raw.get("authorized_effect", "")

            for name, value in (
                ("selected_fragment", selected_fragment),
                ("reason", reason),
                ("destination", destination),
                ("authorized_effect", authorized_effect),
            ):
                if not isinstance(value, str) or not value.strip():
                    raise TransitionRejected(
                        f"MEMORY_TRANSFER item {index}: {name} is required."
                    )

            if not isinstance(human_transformed_content, str):
                raise TransitionRejected(
                    f"MEMORY_TRANSFER item {index}: "
                    "human_transformed_content must be text."
                )
            if not isinstance(conditions, str):
                raise TransitionRejected(
                    f"MEMORY_TRANSFER item {index}: conditions must be text."
                )

            selected_fragment = selected_fragment.strip()
            human_transformed_content = human_transformed_content.strip()
            reason = reason.strip()
            conditions = conditions.strip()
            destination = destination.strip()
            authorized_effect = authorized_effect.strip()

            if selected_fragment not in candidate.original_content:
                raise TransitionRejected(
                    f"MEMORY_TRANSFER item {index}: selected fragment "
                    "does not match the canonical memory candidate."
                )

            if (
                selected.accepted_fragment
                and selected_fragment not in selected.accepted_fragment
                and selected.accepted_fragment not in selected_fragment
            ):
                raise TransitionRejected(
                    f"MEMORY_TRANSFER item {index}: fragment differs "
                    "from HUMAN-reviewed activation."
                )

            if destination != selected.destination:
                raise TransitionRejected(
                    f"MEMORY_TRANSFER item {index}: destination differs "
                    "from HUMAN-reviewed selection."
                )

            if authorized_effect != selected.authorized_effect:
                raise TransitionRejected(
                    f"MEMORY_TRANSFER item {index}: authorized effect "
                    "differs from HUMAN-reviewed selection."
                )

            if conditions != selected.conditions:
                raise TransitionRejected(
                    f"MEMORY_TRANSFER item {index}: conditions differ "
                    "from HUMAN-reviewed selection."
                )

            if human_transformed_content != selected.human_transformed_content:
                raise TransitionRejected(
                    f"MEMORY_TRANSFER item {index}: HUMAN transformation "
                    "differs from the reviewed selection."
                )

            transfer = MemoryTransferItem(
                transfer_item_id=str(_hv_mem_uuid4()),
                selection_item_id=selection_item_id,
                candidate_id=candidate.candidate_id,
                source_id=candidate.source_id,
                source_actor=candidate.source_actor,
                original_content=candidate.original_content,
                selected_fragment=selected_fragment,
                human_transformed_content=human_transformed_content,
                reason=reason,
                conditions=conditions,
                destination=destination,
                authorized_effect=authorized_effect,
                provenance=candidate.provenance,
                content_hash="",
            )

            transfer = _hv_mem_replace(
                transfer,
                content_hash=_hv_memory_transfer_item_hash(transfer),
            )
            built.append(transfer)

        package = MemoryTransferPackage(
            package_id=str(_hv_mem_uuid4()),
            session_id=str(self.session_id or ""),
            retrieval_id=retrieval.retrieval_id,
            selection_id=selection.selection_id,
            package_type="MEMORY_TRANSFER",
            items=tuple(built),
            status="DRAFT",
            confirmed_by="",
            confirmed_at="",
            confirmed_content_hash="",
            confirmation_note="",
            locked_by="",
            locked_at="",
            content_hash="",
            created_at=_hv_memory_now(),
        )

        package = _hv_mem_replace(
            package,
            content_hash=_hv_memory_transfer_hash(package),
        )

        self.memory_transfer_artifact = package
        self.memory_transfer_history.append(package)
        return package

    def confirm_memory_selection_and_transfer(
        self,
        *,
        actor: Actor,
        selection_content_hash: str,
        transfer_content_hash: str,
        confirmation_note: str,
    ) -> tuple[MemorySelection, MemoryTransferPackage]:
        if actor is not Actor.HUMAN:
            raise TransitionRejected(
                "Only HUMAN can confirm memory activation and transfer."
            )

        if self.state is not S.MEMORY_SELECTION_CONFIRMATION_REQUIRED:
            raise TransitionRejected(
                "Memory confirmation is allowed only in "
                "MEMORY_SELECTION_CONFIRMATION_REQUIRED."
            )

        selection = self.memory_selection_artifact
        package = self.memory_transfer_artifact

        if selection is None or package is None:
            raise TransitionRejected(
                "Memory Selection and MEMORY_TRANSFER package are required."
            )

        if selection.status != "DRAFT" or package.status != "DRAFT":
            raise TransitionRejected(
                "Memory activation/transfer is not awaiting confirmation."
            )

        if (
            not isinstance(confirmation_note, str)
            or len(confirmation_note.strip()) < 8
        ):
            raise TransitionRejected(
                "HUMAN memory confirmation must be explicit."
            )

        self._validate_memory_selection_integrity(selection)
        self._validate_memory_transfer_integrity(package)

        if selection_content_hash.strip() != selection.content_hash:
            raise TransitionRejected(
                "HUMAN confirmation does not reference the exact "
                "Memory Selection hash."
            )

        if transfer_content_hash.strip() != package.content_hash:
            raise TransitionRejected(
                "HUMAN confirmation does not reference the exact "
                "MEMORY_TRANSFER hash."
            )

        now = _hv_memory_now()
        note = confirmation_note.strip()

        confirmed_selection = _hv_mem_replace(
            selection,
            status="HUMAN_CONFIRMED",
            confirmed_by=Actor.HUMAN.value,
            confirmed_at=now,
            confirmed_content_hash=selection.content_hash,
            confirmation_note=note,
        )

        confirmed_package = _hv_mem_replace(
            package,
            status="HUMAN_CONFIRMED",
            confirmed_by=Actor.HUMAN.value,
            confirmed_at=now,
            confirmed_content_hash=package.content_hash,
            confirmation_note=note,
        )

        self.memory_selection_artifact = confirmed_selection
        self.memory_transfer_artifact = confirmed_package
        self.memory_selection_history.append(confirmed_selection)
        self.memory_transfer_history.append(confirmed_package)

        return confirmed_selection, confirmed_package

    def lock_memory_selection(
        self,
        *,
        actor: Actor,
    ) -> tuple[MemorySelection, MemoryTransferPackage]:
        if actor is not Actor.SYSTEM:
            raise TransitionRejected(
                "Only SYSTEM can execute MEMORY_SELECTION_LOCKED."
            )

        if self.state is not S.MEMORY_SELECTION_CONFIRMATION_REQUIRED:
            raise TransitionRejected(
                "SYSTEM memory lock requires "
                "MEMORY_SELECTION_CONFIRMATION_REQUIRED."
            )

        selection = self.memory_selection_artifact
        package = self.memory_transfer_artifact

        if selection is None or package is None:
            raise TransitionRejected(
                "Memory Selection and MEMORY_TRANSFER are required."
            )

        if (
            selection.status != "HUMAN_CONFIRMED"
            or package.status != "HUMAN_CONFIRMED"
        ):
            raise TransitionRejected(
                "SYSTEM cannot lock memory before explicit HUMAN confirmation."
            )

        if (
            selection.confirmed_by != Actor.HUMAN.value
            or package.confirmed_by != Actor.HUMAN.value
        ):
            raise TransitionRejected(
                "Memory confirmation provenance must be HUMAN."
            )

        self._validate_memory_selection_integrity(selection)
        self._validate_memory_transfer_integrity(package)

        if (
            selection.confirmed_content_hash != selection.content_hash
            or package.confirmed_content_hash != package.content_hash
        ):
            raise TransitionRejected(
                "Memory content changed after HUMAN confirmation."
            )

        authorization = selection.content_hash + ":" + package.content_hash

        self._memory_selection_lock_authorization_hash = authorization
        try:
            self.transition(
                S.MEMORY_SELECTION_LOCKED,
                actor,
            )
        finally:
            self._memory_selection_lock_authorization_hash = None

        now = _hv_memory_now()

        locked_selection = _hv_mem_replace(
            selection,
            status="LOCKED",
            locked_by=Actor.SYSTEM.value,
            locked_at=now,
        )

        locked_package = _hv_mem_replace(
            package,
            status="LOCKED",
            locked_by=Actor.SYSTEM.value,
            locked_at=now,
        )

        self.memory_selection_artifact = locked_selection
        self.memory_transfer_artifact = locked_package
        self.memory_selection_history.append(locked_selection)
        self.memory_transfer_history.append(locked_package)

        return locked_selection, locked_package

    def confirm_no_relevant_memory(
        self,
        *,
        actor: Actor,
        reason: str,
    ) -> None:
        if actor is not Actor.HUMAN:
            raise TransitionRejected(
                "Only HUMAN can confirm NO_RELEVANT_MEMORY."
            )

        if (
            not isinstance(reason, str)
            or len(reason.strip()) < 8
        ):
            raise TransitionRejected(
                "NO_RELEVANT_MEMORY requires an explicit HUMAN reason."
            )

        if self.state is S.MEMORY_RETRIEVAL_RUNNING:
            if (
                self.retrieval_outcome
                != RETRIEVAL_NO_RELEVANT_CANDIDATE_FOUND
            ):
                raise TransitionRejected(
                    "Direct negative memory resolution requires "
                    "NO_RELEVANT_CANDIDATE_FOUND."
                )

        elif self.state is S.MEMORY_REVIEW_REQUIRED:
            if self.retrieval_outcome != RETRIEVAL_CANDIDATES_FOUND:
                raise TransitionRejected(
                    "Post-review negative resolution requires "
                    "CANDIDATES_FOUND."
                )

            selection = self.memory_selection_artifact
            if selection is None:
                raise TransitionRejected(
                    "HUMAN must review all candidates before "
                    "NO_RELEVANT_MEMORY."
                )

            self._validate_memory_selection_integrity(selection)

            if any(
                item.decision in self._memory_active_decisions()
                for item in selection.items
            ):
                raise TransitionRejected(
                    "NO_RELEVANT_MEMORY is impossible while HUMAN has "
                    "authorized active memory items."
                )

        else:
            raise TransitionRejected(
                "NO_RELEVANT_MEMORY can be confirmed only after retrieval "
                "or after HUMAN memory review."
            )

        self._memory_negative_resolution_authorized = True
        try:
            self.transition(
                S.NO_RELEVANT_MEMORY,
                actor,
            )
        finally:
            self._memory_negative_resolution_authorized = False

        self.memory_negative_human_reason = reason.strip()

    def record_memory_retrieval_outcome(
        self,
        outcome: str,
        actor: Actor,
        reason: str = "",
    ) -> None:
        if self.state is not S.MEMORY_RETRIEVAL_RUNNING:
            raise TransitionRejected(
                "Memory retrieval outcome can only be recorded while "
                f"{S.MEMORY_RETRIEVAL_RUNNING.value} is active."
            )

        if actor is not Actor.MEMORY:
            raise TransitionRejected(
                "Memory retrieval outcome requires MEMORY actor."
            )

        allowed_outcomes = {
            RETRIEVAL_CANDIDATES_FOUND,
            RETRIEVAL_NO_RELEVANT_CANDIDATE_FOUND,
            RETRIEVAL_TECHNICAL_ERROR,
        }

        if outcome not in allowed_outcomes:
            raise TransitionRejected(
                f"Invalid memory retrieval outcome: {outcome}"
            )

        if (
            outcome
            in {
                RETRIEVAL_NO_RELEVANT_CANDIDATE_FOUND,
                RETRIEVAL_TECHNICAL_ERROR,
            }
            and not reason.strip()
        ):
            raise TransitionRejected(
                f"{outcome} requires a preserved outcome_reason."
            )

        if self.retrieval_outcome is not None:
            if (
                self.retrieval_outcome == outcome
                and self.outcome_reason == reason
            ):
                return

            raise TransitionRejected(
                "Memory retrieval outcome is already recorded for this run."
            )

        self.retrieval_outcome = outcome
        self.outcome_reason = reason

    def resume(
        self,
        reason: str = "",
    ) -> TransitionRecord:
        if self.state is not S.SESSION_PAUSED:
            raise TransitionRejected(
                f"Resume requires {S.SESSION_PAUSED.value}; "
                f"current state is {self.state.value}"
            )

        if not self.history:
            raise TransitionRejected("Pause context incomplete")

        pause_entry = self.history[-1]

        if pause_entry.target is not S.SESSION_PAUSED:
            raise TransitionRejected("Pause history is inconsistent")

        target = pause_entry.source

        if target is S.SESSION_PAUSED:
            raise TransitionRejected("Invalid nested pause context")

        self.revision += 1

        record = TransitionRecord(
            revision=self.revision,
            source=self.state,
            target=target,
            actor=Actor.ORCHESTRATOR,
            reason=reason or f"Resume session to {target.value}",
            occurred_at=datetime.now(timezone.utc).isoformat(),
        )

        self.state = target
        self.history.append(record)

        return record

    def recover(
        self,
        reason: str = "",
    ) -> TransitionRecord:
        if self.state is not S.RECOVERY_REQUIRED:
            raise TransitionRejected(
                f"Recovery requires {S.RECOVERY_REQUIRED.value}; "
                f"current state is {self.state.value}"
            )

        if len(self.history) < 2:
            raise TransitionRejected("Recovery context incomplete")

        recovery_entry = self.history[-1]
        failure_entry = self.history[-2]

        if recovery_entry.target is not S.RECOVERY_REQUIRED:
            raise TransitionRejected("Recovery history is inconsistent")

        failure_state = recovery_entry.source

        if failure_entry.target is not failure_state:
            raise TransitionRejected("Failure provenance is inconsistent")

        failed_from = failure_entry.source

        try:
            target = resolve_recovery_target(failure_state, failed_from)
        except ValueError as exc:
            raise TransitionRejected(str(exc)) from exc

        self.revision += 1

        record = TransitionRecord(
            revision=self.revision,
            source=self.state,
            target=target,
            actor=Actor.ORCHESTRATOR,
            reason=reason or (
                f"Authorized recovery from {failure_state.value}; "
                f"failed from {failed_from.value}"
            ),
            occurred_at=datetime.now(timezone.utc).isoformat(),
        )

        self.state = target
        self.history.append(record)

        return record

    def transition(
        self,
        target: S,
        actor: Actor,
        reason: str = "",
    ) -> TransitionRecord:
        source = self.state

        if not is_static_transition_allowed(source, target):
            if source in DYNAMIC_TRANSITION_STATES:
                raise TransitionRejected(
                    f"Dynamic transition from {source.value} "
                    f"to {target.value} requires explicit recovery context."
                )

            raise TransitionRejected(
                f"Transition not allowed: "
                f"{source.value} -> {target.value}"
            )

        # Manual Transfer: SYSTEM owns the technical lock, but SYSTEM
        # may cross this transition only after HUMAN confirmed the exact
        # preliminary package. Direct transition() calls cannot bypass
        # the HUMAN confirmation contract.
        if (
            source is S.TRANSFER_CONFIRMATION_REQUIRED
            and target is S.TRANSFER_PACKAGE_LOCKED
        ):
            if actor is not Actor.SYSTEM:
                raise TransitionRejected(
                    "Manual Transfer technical lock requires SYSTEM."
                )

            package = self.manual_transfer_artifact

            if package is None:
                raise TransitionRejected(
                    "Manual Transfer technical lock requires the exact "
                    "HUMAN-confirmed package."
                )

            if package.status != "HUMAN_CONFIRMED":
                raise TransitionRejected(
                    "Manual Transfer technical lock requires prior "
                    "explicit HUMAN confirmation."
                )

            if package.confirmed_by != Actor.HUMAN.value:
                raise TransitionRejected(
                    "Manual Transfer confirmation provenance must be HUMAN."
                )

            self._manual_transfer_validate_integrity(package)

            if (
                not package.confirmed_content_hash
                or package.confirmed_content_hash != package.content_hash
            ):
                raise TransitionRejected(
                    "Manual Transfer technical lock requires the exact "
                    "HUMAN-confirmed package."
                )

            if (
                self._manual_transfer_lock_authorization_hash
                != package.content_hash
            ):
                raise TransitionRejected(
                    "Manual Transfer technical lock must be executed through "
                    "lock_manual_transfer_package()."
                )

        # Active Agentic Memory cannot begin without the exact
        # locked preliminary Manual Transfer package.
        if (
            source is S.MEMORY_RETRIEVAL_READY
            and target is S.MEMORY_RETRIEVAL_RUNNING
        ):
            preliminary = self.manual_transfer_artifact
            if (
                preliminary is None
                or preliminary.status != "LOCKED"
                or preliminary.confirmed_by != Actor.HUMAN.value
                or preliminary.locked_by != Actor.SYSTEM.value
            ):
                raise TransitionRejected(
                    "Memory retrieval requires a HUMAN-confirmed, "
                    "SYSTEM-locked preliminary Manual Transfer package."
                )

        # HUMAN confirms activation + exact manual MEMORY_TRANSFER;
        # SYSTEM alone performs the technical MEMORY_SELECTION_LOCKED.
        if (
            source is S.MEMORY_SELECTION_CONFIRMATION_REQUIRED
            and target is S.MEMORY_SELECTION_LOCKED
        ):
            if actor is not Actor.SYSTEM:
                raise TransitionRejected(
                    "MEMORY_SELECTION_LOCKED requires SYSTEM."
                )

            selection = self.memory_selection_artifact
            package = self.memory_transfer_artifact

            if selection is None or package is None:
                raise TransitionRejected(
                    "Memory technical lock requires persisted Selection "
                    "and MEMORY_TRANSFER artifacts."
                )

            if (
                selection.status != "HUMAN_CONFIRMED"
                or package.status != "HUMAN_CONFIRMED"
            ):
                raise TransitionRejected(
                    "Memory technical lock requires prior explicit "
                    "HUMAN confirmation."
                )

            if (
                selection.confirmed_by != Actor.HUMAN.value
                or package.confirmed_by != Actor.HUMAN.value
            ):
                raise TransitionRejected(
                    "Memory confirmation provenance must be HUMAN."
                )

            self._validate_memory_selection_integrity(selection)
            self._validate_memory_transfer_integrity(package)

            if (
                selection.confirmed_content_hash != selection.content_hash
                or package.confirmed_content_hash != package.content_hash
            ):
                raise TransitionRejected(
                    "Memory technical lock requires the exact "
                    "HUMAN-confirmed content."
                )

            required_authorization = (
                selection.content_hash + ":" + package.content_hash
            )

            if (
                self._memory_selection_lock_authorization_hash
                != required_authorization
            ):
                raise TransitionRejected(
                    "Memory technical lock must be executed through "
                    "lock_memory_selection()."
                )

        # NO_RELEVANT_MEMORY is a HUMAN protocol resolution,
        # never an automatic interpretation of retrieval or score.
        if (
            target is S.NO_RELEVANT_MEMORY
            and source in {
                S.MEMORY_RETRIEVAL_RUNNING,
                S.MEMORY_REVIEW_REQUIRED,
            }
            and not self._memory_negative_resolution_authorized
        ):
            raise TransitionRejected(
                "NO_RELEVANT_MEMORY requires explicit HUMAN resolution "
                "through confirm_no_relevant_memory()."
            )

        # Final Reconstruction Package must exist before
        # ORCHESTRATOR may open the HUMAN confirmation gate.
        if (
            source is S.RECONSTRUCTION_PACKAGE_PREPARATION
            and target
            is S.RECONSTRUCTION_PACKAGE_CONFIRMATION_REQUIRED
        ):
            package = self.reconstruction_package_artifact

            if package is None or package.status != "DRAFT":
                raise TransitionRejected(
                    "Reconstruction confirmation gate requires a "
                    "persisted DRAFT Final Reconstruction Package."
                )

            self._validate_final_reconstruction_package_integrity(
                package,
                verify_live_sources=True,
            )

        # HUMAN confirms cognition/content; SYSTEM alone executes
        # the technical READY lock through the canonical method.
        if (
            source
            is S.RECONSTRUCTION_PACKAGE_CONFIRMATION_REQUIRED
            and target is S.RECONSTRUCTION_PACKAGE_READY
        ):
            if actor is not Actor.SYSTEM:
                raise TransitionRejected(
                    "RECONSTRUCTION_PACKAGE_READY requires SYSTEM."
                )

            package = self.reconstruction_package_artifact

            if package is None:
                raise TransitionRejected(
                    "Reconstruction technical lock requires package."
                )

            if (
                package.status != "HUMAN_CONFIRMED"
                or package.confirmed_by
                != Actor.HUMAN.value
            ):
                raise TransitionRejected(
                    "Reconstruction technical lock requires prior "
                    "explicit HUMAN confirmation."
                )

            self._validate_final_reconstruction_package_integrity(
                package,
                verify_live_sources=True,
            )

            if (
                package.confirmed_content_hash
                != package.content_hash
            ):
                raise TransitionRejected(
                    "Reconstruction technical lock requires the exact "
                    "HUMAN-confirmed package."
                )

            if (
                self._reconstruction_package_lock_authorization_hash
                != package.content_hash
            ):
                raise TransitionRejected(
                    "Reconstruction technical lock must be executed "
                    "through lock_final_reconstruction_package()."
                )

        # Builder Reconstruction can start only from the exact
        # HUMAN-confirmed and SYSTEM-locked package.
        if (
            source is S.RECONSTRUCTION_PACKAGE_READY
            and target is S.RECONSTRUCTION_RUNNING
        ):
            package = self.reconstruction_package_artifact

            if package is None:
                raise TransitionRejected(
                    "Reconstruction cannot run without Final "
                    "Reconstruction Package."
                )

            if (
                package.status != "LOCKED"
                or package.confirmed_by
                != Actor.HUMAN.value
                or package.locked_by
                != Actor.SYSTEM.value
            ):
                raise TransitionRejected(
                    "Reconstruction requires a HUMAN-confirmed, "
                    "SYSTEM-locked package."
                )

            self._validate_final_reconstruction_package_integrity(
                package,
                verify_live_sources=True,
            )

        if (
            (source, target) in HUMAN_AUTHORITY_TRANSITIONS
            and actor is not Actor.HUMAN
        ):
            raise TransitionRejected(
                f"Human authority required: "
                f"{source.value} -> {target.value}"
            )

        required_actor = AGENT_OWNED_TRANSITIONS.get((source, target))
        if required_actor is not None and actor is not required_actor:
            raise TransitionRejected(
                f"Agent ownership required: "
                f"{source.value} -> {target.value} requires "
                f"{required_actor.value}"
            )

        if (
            source is S.CRITIC_REVIEW_GENERATED
            and target is S.CONFLICT_SPACE_READY
            and self.conflict_space_artifact is None
        ):
            raise TransitionRejected(
                "CONFLICT_SPACE_READY requires a persisted Conflict Space."
            )

        if (
            source is S.CONFLICT_SPACE_READY
            and target is S.HUMAN_CRITIC_SELECTION
            and self.conflict_space_artifact is None
        ):
            raise TransitionRejected(
                "HUMAN_CRITIC_SELECTION requires a persisted Conflict Space."
            )

        if (
            source is S.HUMAN_CRITIC_SELECTION
            and target in {
                S.CRITIC_CLARIFICATION_REQUIRED,
                S.MANUAL_TRANSFER_PREPARATION,
                S.SESSION_PAUSED,
            }
            and self.human_critic_selection_artifact is None
        ):
            raise TransitionRejected(
                "Leaving HUMAN_CRITIC_SELECTION requires explicit persisted HUMAN decisions."
            )

        if not self._vf_precheck_transition_allowed(
            source,
            target,
        ):
            raise TransitionRejected(
                "VF precheck transition rejected: target is not the "
                "current deterministic precheck target."
            )

        if not self._vf_human_declaration_allows_declared(
            source,
            target,
        ):
            raise TransitionRejected(
                "VF_DECLARED requires a complete HUMAN declaration "
                "recorded for the current revision."
            )

        if not self._vf_final_integrity_allows_locking(
            source,
            target,
        ):
            raise TransitionRejected(
                "VF_LOCKING_IN_PROGRESS requires a complete positive "
                "final integrity result for the current revision."
            )

        if not self._vf_selected_result_allows_locked(
            source,
            target,
        ):
            raise TransitionRejected(
                "VF_LOCKED requires the exact HUMAN-selected ResultVersion "
                "with matching session, UUID, label, and SHA-256."
            )

        if source is S.MEMORY_RETRIEVAL_RUNNING:
            if (
                target is S.MEMORY_REVIEW_REQUIRED
                and self.retrieval_outcome != RETRIEVAL_CANDIDATES_FOUND
            ):
                raise TransitionRejected(
                    "MEMORY_REVIEW_REQUIRED requires "
                    "retrieval_outcome=CANDIDATES_FOUND."
                )

            if (
                target is S.NO_RELEVANT_MEMORY
                and self.retrieval_outcome
                != RETRIEVAL_NO_RELEVANT_CANDIDATE_FOUND
            ):
                raise TransitionRejected(
                    "NO_RELEVANT_MEMORY from retrieval requires "
                    "retrieval_outcome=NO_RELEVANT_CANDIDATE_FOUND."
                )

            if (
                target is S.MEMORY_RETRIEVAL_FAILED
                and self.retrieval_outcome != RETRIEVAL_TECHNICAL_ERROR
            ):
                raise TransitionRejected(
                    "MEMORY_RETRIEVAL_FAILED requires "
                    "retrieval_outcome=TECHNICAL_ERROR."
                )

        if (
            source is S.MEMORY_REVIEW_REQUIRED
            and target is S.NO_RELEVANT_MEMORY
            and self.retrieval_outcome != RETRIEVAL_CANDIDATES_FOUND
        ):
            raise TransitionRejected(
                "NO_RELEVANT_MEMORY after human review requires a prior "
                "retrieval_outcome=CANDIDATES_FOUND."
            )

        if (
            source is S.MEMORY_RETRIEVAL_READY
            and target is S.MEMORY_RETRIEVAL_RUNNING
        ):
            self.retrieval_outcome = None
            self.outcome_reason = ""
            self.memory_resolution_outcome = None
            self.negative_result_reason = ""

        if (
            source is S.MEMORY_RETRIEVAL_RUNNING
            and target is S.NO_RELEVANT_MEMORY
        ):
            self.memory_resolution_outcome = (
                MEMORY_RESOLUTION_NO_RELEVANT_MEMORY
            )
            self.negative_result_reason = (
                NEGATIVE_REASON_NO_RELEVANT_CANDIDATE_FOUND
            )

        if (
            source is S.MEMORY_REVIEW_REQUIRED
            and target is S.NO_RELEVANT_MEMORY
        ):
            self.memory_resolution_outcome = (
                MEMORY_RESOLUTION_NO_RELEVANT_MEMORY
            )
            self.negative_result_reason = (
                NEGATIVE_REASON_ZERO_ITEMS_AUTHORIZED_AFTER_HUMAN_REVIEW
            )

        vf_lock_version_id: str | None = None
        vf_lock_content_hash: str | None = None

        if (
            source is S.VF_LOCKING_IN_PROGRESS
            and target is S.VF_LOCKED
        ):
            declaration = self.vf_human_declaration

            if declaration is None:
                raise TransitionRejected(
                    "VF_LOCKED requires the HUMAN VF declaration."
                )

            vf_lock_version_id = (
                declaration.selected_version_id
            )
            vf_lock_content_hash = (
                declaration.selected_version_content_hash
            )

        if not self._final_report_allows_ready(
            source,
            target,
        ):
            raise TransitionRejected(
                "FINAL_REPORT_READY requires a valid report bound "
                "to the exact locked VF for the current revision."
            )

        if not self._final_report_review_allows_archive(
            source,
            target,
        ):
            raise TransitionRejected(
                "SESSION_ARCHIVED requires a current HUMAN-confirmed "
                "FinalReport review."
            )

        if not self._final_report_review_allows_regeneration(
            source,
            target,
        ):
            raise TransitionRejected(
                "FINAL_REPORT_GENERATION retry requires a current HUMAN "
                "CORRECTED or CONTESTED FinalReport review."
            )

        self.revision += 1

        record = TransitionRecord(
            revision=self.revision,
            source=source,
            target=target,
            actor=actor,
            reason=reason,
            occurred_at=datetime.now(timezone.utc).isoformat(),
        )

        if vf_lock_version_id is not None:
            self.vf_locked_version_id = vf_lock_version_id
            self.vf_locked_content_hash = (
                vf_lock_content_hash
            )

        self.state = target
        self.history.append(record)

        return record


def _self_test() -> None:
    orchestrator = SystemOrchestrator()

    orchestrator.transition(
        S.DIRECTION_DRAFT,
        Actor.ORCHESTRATOR,
    )
    orchestrator.transition(
        S.DIRECTION_VALIDATION_REQUIRED,
        Actor.ORCHESTRATOR,
    )
    orchestrator.transition(
        S.DIRECTION_CONFIRMATION_REQUIRED,
        Actor.ORCHESTRATOR,
    )

    try:
        orchestrator.transition(
            S.DIRECTION_LOCKED,
            Actor.ORCHESTRATOR,
        )
    except TransitionRejected:
        pass
    else:
        raise AssertionError(
            "Orchestrator incorrectly crossed a human authority gate."
        )

    orchestrator.transition(
        S.DIRECTION_LOCKED,
        Actor.HUMAN,
        reason="Human confirmed and locked direction.",
    )

    orchestrator.transition(
        S.BUILDER_V1_PACKAGE_PREPARATION,
        Actor.ORCHESTRATOR,
    )
    orchestrator.transition(
        S.BUILDER_V1_READY,
        Actor.ORCHESTRATOR,
    )
    orchestrator.transition(
        S.BUILDER_V1_RUNNING,
        Actor.ORCHESTRATOR,
    )
    orchestrator.transition(
        S.V1_GENERATED,
        Actor.BUILDER_AI,
    )

    try:
        orchestrator.transition(
            S.CRITIC_RUNNING,
            Actor.ORCHESTRATOR,
        )
    except TransitionRejected:
        pass
    else:
        raise AssertionError(
            "Critic was allowed before mandatory human response."
        )

    orchestrator.transition(
        S.HUMAN_RESPONSE_REQUIRED,
        Actor.ORCHESTRATOR,
    )

    assert orchestrator.revision == 9
    assert len(orchestrator.history) == 9


if __name__ == "__main__":
    _self_test()




def _validate_agent_ownership() -> None:
    for (source, target), required_actor in AGENT_OWNED_TRANSITIONS.items():
        test = SystemOrchestrator(state=source)

        wrong_actors = {
            Actor.HUMAN,
            Actor.BUILDER_AI,
            Actor.CRITIC_AI,
            Actor.MEMORY,
            Actor.ORCHESTRATOR,
            Actor.SYSTEM,
        } - {required_actor}

        for wrong_actor in wrong_actors:
            if test.can_transition(target, wrong_actor):
                raise AssertionError(
                    f"{wrong_actor.value} incorrectly allowed for "
                    f"{source.value} -> {target.value}"
                )


if __name__ == "__main__":
    _validate_agent_ownership()
