from __future__ import annotations

from google.adk.runners import InMemoryRunner
from google.genai import types
from human_vector_agent.canonical_selector import (
    SelectorDecision,
    CanonicalAssessment,
    evaluate_canonical_selector,
    build_builder_reconstruction_package,
)
from human_vector_agent.agent import builder_v1_agent

from fastapi import HTTPException
from google.adk.cli.fast_api import get_fast_api_app


app = get_fast_api_app(
    agents_dir="/app/hv-adk",
    web=False,
)


from human_vector_agent.hv_core_bridge import (
    bind_orchestrator,
    advance_to_builder_v1_running,
    prepare_builder_v1_direction,
    record_builder_v1_from_state,
)

@app.get("/human-vector/health")
def human_vector_health() -> dict[str, object]:
    return {
        "ok": True,
        "service": "human-vector",
        "access_layer": True,
    }


from pydantic import BaseModel

from human_vector.session_controller import SessionController
from human_vector.orchestrator import S, Actor, TransitionRejected
from human_vector_agent.hv_core_bridge import (
    prepare_critic_analysis,
    record_critic_review_from_state,
)
from human_vector_agent.agent import critic_v1_agent


session_controller = SessionController()


class CreateSessionRequest(BaseModel):
    user_id: str
    actor_id: str
    actor_role: str = "HUMAN"


@app.post("/human-vector/sessions")
def create_human_vector_session(
    request: CreateSessionRequest,
) -> dict[str, object]:
    context = session_controller.create_session(
        user_id=request.user_id,
        actor_id=request.actor_id,
        actor_role=request.actor_role,
    )

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "actor_id": context.actor_id,
        "actor_role": context.actor_role,
        "state": context.orchestrator.state.value,
        "revision": context.orchestrator.revision,
    }



class PersistSessionRequest(BaseModel):
    user_id: str
    path: str


@app.post("/human-vector/sessions/{session_id}/persist")
def persist_human_vector_session(
    session_id: str,
    request: PersistSessionRequest,
) -> dict[str, object]:

    try:
        session_controller.require_session_for_user(
            session_id=session_id,
            user_id=request.user_id,
        )
        session_controller.save_session(
            session_id=session_id,
            path=request.path,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": session_id,
        "persisted": True,
        "path": request.path,
    }



class LoadSessionRequest(BaseModel):
    path: str


@app.post("/human-vector/sessions/load")
def load_human_vector_session(
    request: LoadSessionRequest,
) -> dict[str, object]:

    try:
        context = session_controller.load_session(request.path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "actor_id": context.actor_id,
        "actor_role": context.actor_role,
        "state": context.orchestrator.state.value,
        "revision": context.orchestrator.revision,
        "loaded": True,
    }


@app.get("/human-vector/sessions/{session_id}")
def get_human_vector_session(
    session_id: str,
    user_id: str,
) -> dict[str, object]:

    try:
        context = session_controller.require_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "actor_id": context.actor_id,
        "actor_role": context.actor_role,
        "state": context.orchestrator.state.value,
        "revision": context.orchestrator.revision,
    }


@app.delete("/human-vector/sessions/{session_id}")
def close_human_vector_session(
    session_id: str,
    user_id: str,
) -> dict[str, object]:

    try:
        session_controller.close_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": session_id,
        "closed": True,
    }

@app.post("/human-vector/sessions/{session_id}/direction")
async def record_human_vector_direction(
    session_id: str,
    payload: dict[str, object],
):
    user_id = str(payload.get("user_id", "")).strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="USER_ID_REQUIRED")

    try:
        context = session_controller.require_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    orchestrator = context.orchestrator

    from human_vector.orchestrator import Actor
    from human_vector.states import HumanVectorState as S

    if orchestrator.state is not S.DIRECTION_DRAFT:
        orchestrator.transition(S.DIRECTION_DRAFT, Actor.ORCHESTRATOR)

    direction = orchestrator.record_human_direction_draft(
        objective=str(payload.get("objective", "")).strip(),
        context=str(payload.get("context", "")).strip(),
        criteria=str(payload.get("criteria", "")).strip(),
        limits=str(payload.get("limits", "")).strip(),
        actor=Actor.HUMAN,
    )

    return {
        "ok": True,
        "session_id": session_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "direction_type": type(direction).__name__,
    }



@app.post("/human-vector/sessions/{session_id}/direction/confirm")
def confirm_human_vector_direction(
    session_id: str,
    payload: dict[str, object],
) -> dict[str, object]:
    user_id = str(payload.get("user_id", "")).strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    try:
        context = session_controller.require_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    orchestrator = context.orchestrator

    try:
        if orchestrator.state is S.DIRECTION_DRAFT:
            orchestrator.transition(
                S.DIRECTION_VALIDATION_REQUIRED,
                Actor.ORCHESTRATOR,
            )

        if orchestrator.state is S.DIRECTION_VALIDATION_REQUIRED:
            orchestrator.transition(
                S.DIRECTION_CONFIRMATION_REQUIRED,
                Actor.ORCHESTRATOR,
            )

        direction = orchestrator.confirm_human_direction(
            actor=Actor.HUMAN,
        )
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "direction_status": direction.status,
        "final_authority": "HUMAN",
    }



