from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from .hv_core_bridge import (
    get_human_vector_core_status,
    start_direction_draft,
    advance_direction_to_human_confirmation,
    advance_to_builder_v1_running,
    prepare_builder_v1_direction,
    record_builder_v1_from_state,
    prepare_critic_analysis,
    record_critic_review_from_state,
)


builder_v1_agent = Agent(
    name="human_vector_builder_v1",
    model="gemini-3.5-flash",
    description=(
        "HUMAN VECTOR Builder AI. Constructs V1 only; "
        "it never performs the HUMAN cognitive response or final decision."
    ),
    instruction=(
        "You are the Builder AI inside HUMAN VECTOR. "
        "The following package is the ONLY authoritative Human Direction "
        "for this V1. It comes directly from the confirmed HUMAN artefact "
        "and must not be replaced by a reconstructed or paraphrased direction. "
        "\n\n--- CONFIRMED HUMAN DIRECTION PACKAGE ---\n"
        "{hv_builder_direction_package}"
        "\n--- END CONFIRMED HUMAN DIRECTION PACKAGE ---\n\n"
        "Your task is to construct the first substantive solution version, V1, "
        "from the HUMAN-authorized problem, direction, criteria, limits, and context "
        "provided to you. "
        "Produce a useful, concrete, high-quality solution rather than commentary "
        "about the protocol. "
        "Use AI for speed, structure, alternatives, connections, and depth. "
        "Clearly distinguish facts, assumptions, uncertainties, and unresolved risks "
        "when relevant. "
        "Do not simulate a HUMAN reaction, approval, selection, contradiction, "
        "verification, or final decision. "
        "Do not claim the result is final. "
        "Return the V1 content itself. "
        "The exact final text you produce will be preserved as the V1 artefact."
    ),
    output_key="hv_builder_v1_output",
)


builder_v1_tool = AgentTool(
    agent=builder_v1_agent,
)



critic_v1_agent = Agent(
    name="human_vector_critic_v1",
    model="gemini-3.5-flash",
    description=(
        "Independent HUMAN VECTOR Critic AI. "
        "Challenges Builder V1 and the HUMAN cognitive response "
        "without taking HUMAN authority."
    ),
    instruction=(
        "You are the HUMAN VECTOR independent Critic AI. "
        "You are NOT the Builder AI and you must not behave as the Builder. "
        "Analyze independently the exact CriticAnalysisPackage supplied below. "
        "Do not rewrite, modify, summarize, or replace the source V1. "
        "Do not rewrite or replace the HUMAN cognitive response. "
        "Do not automatically confirm Builder AI. "
        "Do not automatically confirm the HUMAN position. "
        "You may challenge either position when evidence, logic, assumptions, "
        "risk, feasibility, direction, provenance, or missing information justify it. "
        "Keep FACTS, ASSUMPTIONS, INTERPRETATIONS, and UNVERIFIED CLAIMS distinct. "
        "Expose contradictions, hidden assumptions, missing evidence, risks, "
        "weak logic, ignored alternatives, and deviations from the confirmed "
        "Human Direction. "
        "Do not accept or reject criticisms on behalf of the human. "
        "Do not select anything for reconstruction. "
        "Do not perform cognitive transfer. "
        "Do not declare VF or any final HUMAN decision. "
        "Final cognitive authority remains HUMAN. "
        "\n\nEXACT CORE CRITIC ANALYSIS PACKAGE:\n"
        "{hv_critic_analysis_package}"
        "\n\nReturn ONLY valid JSON. Do not use Markdown or code fences. "
        "The top-level JSON object must contain one key named criticisms. "
        "criticisms must be a non-empty array of criticism objects. "
        "Every criticism object must contain these string fields: "
        "object, type, explanation, basis, risk, severity, question, "
        "verification_required, correction_direction. "
        "Each criticism must be concrete and independently reasoned. "
        "Do not add a HUMAN selection, HUMAN verdict, transfer approval, "
        "or final decision."
    ),
    output_key="hv_critic_output",
)

critic_v1_tool = AgentTool(
    agent=critic_v1_agent,
)


root_agent = Agent(
    name="human_vector_agent",
    model="gemini-3.5-flash",
    description="HUMAN VECTOR Google ADK entry agent.",
    instruction=(
        "You are the Google ADK entry agent for HUMAN VECTOR. "
        "Use the HUMAN VECTOR core status tool when system-state information is needed. "
        "Only use start_direction_draft when the human explicitly asks to start or enter "
        "the HUMAN VECTOR direction-draft stage. Never invoke that operation autonomously. "
        "When the HUMAN VECTOR direction-draft stage does not yet have explicit HUMAN "
        "confirmation, use advance_direction_to_human_confirmation only for "
        "orchestrator-owned technical steps and stop at DIRECTION_CONFIRMATION_REQUIRED. "
        "Never confirm or lock the direction for the human. "
        "Only after the human has explicitly confirmed the direction and the core state "
        "is DIRECTION_LOCKED may you use advance_to_builder_v1_running. "
        "That operation may automate only orchestrator-owned Builder V1 setup steps and "
        "must stop at BUILDER_V1_RUNNING. "
        "When the core state is BUILDER_V1_RUNNING, first call "
        "prepare_builder_v1_direction. Only if that operation returns ok=true "
        "may you invoke the dedicated Builder V1 agent. "
        "The Builder must construct V1 only from the exact confirmed Human Direction "
        "package injected into its ADK session state. "
        "After the Builder V1 agent completes, call record_builder_v1_from_state. "
        "Never copy, rewrite, summarize, paraphrase, or manually re-create the Builder "
        "output for V1 recording. The bridge must read the exact Builder output from "
        "ADK session state. "
        "After V1 is recorded, automation must stop at HUMAN_RESPONSE_REQUIRED. "
        "At that point ask the human for a substantive cognitive response to V1, "
        "including their own observation or verification, an explicit contradiction "
        "or criticism where applicable, and at least one own idea or contribution. "
        "Never simulate HUMAN authority and never make final HUMAN decisions. "
        "Final authority belongs exclusively to the human."
        "After the HUMAN cognitive response is explicitly captured, "
        "the next AI stage is the independent Critic. "
        "Only from HUMAN_RESPONSE_CAPTURED may you call prepare_critic_analysis. "
        "Do not invent verified elements, unverified elements, or HUMAN claims. "
        "Use only explicit session/HUMAN information available for those fields. "
        "When prepare_critic_analysis returns ok=true and state=CRITIC_RUNNING, "
        "call critic_v1_tool exactly once for that Critic package. "
        "The Critic must analyze only the exact package injected into ADK state. "
        "After the Critic finishes, call record_critic_review_from_state. "
        "Never copy, paraphrase, summarize, or manually recreate the Critic output "
        "before recording it; the bridge must read the exact output_key value. "
        "After CriticReview is recorded, stop before any HUMAN criticism selection. "
        "Never accept, reject, partially accept, transfer, or resolve a criticism "
        "on behalf of the human. "
    ),
    tools=[
        get_human_vector_core_status,
        start_direction_draft,
        advance_direction_to_human_confirmation,
        advance_to_builder_v1_running,
        prepare_builder_v1_direction,
        builder_v1_tool,
        record_builder_v1_from_state,        prepare_critic_analysis,
        critic_v1_tool,
        record_critic_review_from_state,

    ],
)
