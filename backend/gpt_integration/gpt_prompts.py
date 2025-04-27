from openai_client import chat_completion

# Templates for LLM-driven reports
_PROMPTS = {
    "event_report": """
You are an expert maritime security analyst. Given the following incident data, 
generate a structured event report including:
- Incident summary
- Vessel identity
- Timestamp and location
- Recommended next actions

Incident Data:
{incident_data}
""",
    "vessel_report": """
You are a maritime data specialist. Generate a vessel report with:
- Vessel name and flag
- Vessel type
- Recent movements summary
- Any AIS anomalies detected
- Risk assessment

Vessel Data:
{vessel_data}
"""
}

def generate_event_report(incident_data: str) -> str:
    prompt = _PROMPTS["event_report"].format(incident_data=incident_data)
    return chat_completion(prompt)

def generate_vessel_report(vessel_data: str) -> str:
    prompt = _PROMPTS["vessel_report"].format(vessel_data=vessel_data)
    return chat_completion(prompt)