@app.post("/human-vector/sessions/{session_id}/builder-v1")
async def run_human_vector_builder_v1(session_id: str, payload: dict):
    try:
        context = session_controller.require_session(session_id)
        session_controller.require_session_for_user(session_id=session_id, user_id=payload["user_id"])
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    orchestrator = context.orchestrator

    try:
        bind_orchestrator(orchestrator)
        advance_result = advance_to_builder_v1_running()
        if not advance_result.get("ok"):
            raise RuntimeError(
                advance_result.get("reason", "Builder V1 advance failed")
            )
        if orchestrator.state is not S.BUILDER_V1_RUNNING:
            raise RuntimeError(
                f"Builder V1 advance failed: state={orchestrator.state.value}"
            )
        class _BuilderV1ApiToolContext:
            def __init__(self):
                self.state = {}

        builder_tool_context = _BuilderV1ApiToolContext()
        builder_tool_context.state["hv_core_session_id"] = context.session_id
        builder_input = prepare_builder_v1_direction(builder_tool_context)

        runner = InMemoryRunner(agent=builder_v1_agent)
        adk_session = await runner.session_service.create_session(
            app_name=runner.app_name,
            user_id=context.user_id,
            state={
                "hv_builder_direction_package": builder_tool_context.state[
                    "hv_builder_direction_package"
                ]
            ,
            "hv_core_session_id": context.session_id,},
        )
        message = types.Content(
            role="user",
            parts=[types.Part(text=builder_tool_context.state["hv_builder_direction_package"])],
        )
        async for _event in runner.run_async(
            user_id=context.user_id,
            session_id=adk_session.id,
            new_message=message,
        ):
            pass

        builder_output = await runner.session_service.get_session(
            app_name=runner.app_name,
            user_id=context.user_id,
            session_id=adk_session.id,
        )
        builder_output = builder_output.state.get("hv_builder_v1_output")
        if not builder_output:
            raise RuntimeError("Builder V1 produced no exact ADK session output")

        builder_tool_context.state["hv_builder_v1_output"] = builder_output

        # OP03_M06_BUILDER_V1_CANONICAL_SELECTOR_GATE
        # OP03_M06_CANONICAL_SELECTOR_RECONSTRUCTION_LOOP
        from human_vector_agent.canonical_selector import (
            evaluate_builder_output as _canonical_selector,
        )

        selector_max_rounds = 4
        selector_round = 0
        selected_builder_output = builder_output
        selector_trace = []

        while True:
            selector_round += 1

            selector_model = getattr(
                builder_v1_agent,
                "model",
                None,
            )

            if not isinstance(selector_model, str):
                selector_model = getattr(
                    selector_model,
                    "model",
                    None,
                )

            selector_assessment, selector_result = (
                await _canonical_selector(
                    builder_output=selected_builder_output,
                    human_request=builder_input,
                    locked_human_direction=(
                        builder_tool_context.state.get(
                            "hv_builder_direction_package"
                        )
                    ),
                    model_name=selector_model,
                )
            )

            selector_trace.append({
                "round": selector_round,
                "decision": selector_result.decision.value,
                "reasons": list(selector_result.reasons),
                "reconstruction_requirements": list(
                    selector_result.reconstruction_requirements
                ),
                "provenance": selector_result.provenance,
            })

            builder_tool_context.state[
                "hv_canonical_selector_result"
            ] = selector_trace[-1]

            if selector_result.decision is SelectorDecision.PASS:
                builder_output = selected_builder_output
                builder_tool_context.state[
                    "hv_builder_v1_output"
                ] = builder_output
                break

            if selector_result.decision is SelectorDecision.ESCALATE:
                builder_tool_context.state[
                    "hv_selector_requires_human_input"
                ] = True

                builder_output = selected_builder_output
                builder_tool_context.state[
                    "hv_builder_v1_output"
                ] = builder_output

                break

            if selector_round >= selector_max_rounds:
                raise RuntimeError(
                    "Canonical Selector did not PASS Builder output "
                    f"after {selector_max_rounds} rounds."
                )

            reconstruction_package = build_builder_reconstruction_package(
                original_builder_output=selected_builder_output,
                critic_output=None,
                selector_result=selector_result,
                locked_human_direction=builder_tool_context.state.get(
                    "hv_builder_direction_package"
                ),
                human_request=builder_input,
            )

            builder_tool_context.state[
                "hv_builder_reconstruction_package"
            ] = reconstruction_package

            reconstruction_input = (
                "Reconstruct your previous Builder result using the "
                "Canonical Selector package below. Preserve the HUMAN "
                "request and locked HUMAN direction. Resolve the identified "
                "problems using your own reasoning. Return a complete "
                "replacement result.\n\n"
                + str(reconstruction_package)
            )

            rebuilt_output = None

            async for event in runner.run_async(
                user_id=context.user_id,
                session_id=adk_session.id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=reconstruction_input)],
                ),
            ):
                content = getattr(event, "content", None)
                if content is None:
                    continue

                for part in getattr(content, "parts", []) or []:
                    text = getattr(part, "text", None)
                    if text and text.strip():
                        rebuilt_output = text.strip()

            if not rebuilt_output:
                raise RuntimeError(
                    "Builder reconstruction produced no output."
                )

            selected_builder_output = rebuilt_output
            builder_tool_context.state[
                "hv_builder_v1_output"
            ] = selected_builder_output

        builder_tool_context.state[
            "hv_canonical_selector_trace"
        ] = selector_trace

        record_result = record_builder_v1_from_state(builder_tool_context)
        if not record_result.get("ok"):
            raise RuntimeError(
                record_result.get("reason", "Builder V1 CORE recording failed")
            )
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "builder_v1_ready": True,
        "builder_input": builder_input,
        "required_next_operation": "ADK_BUILDER_V1",
        "human_authority_preserved": True,
        # OP03_M06_SELECTOR_TRACE_API_V1
        "selector_trace": builder_tool_context.state.get(
            "hv_canonical_selector_trace", []
        ),
        "selector_rounds": len(
            builder_tool_context.state.get(
                "hv_canonical_selector_trace", []
            )
        ),
        "selector_decision": (
            builder_tool_context.state[
                "hv_canonical_selector_trace"
            ][-1].get("decision")
            if builder_tool_context.state.get(
                "hv_canonical_selector_trace"
            )
            else None
        ),
        "selector_reconstruction_count": sum(
            1
            for item in builder_tool_context.state.get(
                "hv_canonical_selector_trace", []
            )
            if item.get("decision") == "RECONSTRUCT"
        ),
    }





