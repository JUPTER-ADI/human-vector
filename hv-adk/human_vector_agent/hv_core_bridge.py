import json
from dataclasses import asdict
from uuid import UUID, uuid4
from google.adk.tools import ToolContext
from human_vector.orchestrator import Actor, SystemOrchestrator, TransitionRejected
from human_vector.states import HumanVectorState as S

_orchestrator = SystemOrchestrator()


def bind_orchestrator(orchestrator: SystemOrchestrator) -> dict:
    """Bind the ADK bridge to an existing HUMAN VECTOR CORE session.

    Technical binding only: no copy, state transition, cognitive action,
    artefact mutation, or HUMAN impersonation is performed.
    """
    global _orchestrator

    if not isinstance(orchestrator, SystemOrchestrator):
        raise TypeError(
            "bind_orchestrator requires an existing SystemOrchestrator instance."
        )

    _orchestrator = orchestrator

    return {
        "ok": True,
        "same_instance": _orchestrator is orchestrator,
        "state": _orchestrator.state.value,
        "revision": _orchestrator.revision,
        "history_length": len(_orchestrator.history),
        "final_authority": "HUMAN",
    }


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

def record_builder_v1_from_state(tool_context: ToolContext) -> dict:
    """Record the exact Builder V1 saved by ADK output_key.

    The orchestrator does not receive V1 content as an LLM-supplied argument.
    It reads the exact Builder AI final response directly from session state.
    """
    v1_content = tool_context.state.get("hv_builder_v1_output")

    if not isinstance(v1_content, str) or not v1_content.strip():
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": (
                "No exact Builder V1 output is available in ADK session state."
            ),
            "builder_output_key": "hv_builder_v1_output",
            "final_authority": "HUMAN",
        }

    result = record_builder_v1(v1_content, tool_context)
    result["builder_output_key"] = "hv_builder_v1_output"
    result["builder_output_source"] = "ADK_SESSION_STATE"
    return result

def prepare_builder_v1_direction(tool_context: ToolContext) -> dict:
    """Bind the exact confirmed Human Direction to ADK state for Builder V1.

    This operation is technical only. It does not create, modify, confirm,
    summarize, or reinterpret Human Direction.
    """
    from hashlib import sha256

    if _orchestrator.state is not S.BUILDER_V1_RUNNING:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": (
                "Builder direction package can only be prepared from "
                "BUILDER_V1_RUNNING."
            ),
            "final_authority": "HUMAN",
        }

    direction = _orchestrator.human_direction_artifact

    if (
        direction is None
        or direction.status != "CONFIRMED"
        or direction.confirmed_revision is None
    ):
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": (
                "Builder V1 requires an explicitly confirmed "
                "Human Direction artefact."
            ),
            "final_authority": "HUMAN",
        }

    package = (
        "HUMAN VECTOR — CONFIRMED HUMAN DIRECTION\n"
        f"DIRECTION_ID: {direction.direction_id}\n"
        f"CONFIRMED_REVISION: {direction.confirmed_revision}\n"
        "\nOBJECTIVE:\n"
        f"{direction.objective}\n"
        "\nCONTEXT:\n"
        f"{direction.context}\n"
        "\nCRITERIA:\n"
        f"{direction.criteria}\n"
        "\nLIMITS:\n"
        f"{direction.limits}\n"
        "\nFACTS:\n"
        f"{direction.facts}\n"
        "\nASSUMPTIONS:\n"
        f"{direction.assumptions}\n"
        "\nINTENDED_USE:\n"
        f"{direction.intended_use}\n"
    )

    package_hash = sha256(
        package.encode("utf-8")
    ).hexdigest()

    tool_context.state[
        "hv_builder_direction_package"
    ] = package

    tool_context.state[
        "hv_builder_direction_id"
    ] = direction.direction_id

    tool_context.state[
        "hv_builder_direction_confirmed_revision"
    ] = direction.confirmed_revision

    tool_context.state[
        "hv_builder_direction_sha256"
    ] = package_hash

    return {
        "ok": True,
        "state": _orchestrator.state.value,
        "direction_id": direction.direction_id,
        "confirmed_revision": direction.confirmed_revision,
        "direction_sha256": package_hash,
        "builder_input_source": "CONFIRMED_HUMAN_DIRECTION",
        "exact_human_wording_preserved": True,
        "final_authority": "HUMAN",
    }
