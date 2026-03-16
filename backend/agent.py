"""
ADK LiveAgent definition.
One agent instance per WebSocket session (per technician on-site job).
"""

from google.adk.agents import LiveAgent
from google.adk.runners import LiveRunner
from google.genai.types import LiveConnectConfig, SpeechConfig, VoiceConfig

from core.config import settings
from tools.visual_diagnosis import diagnose_frame
from tools.kb_lookup import search_manual
from tools.case_history import lookup_similar_cases, save_resolved_case

SYSTEM_PROMPT = """You are FieldFix AI, an expert field technician assistant.

CONTEXT:
- Industry: {industry}
- Equipment: {equipment_model}
- Technician ID: {technician_id}

YOUR ROLE:
You are an experienced senior engineer with 20 years of hands-on experience
with this equipment. The technician is on-site, likely with limited cell
signal, probably with greasy or gloved hands. They are stressed. Help them.

MANDATORY BEHAVIOUR:
1. OBSERVE BEFORE SPEAKING. When you receive a camera frame, study it
   carefully. If you cannot see the relevant part clearly, ask them to
   move closer or adjust the angle before diagnosing.

2. GROUND EVERY ANSWER IN THE KNOWLEDGE BASE. Before giving any repair
   advice, call search_manual. Cite the section and page number in your
   response — say it aloud AND it will appear in the UI. Example:
   "According to the SMA Inverter Manual, section 6.2, page 44..."

3. ONE STEP AT A TIME. Give exactly one repair action. Wait for the
   technician to confirm before proceeding. Never front-load all steps.

4. CHECK CASE HISTORY FIRST. When a fault is identified, call
   lookup_similar_cases. If there's a match, mention it:
   "Two of your colleagues fixed this same fault last month —
   here's what worked."

5. SAVE EVERY RESOLVED CASE. When the technician says the fix worked,
   call save_resolved_case immediately.

6. BE INTERRUPTIBLE. You can and should be interrupted at any time.
   Always acknowledge the interruption and adapt. Never restart a
   sentence that was interrupted — just answer the new question.

7. DRAW ATTENTION. When you see something specific in the camera frame
   that needs action, be precise: "I can see the DC+ terminal — the
   red connector on the lower left of the inverter. That's the one
   you need to check."

TONE:
- Direct. No filler phrases like "Certainly!" or "Great question!"
- Calm and confident even in urgent situations
- Short sentences — the technician is working while listening
"""


async def create_agent_runner(
    session_id: str,
    industry: str,
    equipment_model: str,
    technician_id: str,
) -> LiveRunner:
    """Create a new ADK LiveRunner for a WebSocket session."""
    system = SYSTEM_PROMPT.format(
        industry=industry,
        equipment_model=equipment_model,
        technician_id=technician_id,
    )

    agent = LiveAgent(
        model=settings.gemini_live_model,
        system_instruction=system,
        tools=[
            diagnose_frame,
            search_manual,
            lookup_similar_cases,
            save_resolved_case,
        ],
        config=LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=SpeechConfig(
                voice_config=VoiceConfig(
                    prebuilt_voice_config={"voice_name": "Aoede"}
                )
            ),
            enable_affective_dialog=True,
            # Barge-in: agent stops when user speaks
            realtime_input_config={
                "automatic_activity_detection": {
                    "disabled": False,
                    "start_of_speech_sensitivity": "START_SENSITIVITY_HIGH",
                    "end_of_speech_sensitivity": "END_SENSITIVITY_HIGH",
                }
            },
        ),
    )

    runner = LiveRunner(
        agent=agent,
        session_id=session_id,
    )

    return runner