class HumanCognitiveResponseRequest(BaseModel):
    user_id: str
    observation: str
    contradiction: str
    own_idea: str
    risks: str
    critic_questions: str


@app.post("/human-vector/sessions/{session_id}/human-response")
def record_human_vector_cognitive_response(
    session_id: str,
    payload: HumanCognitiveResponseRequest,
) -> dict[str, object]:
    from dataclasses import asdict

    try:
        context = session_controller.require_session_for_user(
            session_id=session_id,
            user_id=payload.user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    orchestrator = context.orchestrator

    try:
        draft = orchestrator.record_human_response_draft(
            observation=payload.observation,
            contradiction=payload.contradiction,
            own_idea=payload.own_idea,
            risks=payload.risks,
            critic_questions=payload.critic_questions,
            actor=Actor.HUMAN,
        )
        orchestrator.request_human_response_confirmation(actor=Actor.HUMAN)
        confirmed = orchestrator.confirm_human_response(actor=Actor.HUMAN)
    except (TransitionRejected, TypeError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": session_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "human_response": asdict(confirmed),
        "draft_response_id": getattr(draft, "response_id", None),
        "provenance_actor": Actor.HUMAN.value,
        "final_authority": "HUMAN",
    }


@app.post("/human-vector/sessions/{session_id}/conflict-space")
def build_human_vector_conflict_space(
    session_id: str,
    user_id: str,
) -> dict[str, object]:
    from dataclasses import asdict

    try:
        context = session_controller.require_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    orchestrator = context.orchestrator

    try:
        space = orchestrator.build_conflict_space(actor=Actor.SYSTEM)
        orchestrator.open_human_critic_selection(actor=Actor.ORCHESTRATOR)
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "conflict_space": asdict(space),
        "required_next_operation": "HUMAN_CRITIC_SELECTION",
        "final_authority": "HUMAN",
    }


class HumanCriticSelectionRequest(BaseModel):
    decisions: list[dict[str, str]]



