from dataclasses import dataclass, field
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
        S.RECONSTRUCTION_PACKAGE_READY,
    ),

    (
        S.HUMAN_VERIFICATION_REQUIRED,
        S.VF_CONFIRMATION_REQUIRED,
    ),

    (
        S.VF_CONFIRMATION_REQUIRED,
        S.VF_HUMAN_DECLARATION,
    ),

    (
        S.VF_HUMAN_DECLARATION,
        S.VF_DECLARED,
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
    (S.RECONSTRUCTION_RUNNING, S.VN_GENERATED): Actor.BUILDER_AI,
    (S.VN_GENERATED, S.VERSION_COMPARISON_READY): Actor.ORCHESTRATOR,
    (S.VERSION_COMPARISON_READY, S.VERSION_COMPARISON_GENERATED): Actor.ORCHESTRATOR,
    (S.VERSION_COMPARISON_GENERATED, S.HUMAN_VERIFICATION_REQUIRED): Actor.ORCHESTRATOR,
}


@dataclass(frozen=True)
class TransitionRecord:
    revision: int
    source: S
    target: S
    actor: Actor
    reason: str
    occurred_at: str


@dataclass
class SystemOrchestrator:
    state: S = S.SESSION_CREATED
    revision: int = 0
    history: list[TransitionRecord] = field(default_factory=list)
    retrieval_outcome: str | None = None
    outcome_reason: str = ""
    memory_resolution_outcome: str | None = None
    negative_result_reason: str = ""

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

        return True

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

        self.revision += 1

        record = TransitionRecord(
            revision=self.revision,
            source=source,
            target=target,
            actor=actor,
            reason=reason,
            occurred_at=datetime.now(timezone.utc).isoformat(),
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
