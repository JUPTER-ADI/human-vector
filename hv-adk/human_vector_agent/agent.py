from google.adk.agents import Agent

from .hv_core_bridge import (
    get_human_vector_core_status,
    start_direction_draft,
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
        "Starting the direction-draft stage does not set, approve, or replace human direction. "
        "Never claim human authority and never make final human decisions. "
        "Final authority belongs exclusively to the human."
    ),
    tools=[
        get_human_vector_core_status,
        start_direction_draft,
    ],
)