@app.post("/human-vector/sessions/{session_id}/critic")
async def run_human_vector_critic(
    session_id: str,
    user_id: str,
) -> dict[str, object]:
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    try:
        context = session_controller.require_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    orchestrator = context.orchestrator

    try:
        bind_orchestrator(orchestrator)

        from types import SimpleNamespace

        critic_tool_context = SimpleNamespace(
            state={
                "hv_core_session_id": context.session_id,
            }
        )

        # OP03_M06_CRITIC_RUNNING_RECOVERY
        existing_orchestrator = context.orchestrator

        if existing_orchestrator.state is S.CRITIC_RUNNING:
            existing_critic_output = critic_tool_context.state.get(
                "hv_critic_output"
            )

            if not existing_critic_output:
                existing_critic_output = getattr(
                    existing_orchestrator,
                    "critic_running_output",
                    None,
                )

            if existing_critic_output:
                critic_tool_context.state[
                    "hv_critic_output"
                ] = existing_critic_output

                recovery_result = record_critic_review_from_state(
                    critic_tool_context
                )

                if not recovery_result.get("ok"):
                    raise RuntimeError(
                        recovery_result.get(
                            "reason",
                            "Critic CORE recovery failed",
                        )
                    )

                session_controller.save_session(context.session_id)

                return recovery_result

        prepare_result = prepare_critic_analysis(
            verified_elements=(
                "Confirmed HUMAN direction, generated Builder V1, and confirmed "
                "HUMAN cognitive response are present in the CORE session."
            ),
            unverified_elements=(
                "Builder V1 claims, assumptions, omissions, evidence quality, and "
                "proposed reasoning remain subject to independent Critic analysis."
            ),
            relevant_principles=(
                "Critic must independently challenge the result without replacing "
                "HUMAN authority; final authority remains HUMAN."
            ),
            tool_context=critic_tool_context,
        )
        if not prepare_result.get("ok"):
            raise RuntimeError(
                prepare_result.get(
                    "reason",
                    "Critic analysis preparation failed",
                )
            )

        critic_package = critic_tool_context.state.get(
            "hv_critic_analysis_package"
        )
        if not critic_package:
            raise RuntimeError(
                "Critic preparation produced no exact analysis package"
            )

        runner = InMemoryRunner(agent=critic_v1_agent)

        adk_session = await runner.session_service.create_session(
            app_name=runner.app_name,
            user_id=context.user_id,
            state={
                "hv_critic_analysis_package": critic_package,
                "hv_core_session_id": context.session_id,
            },
        )

        message = types.Content(
            role="user",
            parts=[types.Part(text=critic_package)],
        )

        async for _event in runner.run_async(
            user_id=context.user_id,
            session_id=adk_session.id,
            new_message=message,
        ):
            pass

        critic_session = await runner.session_service.get_session(
            app_name=runner.app_name,
            user_id=context.user_id,
            session_id=adk_session.id,
        )

        critic_output = critic_session.state.get("hv_critic_output")

        # OP03_M06_CANONICAL_SELECTOR_LIVE_V2
        locked_human_direction = critic_tool_context.state.get(
            "hv_locked_human_direction"
        )
        human_request = critic_tool_context.state.get("hv_human_request")

        criticisms = []
        if isinstance(critic_output, dict):
            criticisms = critic_output.get("criticisms") or []
        elif hasattr(critic_output, "criticisms"):
            criticisms = getattr(critic_output, "criticisms") or []

        if not isinstance(criticisms, list):
            criticisms = []

        def _critic_field(item, key, default=""):
            if isinstance(item, dict):
                return item.get(key, default)
            return getattr(item, key, default)

        actionable_criticisms = [
            item for item in criticisms
            if str(_critic_field(item, "correction_direction", "")).strip()
        ]

        verification_criticisms = [
            item for item in criticisms
            if str(_critic_field(item, "verification_required", "")).strip().lower()
            not in ("", "false", "none", "no", "0")
        ]

        critic_reasons = tuple(
            str(_critic_field(item, "explanation", "")).strip()
            for item in actionable_criticisms
            if str(_critic_field(item, "explanation", "")).strip()
        )

        critic_requirements = tuple(
            str(_critic_field(item, "correction_direction", "")).strip()
            for item in actionable_criticisms
            if str(_critic_field(item, "correction_direction", "")).strip()
        )

        assessment = CanonicalAssessment(
            direction_alignment=bool(locked_human_direction),
            human_request_alignment=bool(human_request),
            preserves_human_authority=True,
            ai_work_sufficient=not bool(actionable_criticisms),
            critic_found_actionable_gap=bool(actionable_criticisms),
            critic_gap_relevant=bool(actionable_criticisms),
            requires_human_input=False,
            reasons=critic_reasons,
            reconstruction_requirements=critic_requirements,
        )

        selector_result = evaluate_canonical_selector(
            assessment,
            source="CRITIC_CONFLICT_SPACE",
        )

        critic_tool_context.state["hv_canonical_selector_result"] = {
            "decision": selector_result.decision.value,
            "reasons": list(selector_result.reasons),
            "reconstruction_requirements": list(
                selector_result.reconstruction_requirements
            ),
            "provenance": selector_result.provenance,
        }

        if selector_result.decision is SelectorDecision.RECONSTRUCT:
            reconstruction_package = build_builder_reconstruction_package(
                original_builder_output=critic_tool_context.state.get(
                    "hv_builder_output"
                ),
                critic_output=critic_output,
                selector_result=selector_result,
                locked_human_direction=locked_human_direction,
                human_request=human_request,
            )
            critic_tool_context.state[
                "hv_builder_reconstruction_package"
            ] = reconstruction_package

        elif selector_result.decision is SelectorDecision.ESCALATE:
            critic_tool_context.state[
                "hv_selector_requires_human_input"
            ] = True
            print(
            "D364_CRITIC_OUTPUT_RUNTIME",
            "type=" + type(critic_output).__name__,
            "repr=" + repr(critic_output),
            flush=True,
        )
        if not critic_output:
            raise RuntimeError(
                "Critic produced no exact ADK session output"
            )

        critic_tool_context.state["hv_critic_output"] = critic_output

        # OP03_M06_CRITIC_OUTPUT_DURABLE_RECOVERY
        orchestrator.critic_running_output = critic_output
        session_controller.save_session(context.session_id)

        record_result = record_critic_review_from_state(
            critic_tool_context
        )
        if not record_result.get("ok"):
            raise RuntimeError(
                record_result.get(
                    "reason",
                    "Critic CORE recording failed",
                )
            )

    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "critic_output_key": "hv_critic_output",
        "critic_output_source": "ADK_SESSION_STATE",
        "criticisms_count": record_result.get("criticism_count"),
        "provenance_actor": "CRITIC_AI",
        "final_authority": "HUMAN",
    }