def prepare_critic_analysis(
    verified_elements: str,
    unverified_elements: str,
    relevant_principles: str,
    tool_context: ToolContext,
) -> dict:
    """Bind the exact CORE CriticAnalysisPackage into ADK session state.

    ORCHESTRATOR performs only the technical Critic setup:
    HUMAN_RESPONSE_CAPTURED -> CRITIC_PACKAGE_PREPARATION
    -> CRITIC_READY -> CRITIC_RUNNING.

    This function does not create, rewrite, approve, select, or transfer
    any HUMAN contribution or Critic criticism.
    """
    if _orchestrator.state is not S.HUMAN_RESPONSE_CAPTURED:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": (
                "Critic analysis can only start from "
                "HUMAN_RESPONSE_CAPTURED."
            ),
            "final_authority": "HUMAN",
        }

    try:
        _orchestrator.prepare_critic_package(
            verified_elements=verified_elements,
            unverified_elements=unverified_elements,
            relevant_principles=relevant_principles,
            actor=Actor.ORCHESTRATOR,
        )
        _orchestrator.mark_critic_ready(
            actor=Actor.ORCHESTRATOR,
        )
        package = _orchestrator.start_critic_running(
            actor=Actor.ORCHESTRATOR,
        )
    except TransitionRejected as exc:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": str(exc),
            "final_authority": "HUMAN",
        }

    package_json = json.dumps(
        asdict(package),
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )

    tool_context.state["hv_critic_analysis_package"] = package_json
    tool_context.state["hv_critic_input_source"] = "CORE_CRITIC_ANALYSIS_PACKAGE"

    return {
        "ok": True,
        "state": _orchestrator.state.value,
        "critic_input_key": "hv_critic_analysis_package",
        "critic_input_source": "CORE_CRITIC_ANALYSIS_PACKAGE",
        "package": package_json,
        "final_authority": "HUMAN",
    }


def record_critic_review_from_state(
    tool_context: ToolContext,
) -> dict:
    """Record the exact Critic Gemini output saved by ADK output_key.

    The ORCHESTRATOR does not receive Critic content as an LLM-supplied
    argument. It reads the exact Critic output directly from ADK state,
    parses the structured criticisms, and records both the criticisms
    and the untouched raw output in CORE.
    """
    if _orchestrator.state is not S.CRITIC_RUNNING:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": (
                "Critic review can only be recorded from CRITIC_RUNNING."
            ),
            "final_authority": "HUMAN",
        }

    raw_output = tool_context.state.get("hv_critic_output")

    if not isinstance(raw_output, str) or not raw_output.strip():
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": "No exact Critic output is available in ADK session state.",
            "critic_output_key": "hv_critic_output",
            "final_authority": "HUMAN",
        }

    candidate = raw_output.strip()

    # Accept a fenced JSON response for runtime robustness while preserving
    # the original raw Gemini output unchanged for provenance/hash in CORE.
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        candidate = "\n".join(lines).strip()

    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": f"Critic output is not valid JSON: {exc}",
            "critic_output_key": "hv_critic_output",
            "final_authority": "HUMAN",
        }

    if not isinstance(payload, dict):
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": "Critic output must be a JSON object.",
            "final_authority": "HUMAN",
        }

    criticisms = payload.get("criticisms")

    if not isinstance(criticisms, list) or not criticisms:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": (
                "Critic output must contain a non-empty "
                "'criticisms' list."
            ),
            "final_authority": "HUMAN",
        }

    try:
        review = _orchestrator.record_critic_review(
            criticisms=criticisms,
            raw_output=raw_output,
            actor=Actor.CRITIC_AI,
        )
    except (TransitionRejected, ValueError, TypeError) as exc:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": str(exc),
            "final_authority": "HUMAN",
        }

    tool_context.state["hv_critic_review_recorded"] = True

    return {
        "ok": True,
        "state": _orchestrator.state.value,
        "critic_output_key": "hv_critic_output",
        "critic_output_source": "ADK_SESSION_STATE",
        "criticism_count": len(review.criticisms),
        "final_authority": "HUMAN",
    }


