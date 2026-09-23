from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SelectorDecision(str, Enum):
    PASS = "PASS"
    RECONSTRUCT = "RECONSTRUCT"
    ESCALATE = "ESCALATE"


@dataclass(frozen=True)
class CanonicalAssessment:
    # Selector's own assessment of the AI result.
    direction_alignment: bool
    human_request_alignment: bool
    preserves_human_authority: bool
    ai_work_sufficient: bool

    # Critic provides evidence. It does not control routing.
    critic_found_actionable_gap: bool = False
    critic_gap_relevant: bool = False

    # True only when continuation genuinely requires HUMAN input.
    requires_human_input: bool = False

    reasons: tuple[str, ...] = ()
    reconstruction_requirements: tuple[str, ...] = ()


@dataclass(frozen=True)
class CanonicalSelectorResult:
    decision: SelectorDecision
    reasons: tuple[str, ...] = ()
    reconstruction_requirements: tuple[str, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)


def evaluate_canonical_selector(
    assessment: CanonicalAssessment,
    *,
    source: str = "CRITIC_CONFLICT_SPACE",
) -> CanonicalSelectorResult:
    """
    CANONICAL SELECTOR V2

    The Selector has routing authority over the AI workflow.

    It decides whether an AI result:
      PASS        -> is suitable for HUMAN presentation;
      RECONSTRUCT -> must return to AI for stronger reconstruction;
      ESCALATE    -> genuinely requires HUMAN input before AI can continue.

    Critic output is evidence for the Selector.
    Critic output is not routing authority.

    HUMAN remains the final authority over HUMAN choices and use of results.
    PASS creates no obligation for HUMAN to verify, certify, approve,
    reject, or immediately respond to the AI result.
    """

    provenance = {
        "selector": "CANONICAL_SELECTOR_V2",
        "source": source,
        "direction_alignment": assessment.direction_alignment,
        "human_request_alignment": assessment.human_request_alignment,
        "preserves_human_authority": assessment.preserves_human_authority,
        "ai_work_sufficient": assessment.ai_work_sufficient,
        "critic_found_actionable_gap": assessment.critic_found_actionable_gap,
        "critic_gap_relevant": assessment.critic_gap_relevant,
        "requires_human_input": assessment.requires_human_input,
    }

    # HUMAN input is requested only when AI cannot legitimately continue
    # without a HUMAN choice, preference, value judgment or missing fact
    # that only HUMAN can supply.
    if assessment.requires_human_input:
        return CanonicalSelectorResult(
            decision=SelectorDecision.ESCALATE,
            reasons=assessment.reasons or (
                "Continuation genuinely requires HUMAN input.",
            ),
            provenance=provenance,
        )

    reasons: list[str] = list(assessment.reasons)
    requirements: list[str] = list(
        assessment.reconstruction_requirements
    )

    if not assessment.direction_alignment:
        reasons.append(
            "AI result diverges from the locked HUMAN direction."
        )
        requirements.append(
            "Reconstruct in alignment with the locked HUMAN direction."
        )

    if not assessment.human_request_alignment:
        reasons.append(
            "AI result does not adequately address the HUMAN request."
        )
        requirements.append(
            "Produce a direct, relevant and substantively useful response "
            "to the HUMAN request."
        )

    if not assessment.preserves_human_authority:
        reasons.append(
            "AI result improperly interferes with HUMAN final authority."
        )
        requirements.append(
            "Reconstruct while preserving HUMAN authority over HUMAN "
            "choices, acceptance, verification and future requests."
        )

    if not assessment.ai_work_sufficient:
        reasons.append(
            "AI-side analysis or synthesis is insufficient."
        )
        requirements.append(
            "Perform the missing AI-side reasoning, analysis, comparison, "
            "verification or synthesis before presenting the result to HUMAN."
        )

    # Critic is evidence only.
    # A criticism affects routing only after the Selector independently
    # determines that the identified gap is relevant to the HUMAN request.
    if (
        assessment.critic_found_actionable_gap
        and assessment.critic_gap_relevant
    ):
        reasons.append(
            "Selector confirms that Critic identified a relevant deficiency."
        )
        requirements.append(
            "Resolve the confirmed relevant deficiency on the AI side."
        )

    if reasons or requirements:
        return CanonicalSelectorResult(
            decision=SelectorDecision.RECONSTRUCT,
            reasons=tuple(dict.fromkeys(reasons)),
            reconstruction_requirements=tuple(
                dict.fromkeys(requirements)
            ),
            provenance=provenance,
        )

    return CanonicalSelectorResult(
        decision=SelectorDecision.PASS,
        reasons=(
            "Selector confirms compatibility for HUMAN presentation.",
        ),
        provenance=provenance,
    )