@app.get("/human-vector/sessions/{session_id}/conflict-space/current")
def get_human_vector_conflict_space(
    session_id: str,
    user_id: str,
) -> dict[str, object]:
    from dataclasses import asdict

    try:
        context = session_controller.require_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    artifact = context.orchestrator.conflict_space_artifact
    if artifact is None:
        raise HTTPException(status_code=409, detail="Conflict Space is not available.")

    return {
        "ok": True,
        "session_id": session_id,
        "state": context.orchestrator.state.value,
        "revision": context.orchestrator.revision,
        "conflict_space": asdict(artifact),
        "final_authority": "HUMAN",
    }


@app.post("/human-vector/sessions/{session_id}/critic-selection")
def record_human_vector_critic_selection(
    session_id: str,
    user_id: str,
    payload: HumanCriticSelectionRequest,
) -> dict[str, object]:
    from dataclasses import asdict

    try:
        context = session_controller.require_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    orchestrator = context.orchestrator

    try:
        selection = orchestrator.record_human_critic_selection(
            actor=Actor.HUMAN,
            decisions=payload.decisions,
        )
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "human_critic_selection": asdict(selection),
        "final_authority": "HUMAN",
    }




@app.post("/human-vector/sessions/{session_id}/manual-transfer/prepare")
def prepare_human_vector_manual_transfer(
    session_id: str,
    user_id: str,
) -> dict[str, object]:
    """
    Continue an already persisted HUMAN Critic Selection into
    Manual Cognitive Transfer preparation.

    This endpoint does not recreate or reinterpret HUMAN decisions.
    It only advances the canonical state after the persisted HUMAN
    selection already exists.
    """
    try:
        context = session_controller.require_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    orchestrator = context.orchestrator

    if orchestrator.state.value != "HUMAN_CRITIC_SELECTION":
        raise HTTPException(
            status_code=409,
            detail=(
                "Manual Transfer preparation requires "
                "HUMAN_CRITIC_SELECTION."
            ),
        )

    if orchestrator.human_critic_selection_artifact is None:
        raise HTTPException(
            status_code=409,
            detail="Persisted HUMAN Critic Selection is required.",
        )

    try:
        # Use the canonical CORE transition. HUMAN remains the authority.
        target = orchestrator.state.__class__.MANUAL_TRANSFER_PREPARATION
        orchestrator.transition(
            target,
            Actor.HUMAN,
            "Persisted HUMAN Critic Selection completed; "
            "Manual Cognitive Transfer preparation authorized.",
        )
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "human_selection_preserved": True,
        "required_next_operation": "HUMAN_OPEN_MANUAL_TRANSFER",
        "final_authority": "HUMAN",
    }


@app.post("/human-vector/sessions/{session_id}/manual-transfer/open")
def open_human_vector_manual_transfer(
    session_id: str,
    user_id: str,
) -> dict[str, object]:
    try:
        context = session_controller.require_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    orchestrator = context.orchestrator

    try:
        orchestrator.open_manual_transfer(actor=Actor.HUMAN)
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "required_next_operation": "HUMAN_BUILD_MANUAL_TRANSFER_PACKAGE",
        "final_authority": "HUMAN",
    }