def prepare_builder_vn_reconstruction(
    tool_context: ToolContext,
) -> dict:
    """
    Bind the exact HUMAN-confirmed, SYSTEM-locked Final Reconstruction
    Package to ADK session state and open Builder Reconstruction.

    This function performs no HUMAN cognitive act.
    """
    if _orchestrator.state is not S.RECONSTRUCTION_PACKAGE_READY:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": (
                "Builder Vn preparation requires "
                "RECONSTRUCTION_PACKAGE_READY."
            ),
            "final_authority": "HUMAN",
        }

    package = _orchestrator.reconstruction_package_artifact

    if package is None:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": "Final Reconstruction Package is missing.",
            "final_authority": "HUMAN",
        }

    if (
        package.status != "LOCKED"
        or package.confirmed_by != Actor.HUMAN.value
        or package.locked_by != Actor.SYSTEM.value
    ):
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": (
                "Builder Vn requires the exact HUMAN-confirmed, "
                "SYSTEM-locked Final Reconstruction Package."
            ),
            "final_authority": "HUMAN",
        }

    try:
        _orchestrator._validate_final_reconstruction_package_integrity(
            package,
            verify_live_sources=True,
        )
    except (TransitionRejected, ValueError, TypeError) as exc:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": str(exc),
            "final_authority": "HUMAN",
        }

    package_state = asdict(package)

    try:
        _orchestrator.transition(
            S.RECONSTRUCTION_RUNNING,
            Actor.ORCHESTRATOR,
            reason=(
                "Open Builder Vn execution from exact locked "
                "Final Reconstruction Package."
            ),
        )
    except TransitionRejected as exc:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": str(exc),
            "final_authority": "HUMAN",
        }

    # State mutation happens only after CORE accepted the transition.
    tool_context.state["hv_builder_vn_reconstruction_package"] = (
        package_state
    )
    tool_context.state[
        "hv_builder_vn_reconstruction_package_hash"
    ] = package.content_hash
    tool_context.state["hv_builder_vn_input_source"] = (
        "LOCKED_FINAL_RECONSTRUCTION_PACKAGE"
    )

    # A previous/stale model output must never authorize a new Vn.
    tool_context.state["hv_builder_vn_output"] = None
    tool_context.state["hv_builder_vn_recorded"] = None

    return {
        "ok": True,
        "state": _orchestrator.state.value,
        "reconstruction_package_id": package.package_id,
        "reconstruction_package_revision": package.package_revision,
        "reconstruction_package_hash": package.content_hash,
        "builder_input_source":
            "LOCKED_FINAL_RECONSTRUCTION_PACKAGE",
        "builder_output_key": "hv_builder_vn_output",
        "final_authority": "HUMAN",
    }


def _next_builder_vn_label(package) -> str:
    # The exact package base determines the next version.
    # Retained history remains provenance only and cannot
    # force a jump in numbering.

    base_label = getattr(
        package,
        "iteration_base_version_label",
        "",
    )

    # Historical package revision 1 predates the explicit
    # iteration_base_version_* fields.
    if not isinstance(base_label, str) or not base_label.strip():
        if getattr(package, "package_revision", 0) == 1:
            base_label = getattr(
                package,
                "source_version_label",
                "",
            )
        else:
            raise TransitionRejected(
                "Builder Vn requires an explicit iteration base "
                "version label."
            )

    if not isinstance(base_label, str):
        raise TransitionRejected(
            "Builder Vn iteration base label must be a string."
        )

    base_label = base_label.strip()

    if not base_label.startswith("V"):
        raise TransitionRejected(
            "Builder Vn iteration base label must be an exact Vn label."
        )

    numeric = base_label[1:]

    if (
        not numeric
        or not numeric.isdigit()
        or numeric.startswith("0")
    ):
        raise TransitionRejected(
            "Builder Vn iteration base label must be an exact Vn label."
        )

    base_number = int(numeric)

    if base_number < 1:
        raise TransitionRejected(
            "Builder Vn iteration base label must be an exact Vn label."
        )

    return f"V{base_number + 1}"


