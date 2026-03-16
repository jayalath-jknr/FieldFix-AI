"""
Tool: diagnose_frame
Accepts a base64 JPEG camera frame + verbal description.
Returns structured diagnosis with attention directive and parts list.
"""

import base64
import json
import re


from google import genai

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)

VISION_PROMPT = """You are an expert field technician analyzing a photo of equipment.

User description: "{description}"
Industry: {industry}
Equipment: {equipment_model}

Examine this image carefully. Look for:
- Visible damage, burn marks, corrosion, loose connectors
- LED status lights and their color/blink patterns
- Cable routing issues, missing components
- Error codes on displays

Respond ONLY with valid JSON in this exact format:
{{
  "issues_found": [
    {{
      "description": "specific description of what you see",
      "location_in_frame": "where exactly in the image (e.g. lower-left connector)"
    }}
  ],
  "severity": "low | medium | high | critical",
  "likely_fault": "concise fault name",
  "confidence": 0.0 to 1.0,
  "draw_attention_to": "one specific thing in the image to look at now",
  "immediate_action": "single next action for the technician",
  "parts_likely_needed": ["part name", ...],
  "safe_to_operate": true or false,
  "needs_closer_view": true or false,
  "closer_view_instruction": "what angle/area to show if needs_closer_view is true"
}}

If the image is too blurry, dark, or not showing the relevant equipment part,
set needs_closer_view to true and provide a clear instruction."""

FALLBACK_RESULT = {
    "issues_found": [],
    "severity": "unknown",
    "likely_fault": "Unable to parse visual",
    "confidence": 0.0,
    "draw_attention_to": "",
    "immediate_action": "Please describe the issue verbally",
    "parts_likely_needed": [],
    "safe_to_operate": False,
    "needs_closer_view": True,
    "closer_view_instruction": "Show the equipment label and any indicator lights",
}


def diagnose_frame(
    image_base64: str,
    description: str,
    industry: str,
    equipment_model: str,
) -> dict:
    """
    Analyze a camera frame of the equipment to identify visible faults.
    Call this whenever a new image is received or when the technician
    describes a visual symptom. Always call search_manual after this
    to ground the diagnosis in documentation.

    Args:
        image_base64: Base64-encoded JPEG image from the camera
        description: What the technician says they're seeing or experiencing
        industry: Equipment industry category (solar, telecom, hvac, lab, factory)
        equipment_model: Specific equipment model identifier

    Returns:
        Structured diagnosis with fault details, severity, and attention directive
    """
    try:
        client = genai.Client()

        response = client.models.generate_content(
            model=settings.gemini_vision_model,
            contents=[
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_base64,
                            }
                        },
                        {
                            "text": VISION_PROMPT.format(
                                description=description,
                                industry=industry,
                                equipment_model=equipment_model,
                            )
                        },
                    ]
                }
            ],
        )

        raw = response.text.strip()
        # Strip markdown code fences if present
        raw = re.sub(r"^```json\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
        result = json.loads(raw)

        logger.info(
            "Visual diagnosis complete",
            fault=result.get("likely_fault"),
            severity=result.get("severity"),
            confidence=result.get("confidence"),
        )
        return result

    except json.JSONDecodeError as e:
        logger.error("Vision response not valid JSON", error=str(e))
        return FALLBACK_RESULT.copy()
    except Exception as e:
        logger.error("Visual diagnosis failed", error=str(e))
        raise