@app.post("/human-vector/sessions/{session_id}/manual-transfer/build")
def build_human_vector_manual_transfer(
    session_id: str,
    user_id: str,
) -> dict[str, object]:
    """Build the canonical Manual Cognitive Transfer package."""
    from dataclasses import asdict

    try:
        context = session_controller.require_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    orchestrator = context.orchestrator

    if orchestrator.state.value != "MANUAL_TRANSFER_IN_PROGRESS":
        raise HTTPException(
            status_code=409,
            detail=(
                "Manual Transfer package can be built only from "
                "MANUAL_TRANSFER_IN_PROGRESS."
            ),
        )

    selection = getattr(orchestrator, "human_critic_selection_artifact", None)
    conflict_space = getattr(orchestrator, "conflict_space_artifact", None)

    if selection is None or conflict_space is None:
        raise HTTPException(
            status_code=409,
            detail="Manual Transfer requires existing HUMAN selection and Conflict Space.",
        )

    decisions = getattr(selection, "decisions", ())
    selected_ids = {
        getattr(decision, "criticism_id", "")
        for decision in decisions
        if getattr(decision, "decision", "") in {
            "ACCEPTED",
            "PARTIALLY_ACCEPTED",
            "NEEDS_CLARIFICATION",
            "NEEDS_EXTERNAL_VERIFICATION",
            "KEEP_AS_UNRESOLVED",
        }
    }

    criticisms = getattr(conflict_space, "criticisms", ())
    items = []

    for criticism in criticisms:
        criticism_id = getattr(criticism, "criticism_id", "")
        if criticism_id not in selected_ids:
            continue

        content = (
            getattr(criticism, "question", "")
            or getattr(criticism, "risk", "")
            or getattr(criticism, "correction_direction", "")
        )

        if not content:
            continue

        items.append({
            "source_object_type": "CRITICISM",
            "source_object_id": criticism_id,
            "source_actor_type": "CRITIC_AI",
            "transfer_type": "TRANSFORMED",
            "original_content": content,
            "selected_fragment": content,
            "human_transformed_content": content,
            "reason": "Explicit HUMAN-selected Critic contribution for Manual Cognitive Transfer.",
            "expected_effect": "Preserve HUMAN-selected cognitive challenge in reconstruction context.",
            "conditions": "Use only within the HUMAN-authorized reconstruction context.",
            "destination": "MEMORY_RETRIEVAL_CONTEXT",
        })

    if not items:
        raise HTTPException(
            status_code=409,
            detail="No HUMAN-selected Critic items available for Manual Transfer.",
        )

    try:
        package = orchestrator.build_manual_transfer_package(
            actor="HUMAN",
            items=items,
        )
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "manual_transfer": asdict(package),
        "required_next_operation": "HUMAN_CONFIRM_MANUAL_TRANSFER",
        "final_authority": "HUMAN",
    }


@app.get("/human-vector/sessions/{session_id}/manual-transfer/current")
def get_human_vector_manual_transfer(
    session_id: str,
    user_id: str,
) -> dict[str, object]:
    from dataclasses import asdict

    try:
        context = session_controller.require_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    orchestrator = context.orchestrator
    artifact = orchestrator.manual_transfer_artifact

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "manual_transfer": asdict(artifact) if artifact is not None else None,
        "final_authority": "HUMAN",
    }


@app.get("/human-vector/sessions/{session_id}/results")
def get_human_vector_session_results(
    session_id: str,
    user_id: str,
) -> dict[str, object]:
    from dataclasses import asdict, is_dataclass

    try:
        context = session_controller.require_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    orchestrator = context.orchestrator

    def serialize_artifact(value: object) -> object:
        if value is None:
            return None
        if is_dataclass(value):
            return asdict(value)
        return value

    baseline = getattr(
        orchestrator,
        "human_capability_baseline_artifact",
        None,
    )
    assessment = getattr(
        orchestrator,
        "human_capability_assessment_artifact",
        None,
    )
    gain = getattr(
        orchestrator,
        "human_capability_gain_artifact",
        None,
    )

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "human_capability": {
            "baseline": serialize_artifact(baseline),
            "assessment": serialize_artifact(assessment),
            "gain_evidence": serialize_artifact(gain),
            "baseline_available": baseline is not None,
            "assessment_available": assessment is not None,
            "gain_evidence_available": gain is not None,
        },
        "final_report_available": getattr(
            orchestrator,
            "final_report",
            None,
        ) is not None,
    }

# HV_OP03_M04_MEMORY_RETRIEVAL_API_V1
class HumanVectorMemoryRetrieveRequest(BaseModel):
    user_id: str
    project_id: str
    query_context: dict[str, object]
    branch_id: str | None = None
    cycle_id: str | None = None
    filters: dict[str, object] | None = None
    database: str = "(default)"
    limit: int = 100
    min_score: float = 0.0
    idempotency_key: str | None = None


@app.post("/human-vector/sessions/{session_id}/memory/retrieve")
def retrieve_human_vector_memory(
    session_id: str,
    request: HumanVectorMemoryRetrieveRequest,
) -> dict[str, object]:
    from human_vector_agent.hv_core_bridge import (
        retrieve_canonical_active_memory_to_core,
    )

    try:
        context = session_controller.require_session_for_user(
            session_id=session_id,
            user_id=request.user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    orchestrator = context.orchestrator

    try:
        if orchestrator.state is S.TRANSFER_PACKAGE_LOCKED:
            orchestrator.transition(
                S.MEMORY_RETRIEVAL_READY,
                actor=Actor.ORCHESTRATOR,
                reason="HUMAN VECTOR API entered canonical Active Memory.",
            )

        if orchestrator.state is S.MEMORY_RETRIEVAL_READY:
            orchestrator.transition(
                S.MEMORY_RETRIEVAL_RUNNING,
                actor=Actor.ORCHESTRATOR,
                reason="HUMAN VECTOR API started canonical Active Memory retrieval.",
            )

        if orchestrator.state is not S.MEMORY_RETRIEVAL_RUNNING:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Memory retrieval requires "
                    "TRANSFER_PACKAGE_LOCKED, MEMORY_RETRIEVAL_READY, "
                    "or MEMORY_RETRIEVAL_RUNNING."
                ),
            )

        bind_orchestrator(orchestrator)

        result = retrieve_canonical_active_memory_to_core(
            project_id=request.project_id,
            session_id=context.session_id,
            query_context=request.query_context,
            branch_id=request.branch_id,
            cycle_id=request.cycle_id,
            filters=request.filters,
            database=request.database,
            limit=request.limit,
            min_score=request.min_score,
            idempotency_key=request.idempotency_key,
        )

    except HTTPException:
        raise
    except TransitionRejected as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    outcome = result.get("outcome")

    if outcome == "CANDIDATES_FOUND":
        required_next_operation = "HUMAN_MEMORY_REVIEW"
    elif outcome == "NO_RELEVANT_CANDIDATE_FOUND":
        required_next_operation = "HUMAN_CONFIRM_NO_RELEVANT_MEMORY"
    else:
        required_next_operation = "HUMAN_MEMORY_RETRIEVAL_REVIEW"

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "memory_retrieval": result,
        "required_next_operation": required_next_operation,
        "human_review_performed": False,
        "memory_activation_performed": False,
        "reconstruction_effect_active": False,
        "final_authority": "HUMAN",
    }

