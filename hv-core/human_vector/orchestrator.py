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
        S.TRANSFER_CONFIRMATION_REQUIRED,
        S.TRANSFER_PACKAGE_LOCKED,
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
        S.MEMORY_SELECTION_CONFIRMATION_REQUIRED,
        S.MEMORY_SELECTION_LOCKED,
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
        S.RECONSTRUCTION_PACKAGE_CONFIRMATION_REQUIRED,
        S.RECONSTRUCTION_PACKAGE_READY,
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
    (S.TRANSFER_PACKAGE_LOCKED, S.MEMORY_RETRIEVAL_READY): Actor.ORCHESTRATOR,
    (S.CRITIC_RUNNING, S.CRITIC_REVIEW_GENERATED): Actor.CRITIC_AI,
    (S.MEMORY_RETRIEVAL_READY, S.MEMORY_RETRIEVAL_RUNNING): Actor.ORCHESTRATOR,
    (S.MEMORY_RETRIEVAL_RUNNING, S.MEMORY_REVIEW_REQUIRED): Actor.MEMORY,
    (S.MEMORY_RETRIEVAL_RUNNING, S.MEMORY_RETRIEVAL_FAILED): Actor.MEMORY,
    (S.MEMORY_SELECTION_LOCKED, S.RECONSTRUCTION_PACKAGE_PREPARATION): Actor.ORCHESTRATOR,
    (S.NO_RELEVANT_MEMORY, S.RECONSTRUCTION_PACKAGE_PREPARATION): Actor.ORCHESTRATOR,
    (S.RECONSTRUCTION_PACKAGE_PREPARATION, S.RECONSTRUCTION_PACKAGE_CONFIRMATION_REQUIRED): Actor.ORCHESTRATOR,
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


@dataclass
class SystemOrchestrator:
    state: S = S.SESSION_CREATED
    revision: int = 0
    history: list[TransitionRecord] = field(default_factory=list)
    session_id: str | None = None
    result_versions: dict[str, ResultVersion] = field(default_factory=dict)
    human_direction_artifact: HumanDirection | None = None
    human_direction_history: list[HumanDirection] = field(default_factory=list)
    human_response_artifact: HumanCognitiveResponse | None = None
    human_response_history: list[HumanCognitiveResponse] = field(default_factory=list)
    critic_package_artifact: CriticAnalysisPackage | None = None
    critic_package_history: list[CriticAnalysisPackage] = field(default_factory=list)
    critic_review_artifact: CriticReview | None = None
    critic_review_history: list[CriticReview] = field(default_factory=list)
    vf_locked_version_id: str | None = None
    vf_locked_content_hash: str | None = None
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
