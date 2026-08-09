from google.adk.agents import Agent

root_agent = Agent(
    name="human_vector_agent",
    model="gemini-3.5-flash",
    description="HUMAN VECTOR Google ADK entry agent.",
    instruction="You are the Google ADK entry agent for HUMAN VECTOR. Do not make final human decisions.",
)