def record_builder_vn_from_state(
    tool_context: ToolContext,
) -> dict:
    """
    Record the exact Gemini Builder Vn output from ADK session state.

    The root agent cannot provide or rewrite the output as an argument.
    """
    import hashlib

    if _orchestrator.state is not S.RECONSTRUCTION_RUNNING:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": (
                "Builder Vn recording requires RECONSTRUCTION_RUNNING."
            ),
            "final_authority": "HUMAN",
        }

    package = _orchestrator.reconstruction_package_artifact

    if package is None:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": "Final Reconstruction Package is missing.",
            "final_authority": "HUMAN",
        }

    if (
        package.status != "LOCKED"
        or package.confirmed_by != Actor.HUMAN.value
        or package.locked_by != Actor.SYSTEM.value
    ):
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": (
                "Builder Vn recording requires the locked "
                "Final Reconstruction Package."
            ),
            "final_authority": "HUMAN",
        }

    try:
        _orchestrator._validate_final_reconstruction_package_integrity(
            package,
            verify_live_sources=True,
        )
    except (TransitionRejected, ValueError, TypeError) as exc:
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": str(exc),
            "final_authority": "HUMAN",
        }

    expected_package = asdict(package)

    adk_package = tool_context.state.get(
        "hv_builder_vn_reconstruction_package"
    )

    adk_package_hash = tool_context.state.get(
        "hv_builder_vn_reconstruction_package_hash"
    )

    if (
        adk_package != expected_package
        or adk_package_hash != package.content_hash
    ):
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": (
                "ADK Builder Vn input does not match the exact locked "
                "Final Reconstruction Package."
            ),
            "final_authority": "HUMAN",
        }

    raw_output = tool_context.state.get("hv_builder_vn_output")

    if not isinstance(raw_output, str) or not raw_output.strip():
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": (
                "Exact Builder Vn output is missing from "
                "hv_builder_vn_output."
            ),
            "builder_output_key": "hv_builder_vn_output",
            "final_authority": "HUMAN",
        }

    if tool_context.state.get("hv_builder_vn_recorded"):
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": "Builder Vn output was already recorded.",
            "final_authority": "HUMAN",
        }

    version_label = _next_builder_vn_label(package)

    core_session_id = str(
        _orchestrator.session_id or package.session_id
    )

    try:
        UUID(core_session_id)
    except (ValueError, TypeError, AttributeError):
        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": "Builder Vn requires a valid session UUID.",
            "final_authority": "HUMAN",
        }

    before_versions = dict(_orchestrator.result_versions)

    try:
        _orchestrator.transition(
            S.VN_GENERATED,
            Actor.BUILDER_AI,
            reason=(
                f"Builder AI generated exact reconstruction "
                f"{version_label}."
            ),
        )

        result = _orchestrator.record_result_version(
            session_id=core_session_id,
            version_label=version_label,
            content=raw_output,
            actor=Actor.BUILDER_AI,
        )

        exact_hash = hashlib.sha256(
            raw_output.encode("utf-8")
        ).hexdigest()

        if result.content != raw_output:
            raise TransitionRejected(
                "CORE ResultVersion does not preserve exact "
                "Builder Vn output."
            )

        if result.content_hash != exact_hash:
            raise TransitionRejected(
                "CORE Vn hash does not match exact Gemini output."
            )

    except (TransitionRejected, ValueError, TypeError) as exc:
        _orchestrator.result_versions = before_versions

        return {
            "ok": False,
            "state": _orchestrator.state.value,
            "reason": str(exc),
            "final_authority": "HUMAN",
        }

    tool_context.state["hv_builder_vn_recorded"] = True
    tool_context.state["hv_builder_vn_version_id"] = result.version_id
    tool_context.state["hv_builder_vn_version_label"] = (
        result.version_label
    )
    tool_context.state["hv_builder_vn_content_hash"] = (
        result.content_hash
    )

    return {
        "ok": True,
        "state": _orchestrator.state.value,
        "builder_output_key": "hv_builder_vn_output",
        "builder_input_source":
            "LOCKED_FINAL_RECONSTRUCTION_PACKAGE",
        "version_id": result.version_id,
        "version_label": result.version_label,
        "content_hash": result.content_hash,
        "exact_output_preserved": result.content == raw_output,
        "final_authority": "HUMAN",
    }

_HV_FIRESTORE_PERSISTENT_MEMORY_BRIDGE_V1 = "HV_FIRESTORE_PERSISTENT_MEMORY_BRIDGE_V1"