# HV_OP03_M05_HUMAN_MEMORY_AUTHORIZATION_API_V1
class HumanVectorMemoryReviewRequest(BaseModel):
    user_id: str
    decisions: list[dict[str, object]]


class HumanVectorMemoryTransferBuildRequest(BaseModel):
    user_id: str
    transfers: list[dict[str, object]]


class HumanVectorMemoryTransferConfirmRequest(BaseModel):
    user_id: str
    selection_content_hash: str
    transfer_content_hash: str
    confirmation_note: str


class HumanVectorMemoryOwnerRequest(BaseModel):
    user_id: str


class HumanVectorNoRelevantMemoryRequest(BaseModel):
    user_id: str
    reason: str


def _op03_require_owner_session(
    session_id: str,
    user_id: str,
):
    try:
        return session_controller.require_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/human-vector/sessions/{session_id}/memory/review")
def review_human_vector_memory(
    session_id: str,
    request: HumanVectorMemoryReviewRequest,
) -> dict[str, object]:
    from dataclasses import asdict

    context = _op03_require_owner_session(
        session_id,
        request.user_id,
    )
    orchestrator = context.orchestrator

    try:
        selection = orchestrator.review_memory_candidates(
            actor=Actor.HUMAN,
            decisions=request.decisions,
        )
    except TransitionRejected as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "memory_selection": asdict(selection),
        "required_next_operation": "HUMAN_BUILD_MEMORY_TRANSFER",
        "final_authority": "HUMAN",
    }


@app.post("/human-vector/sessions/{session_id}/memory/transfer/build")
def build_human_vector_memory_transfer(
    session_id: str,
    request: HumanVectorMemoryTransferBuildRequest,
) -> dict[str, object]:
    from dataclasses import asdict

    context = _op03_require_owner_session(
        session_id,
        request.user_id,
    )
    orchestrator = context.orchestrator

    try:
        package = orchestrator.build_memory_transfer_package(
            actor=Actor.HUMAN,
            transfers=request.transfers,
        )
    except TransitionRejected as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "memory_transfer": asdict(package),
        "required_next_operation": "HUMAN_CONFIRM_MEMORY_TRANSFER",
        "final_authority": "HUMAN",
    }


@app.post("/human-vector/sessions/{session_id}/memory/transfer/confirm")
def confirm_human_vector_memory_transfer(
    session_id: str,
    request: HumanVectorMemoryTransferConfirmRequest,
) -> dict[str, object]:
    from dataclasses import asdict

    context = _op03_require_owner_session(
        session_id,
        request.user_id,
    )
    orchestrator = context.orchestrator

    try:
        selection, package = (
            orchestrator.confirm_memory_selection_and_transfer(
                actor=Actor.HUMAN,
                selection_content_hash=request.selection_content_hash,
                transfer_content_hash=request.transfer_content_hash,
                confirmation_note=request.confirmation_note,
            )
        )
    except TransitionRejected as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "memory_selection": asdict(selection),
        "memory_transfer": asdict(package),
        "required_next_operation": "SYSTEM_LOCK_MEMORY_SELECTION",
        "human_confirmation_recorded": True,
        "final_authority": "HUMAN",
    }


@app.post("/human-vector/sessions/{session_id}/memory/transfer/lock")
def lock_human_vector_memory_transfer(
    session_id: str,
    request: HumanVectorMemoryOwnerRequest,
) -> dict[str, object]:
    from dataclasses import asdict

    context = _op03_require_owner_session(
        session_id,
        request.user_id,
    )
    orchestrator = context.orchestrator

    try:
        selection, package = orchestrator.lock_memory_selection(
            actor=Actor.SYSTEM,
        )
    except TransitionRejected as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "memory_selection": asdict(selection),
        "memory_transfer": asdict(package),
        "required_next_operation": "RECONSTRUCTION_PACKAGE_PREPARATION",
        "technical_lock_by": "SYSTEM",
        "final_authority": "HUMAN",
    }


