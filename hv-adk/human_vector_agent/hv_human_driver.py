from __future__ import annotations

from typing import Any

from human_vector.orchestrator import Actor

from .hv_e2e_coordinator import (
    CoordinatorAction,
    CoordinatorDecision,
    next_action,
)


def human_action_status(orchestrator: Any) -> CoordinatorDecision:
    # Return coordinator status without executing HUMAN authority.
    return next_action(orchestrator)


def _require_human_gate(orchestrator: Any) -> CoordinatorDecision:
    decision = next_action(orchestrator)

    if decision.action is not CoordinatorAction.HUMAN_REQUIRED:
        raise RuntimeError(
            "HUMAN action rejected by coordinator gate: "
            f"state={decision.state}; "
            f"action={decision.action.value}; "
            f"phase={decision.phase}."
        )

    return decision


def submit_human_iteration_decision(
    orchestrator: Any,
    *,
    reason: str,
    evolved_criteria: str,
    requested_changes: str,
) -> Any:
    # Execute only an explicitly supplied HUMAN iteration decision.
    _require_human_gate(orchestrator)

    return orchestrator.record_human_iteration_decision(
        reason=reason,
        evolved_criteria=evolved_criteria,
        requested_changes=requested_changes,
        actor=Actor.HUMAN,
    )


def submit_human_verification(
    orchestrator: Any,
    *,
    candidate_version_id: str,
    candidate_version_label: str,
    candidate_content_hash: str,
    evidence_sufficient: bool,
    verification_note: str,
) -> Any:
    # Record HUMAN verification against one exact candidate identity.
    _require_human_gate(orchestrator)

    return orchestrator.record_human_verification(
        candidate_version_id=candidate_version_id,
        candidate_version_label=candidate_version_label,
        candidate_content_hash=candidate_content_hash,
        evidence_sufficient=evidence_sufficient,
        verification_note=verification_note,
        actor=Actor.HUMAN,
    )


def submit_vf_human_reconsideration(
    orchestrator: Any,
    *,
    reason: str,
    evolved_criteria: str,
    requested_changes: str,
) -> Any:
    # Execute explicit HUMAN reconsideration before final lock.
    _require_human_gate(orchestrator)

    return orchestrator.record_vf_human_reconsideration(
        reason=reason,
        evolved_criteria=evolved_criteria,
        requested_changes=requested_changes,
        actor=Actor.HUMAN,
    )


def submit_vf_human_declaration(
    orchestrator: Any,
    *,
    selected_version: str,
    selected_version_id: str,
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
) -> Any:
    # HUMAN-readable version label plus mandatory exact technical identity.
    _require_human_gate(orchestrator)

    if (
        not isinstance(selected_version, str)
        or not selected_version.strip()
    ):
        raise ValueError(
            "selected_version must be a non-empty string."
        )

    if (
        not isinstance(selected_version_id, str)
        or not selected_version_id.strip()
    ):
        raise ValueError(
            "selected_version_id is required for exact HUMAN VF identity."
        )

    return orchestrator.record_vf_human_declaration(
        selected_version=selected_version.strip(),
        selected_version_id=selected_version_id.strip(),
        choice_reason=choice_reason,
        relation_to_initial_direction=relation_to_initial_direction,
        decisive_human_contribution=decisive_human_contribution,
        integrated_builder_elements=integrated_builder_elements,
        decisive_critics=decisive_critics,
        rejected_critics=rejected_critics,
        memory_basis=memory_basis,
        verifications_performed=verifications_performed,
        remaining_risks_and_uncertainties=remaining_risks_and_uncertainties,
        preserved_contradictions=preserved_contradictions,
        intended_use=intended_use,
        decision_assumption=decision_assumption,
        actor=Actor.HUMAN,
    )