def retrieve_firestore_memory_candidates_to_core(
    *,
    project_id: str,
    document_paths: list[str],
    query_basis: str,
    database: str = "(default)",
) -> dict:
    import hashlib
    import json
    from dataclasses import asdict, is_dataclass

    import google.auth
    from google.cloud import firestore

    from human_vector.orchestrator import Actor

    if not isinstance(project_id, str) or not project_id.strip():
        raise ValueError("project_id is required.")

    if database != "(default)":
        raise ValueError(
            "Persistent HUMAN VECTOR memory is restricted to "
            "the approved Firestore (default) database."
        )

    if not isinstance(query_basis, str) or not query_basis.strip():
        raise ValueError("query_basis is required.")

    if not isinstance(document_paths, list) or not document_paths:
        raise ValueError(
            "At least one Firestore document path is required."
        )

    normalized_paths = []

    for raw_path in document_paths:
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ValueError(
                "Firestore document path must be a non-empty string."
            )

        path_value = raw_path.strip().strip("/")
        segments = [
            segment
            for segment in path_value.split("/")
            if segment
        ]

        if len(segments) < 2 or len(segments) % 2 != 0:
            raise ValueError(
                "Firestore path must identify an exact document."
            )

        normalized_paths.append("/".join(segments))

    if len(set(normalized_paths)) != len(normalized_paths):
        raise ValueError(
            "Duplicate Firestore document paths are not allowed."
        )

    credentials, adc_project = google.auth.default()

    if adc_project != project_id:
        raise RuntimeError(
            "ADC project does not match the requested Firestore project."
        )

    client = firestore.Client(
        project=project_id,
        credentials=credentials,
        database=database,
    )

    candidates = []
    not_found_paths = []

    try:
        for document_path in normalized_paths:
            ref = client.document(document_path)

            snapshot = ref.get(
                retry=None,
                timeout=20,
            )

            if not snapshot.exists:
                not_found_paths.append(ref.path)
                continue

            payload = snapshot.to_dict()

            if not isinstance(payload, dict):
                raise RuntimeError(
                    "Firestore persistent memory payload must be an object."
                )

            expected_fields = {
                "schema_version",
                "memory_id",
                "source_actor",
                "source_session_id",
                "storage_authorized_by",
                "status",
                "content",
                "provenance",
                "authorized_effect",
                "created_at",
                "content_hash",
            }

            actual_fields = set(payload)

            if actual_fields != expected_fields:
                missing = sorted(expected_fields - actual_fields)
                unexpected = sorted(actual_fields - expected_fields)
                raise RuntimeError(
                    "Firestore persistent memory schema fields differ; "
                    f"missing={missing!r}; unexpected={unexpected!r}."
                )

            stored_hash = payload.get("content_hash")

            if (
                not isinstance(stored_hash, str)
                or len(stored_hash) != 64
            ):
                raise RuntimeError(
                    "Firestore persistent memory content_hash is invalid."
                )

            payload_without_hash = {
                key: value
                for key, value in payload.items()
                if key != "content_hash"
            }

            try:
                canonical = json.dumps(
                    payload_without_hash,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ).encode("utf-8")
            except (TypeError, ValueError) as exc:
                raise RuntimeError(
                    "Firestore persistent memory payload is not "
                    "canonically hashable."
                ) from exc

            calculated_hash = hashlib.sha256(
                canonical
            ).hexdigest()

            if calculated_hash != stored_hash:
                raise RuntimeError(
                    "Firestore persistent memory integrity check failed."
                )

            schema_version = payload.get("schema_version")

            if schema_version != "HV_MEMORY_CORE_CANDIDATE_V1":
                raise RuntimeError(
                    "Unsupported persistent memory schema."
                )

            memory_id = payload.get("memory_id")

            if (
                not isinstance(memory_id, str)
                or not memory_id.strip()
            ):
                raise RuntimeError(
                    "Persistent memory memory_id is invalid."
                )

            if memory_id != snapshot.id:
                raise RuntimeError(
                    "Persistent memory document ID binding failed."
                )

            storage_authorized_by = payload.get(
                "storage_authorized_by"
            )

            if storage_authorized_by != Actor.HUMAN.value:
                raise RuntimeError(
                    "Persistent memory storage authorization "
                    "is not exactly HUMAN."
                )

            status = payload.get("status")

            if status != "HUMAN_AUTHORIZED_FOR_STORAGE":
                raise RuntimeError(
                    "Persistent memory storage status is invalid."
                )

            authorized_effect = payload.get(
                "authorized_effect"
            )

            if (
                authorized_effect
                !=
                "NO_RECONSTRUCTION_EFFECT_UNTIL_LATER_HUMAN_REVIEW"
            ):
                raise RuntimeError(
                    "Persistent storage must not grant "
                    "reconstruction effect."
                )

            source_actor = payload.get("source_actor")

            valid_actor_values = {
                actor.value
                for actor in Actor
            }

            if (
                not isinstance(source_actor, str)
                or source_actor not in valid_actor_values
            ):
                raise RuntimeError(
                    "Persistent memory source_actor is invalid."
                )

            source_session_id = payload.get(
                "source_session_id"
            )

            if (
                not isinstance(source_session_id, str)
                or not source_session_id.strip()
            ):
                raise RuntimeError(
                    "Persistent memory source_session_id "
                    "is required."
                )

            original_content = payload.get("content")

            if (
                not isinstance(original_content, str)
                or not original_content.strip()
            ):
                raise RuntimeError(
                    "Persistent memory content is required."
                )

            stored_provenance = payload.get("provenance")

            if (
                not isinstance(stored_provenance, str)
                or not stored_provenance.strip()
            ):
                raise RuntimeError(
                    "Persistent memory provenance is required."
                )

            created_at = payload.get("created_at")

            if (
                not isinstance(created_at, str)
                or not created_at.strip()
            ):
                raise RuntimeError(
                    "Persistent memory created_at is required."
                )

            candidates.append(
                {
                    "source_id": memory_id,
                    "source_type": "FIRESTORE_PERSISTENT_MEMORY",
                    "source_actor": source_actor,
                    "source_session_id": source_session_id,
                    "original_content": original_content,
                    "provenance": stored_provenance,
                    "retrieval_reason": (
                        "Verified persistent Firestore memory "
                        f"retrieved from {ref.path}; "
                        f"stored_hash={stored_hash}; "
                        f"query_basis={query_basis}"
                    ),
                    "relevance_score": None,
                    "warnings": (
                        "PERSISTED_STORAGE_IS_NOT_USAGE_AUTHORIZATION",
                        "REQUIRES_EXISTING_HUMAN_MEMORY_REVIEW",
                    ),
                }
            )

    finally:
        client.close()

    if not candidates:
        _orchestrator.record_memory_retrieval_outcome(
            outcome="NO_RELEVANT_CANDIDATE_FOUND",
            actor=Actor.MEMORY,
            reason=(
                "No verified persistent Firestore candidate was "
                "produced from the explicitly requested document paths."
            ),
        )

        return {
            "outcome": "NO_RELEVANT_CANDIDATE_FOUND",
            "query_basis": query_basis,
            "candidate_count": 0,
            "firestore_document_paths": normalized_paths,
            "not_found_document_paths": not_found_paths,
            "retrieval_outcome_recorded_in_core": True,
            "human_resolution_performed": False,
            "human_review_performed": False,
            "memory_transfer_performed": False,
            "reconstruction_effect_active": False,
        }

    artifact = _orchestrator.record_memory_candidates(
        actor=Actor.MEMORY,
        query_basis=query_basis,
        candidates=candidates,
    )

    if is_dataclass(artifact):
        artifact_data = asdict(artifact)
    else:
        artifact_data = {
            "retrieval_id": getattr(
                artifact,
                "retrieval_id",
                None,
            ),
            "status": getattr(
                artifact,
                "status",
                None,
            ),
        }

    return {
        "outcome": "MEMORY_CANDIDATES_RECORDED",
        "query_basis": query_basis,
        "candidate_count": len(candidates),
        "firestore_document_paths": normalized_paths,
        "not_found_document_paths": not_found_paths,
        "core_memory_retrieval_artifact": artifact_data,
        "recorded_by_actor": Actor.MEMORY.value,
        "human_resolution_performed": False,
        "human_review_performed": False,
        "memory_transfer_performed": False,
        "reconstruction_effect_active": False,
    }