@app.post("/human-vector/sessions/{session_id}/memory/no-relevant")
def confirm_human_vector_no_relevant_memory(
    session_id: str,
    request: HumanVectorNoRelevantMemoryRequest,
) -> dict[str, object]:
    context = _op03_require_owner_session(
        session_id,
        request.user_id,
    )
    orchestrator = context.orchestrator

    try:
        orchestrator.confirm_no_relevant_memory(
            actor=Actor.HUMAN,
            reason=request.reason,
        )
    except TransitionRejected as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "human_reason": request.reason,
        "required_next_operation": "RECONSTRUCTION_PACKAGE_PREPARATION",
        "final_authority": "HUMAN",
    }

# HV_OP03_M06_RECONSTRUCTION_PACKAGE_API_V1
class HumanVectorReconstructionOwnerRequest(BaseModel):
    user_id: str


class HumanVectorReconstructionConfirmRequest(BaseModel):
    user_id: str
    package_content_hash: str
    confirmation_note: str


@app.post(
    "/human-vector/sessions/{session_id}/reconstruction-package/build"
)
def build_human_vector_reconstruction_package(
    session_id: str,
    request: HumanVectorReconstructionOwnerRequest,
) -> dict[str, object]:
    from dataclasses import asdict

    context = _op03_require_owner_session(
        session_id,
        request.user_id,
    )
    orchestrator = context.orchestrator

    if orchestrator.state in {
        S.MEMORY_SELECTION_LOCKED,
        S.NO_RELEVANT_MEMORY,
    }:
        try:
            orchestrator.transition(
                S.RECONSTRUCTION_PACKAGE_PREPARATION,
                Actor.ORCHESTRATOR,
            )
        except TransitionRejected as exc:
            raise HTTPException(
                status_code=409,
                detail=str(exc),
            ) from exc

    try:
        package = orchestrator.build_final_reconstruction_package(
            actor=Actor.ORCHESTRATOR,
        )
    except TransitionRejected as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "reconstruction_package": asdict(package),
        "required_next_operation":
            "HUMAN_CONFIRM_RECONSTRUCTION_PACKAGE",
        "final_authority": "HUMAN",
    }


@app.post(
    "/human-vector/sessions/{session_id}/reconstruction-package/confirm"
)
def confirm_human_vector_reconstruction_package(
    session_id: str,
    request: HumanVectorReconstructionConfirmRequest,
) -> dict[str, object]:
    from dataclasses import asdict

    context = _op03_require_owner_session(
        session_id,
        request.user_id,
    )
    orchestrator = context.orchestrator

    try:
        package = orchestrator.confirm_final_reconstruction_package(
            actor=Actor.HUMAN,
            package_content_hash=request.package_content_hash,
            confirmation_note=request.confirmation_note,
        )
    except TransitionRejected as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "reconstruction_package": asdict(package),
        "human_confirmation_recorded": True,
        "confirmed_content_hash": package.confirmed_content_hash,
        "required_next_operation":
            "SYSTEM_LOCK_RECONSTRUCTION_PACKAGE",
        "final_authority": "HUMAN",
    }


@app.post(
    "/human-vector/sessions/{session_id}/reconstruction-package/lock"
)
def lock_human_vector_reconstruction_package(
    session_id: str,
    request: HumanVectorReconstructionOwnerRequest,
) -> dict[str, object]:
    from dataclasses import asdict

    context = _op03_require_owner_session(
        session_id,
        request.user_id,
    )
    orchestrator = context.orchestrator

    try:
        package = orchestrator.lock_final_reconstruction_package(
            actor=Actor.SYSTEM,
        )
    except TransitionRejected as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "reconstruction_package": asdict(package),
        "technical_lock_by": "SYSTEM",
        "required_next_operation": "RECONSTRUCTION_RUNNING",
        "final_authority": "HUMAN",
    }

# HV_OP03_M06_HUMAN_ITERATION_DECISION_API_V1
class HumanVectorIterationDecisionRequest(BaseModel):
    user_id: str
    reason: str
    evolved_criteria: str
    requested_changes: str


@app.post(
    "/human-vector/sessions/{session_id}/iteration-decision"
)
def record_human_vector_iteration_decision(
    session_id: str,
    request: HumanVectorIterationDecisionRequest,
) -> dict[str, object]:
    from dataclasses import asdict

    context = _op03_require_owner_session(
        session_id,
        request.user_id,
    )
    orchestrator = context.orchestrator

    try:
        from human_vector_agent.hv_human_driver import (
            submit_human_iteration_decision,
        )

        decision = submit_human_iteration_decision(
            orchestrator,
            reason=request.reason,
            evolved_criteria=request.evolved_criteria,
            requested_changes=request.requested_changes,
        )
    except TransitionRejected as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "ok": True,
        "session_id": context.session_id,
        "user_id": context.user_id,
        "state": orchestrator.state.value,
        "revision": orchestrator.revision,
        "iteration_decision": asdict(decision),
        "required_next_operation":
            "BUILD_RECONSTRUCTION_PACKAGE",
        "final_authority": "HUMAN",
    }

