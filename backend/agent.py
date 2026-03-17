"""
Gemini Live agent configuration for FieldFix AI.
Uses google.genai directly for real-time audio/video streaming.
"""

from google.genai import types

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

# Map of function name → callable for tool dispatch in the WebSocket handler
TOOLS_MAP = {
    "diagnose_frame": diagnose_frame,
    "search_manual": search_manual,
    "lookup_similar_cases": lookup_similar_cases,
    "save_resolved_case": save_resolved_case,
}


def build_live_config(
    industry: str,
    equipment_model: str,
    technician_id: str,
) -> types.LiveConnectConfig:
    """Build a LiveConnectConfig for a technician session."""
    system = SYSTEM_PROMPT.format(
        industry=industry,
        equipment_model=equipment_model,
        technician_id=technician_id,
    )
    return types.LiveConnectConfig(
        system_instruction=system,
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config={"voice_name": "Aoede"}
            )
        ),
        tools=[diagnose_frame, search_manual, lookup_similar_cases, save_resolved_case],
        realtime_input_config=types.RealtimeInputConfig(
            automatic_activity_detection=types.AutomaticActivityDetection(
                disabled=False,
                start_of_speech_sensitivity="START_SENSITIVITY_HIGH",
                end_of_speech_sensitivity="END_SENSITIVITY_HIGH",
            )
        ),
    )