def build_builder_reconstruction_package(
    *,
    original_builder_output: Any,
    critic_output: Any,
    selector_result: CanonicalSelectorResult,
    locked_human_direction: Any,
    human_request: Any = None,
) -> dict[str, Any]:
    if selector_result.decision is not SelectorDecision.RECONSTRUCT:
        raise ValueError(
            "Builder reconstruction package requires RECONSTRUCT."
        )

    return {
        "package_type": "CANONICAL_BUILDER_RECONSTRUCTION",
        "selector_version": "V2",
        "locked_human_direction": locked_human_direction,
        "human_request": human_request,
        "original_builder_output": original_builder_output,
        "critic_output": critic_output,
        "selector_reasons": list(selector_result.reasons),
        "requirements": list(
            selector_result.reconstruction_requirements
        ),
        "instruction": (
            "Reconstruct the result on the AI side. "
            "Address the confirmed deficiencies and produce a stronger, "
            "relevant and coherent result aligned with the HUMAN request "
            "and locked direction. Preserve HUMAN final authority. "
            "Do not transfer unfinished AI analysis, verification, "
            "comparison or synthesis to HUMAN."
        ),
        "provenance": selector_result.provenance,
    }

# OP03_M06_DIRECT_SELECTOR_INPUT_V1
async def evaluate_builder_output(
    *,
    builder_output,
    human_request,
    locked_human_direction,
    model_name,
):
    import json
    from google import genai

    if builder_output is None:
        raise RuntimeError("Selector received no Builder output.")

    if not human_request:
        raise RuntimeError("Selector requires HUMAN request.")

    if not locked_human_direction:
        raise RuntimeError("Selector requires locked HUMAN direction.")

    if not isinstance(model_name, str) or not model_name.strip():
        raise RuntimeError("Selector requires active model name.")

    prompt = (
        "CANONICAL SELECTOR\n"
        "Evaluate the Builder result before it continues.\n\n"

        "Check the result against the HUMAN request and locked direction.\n"
        "Detect direction drift, objective substitution, contradictions, "
        "unsupported assumptions, material omissions, insufficient depth, "
        "superficiality, insufficient practical usefulness and unfinished "
        "AI work.\n\n"

        "Return JSON only with exactly these fields:\n"
        "direction_alignment: boolean\n"
        "human_request_alignment: boolean\n"
        "preserves_human_authority: boolean\n"
        "ai_work_sufficient: boolean\n"
        "critic_found_actionable_gap: boolean\n"
        "critic_gap_relevant: boolean\n"
        "requires_human_input: boolean\n"
        "reasons: array of strings\n"
        "reconstruction_requirements: array of strings\n\n"

        "HUMAN REQUEST:\n"
        + json.dumps(
            human_request,
            ensure_ascii=False,
            default=str,
        )
        + "\n\nLOCKED HUMAN DIRECTION:\n"
        + json.dumps(
            locked_human_direction,
            ensure_ascii=False,
            default=str,
        )
        + "\n\nBUILDER OUTPUT:\n"
        + json.dumps(
            builder_output,
            ensure_ascii=False,
            default=str,
        )
    )

    client = genai.Client()

    response = await client.aio.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    text = getattr(response, "text", None)

    if not text or not text.strip():
        raise RuntimeError("Selector produced no assessment.")

    raw = text.strip()

    if raw.startswith("```"):
        if "\n" in raw:
            raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    first = raw.find("{")
    last = raw.rfind("}")

    if first < 0 or last < first:
        raise RuntimeError("Selector produced invalid JSON.")

    payload = json.loads(raw[first:last + 1])

    bool_fields = (
        "direction_alignment",
        "human_request_alignment",
        "preserves_human_authority",
        "ai_work_sufficient",
        "critic_found_actionable_gap",
        "critic_gap_relevant",
        "requires_human_input",
    )

    for field in bool_fields:
        if type(payload.get(field)) is not bool:
            raise RuntimeError(
                "Invalid CanonicalAssessment field: " + field
            )

    reasons = payload.get("reasons")
    requirements = payload.get("reconstruction_requirements")

    if not isinstance(reasons, list):
        raise RuntimeError("Selector reasons must be a list.")

    if not isinstance(requirements, list):
        raise RuntimeError(
            "Selector reconstruction requirements must be a list."
        )

    assessment = CanonicalAssessment(
        direction_alignment=payload["direction_alignment"],
        human_request_alignment=payload[
            "human_request_alignment"
        ],
        preserves_human_authority=payload[
            "preserves_human_authority"
        ],
        ai_work_sufficient=payload[
            "ai_work_sufficient"
        ],
        critic_found_actionable_gap=payload[
            "critic_found_actionable_gap"
        ],
        critic_gap_relevant=payload[
            "critic_gap_relevant"
        ],
        requires_human_input=payload[
            "requires_human_input"
        ],
        reasons=tuple(
            str(x).strip()
            for x in reasons
            if str(x).strip()
        ),
        reconstruction_requirements=tuple(
            str(x).strip()
            for x in requirements
            if str(x).strip()
        ),
    )

    return (
        assessment,
        evaluate_canonical_selector(
            assessment,
            source="BUILDER_V1_PRE_HUMAN",
        ),
    )
