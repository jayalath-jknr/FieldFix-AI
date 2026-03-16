"""Tests for visual_diagnosis.py — Gemini vision analysis."""

import json
from unittest.mock import MagicMock, patch

import pytest


VALID_RESPONSE = {
    "issues_found": [
        {
            "description": "Burn mark on DC+ terminal",
            "location_in_frame": "lower-left connector",
        }
    ],
    "severity": "high",
    "likely_fault": "DC terminal overheating",
    "confidence": 0.85,
    "draw_attention_to": "The darkened connector on the lower left",
    "immediate_action": "Power off and inspect the DC+ terminal connection",
    "parts_likely_needed": ["MC4 connector", "DC cable"],
    "safe_to_operate": False,
    "needs_closer_view": False,
    "closer_view_instruction": "",
}


@pytest.fixture
def mock_genai_client():
    """Mock Gemini API client."""
    with patch("tools.visual_diagnosis.genai.Client") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        yield mock_client


class TestDiagnoseFrame:
    """Tests for the diagnose_frame tool."""

    def test_valid_json_response(self, mock_genai_client):
        """Verify correct parsing of a valid JSON vision response."""
        from tools.visual_diagnosis import diagnose_frame

        mock_response = MagicMock()
        mock_response.text = json.dumps(VALID_RESPONSE)
        mock_genai_client.models.generate_content.return_value = mock_response

        result = diagnose_frame.__wrapped__(
            image_base64="dGVzdA==",  # base64 of "test"
            description="Burn mark near connector",
            industry="solar",
            equipment_model="SMA-Sunny5000",
        )

        assert result["severity"] == "high"
        assert result["likely_fault"] == "DC terminal overheating"
        assert result["confidence"] == 0.85
        assert result["safe_to_operate"] is False
        assert len(result["issues_found"]) == 1

    def test_json_with_markdown_fences(self, mock_genai_client):
        """Verify parsing when response is wrapped in markdown code fences."""
        from tools.visual_diagnosis import diagnose_frame

        mock_response = MagicMock()
        mock_response.text = f"```json\n{json.dumps(VALID_RESPONSE)}\n```"
        mock_genai_client.models.generate_content.return_value = mock_response

        result = diagnose_frame.__wrapped__(
            image_base64="dGVzdA==",
            description="Test",
            industry="solar",
            equipment_model="SMA-Sunny5000",
        )

        assert result["likely_fault"] == "DC terminal overheating"

    def test_malformed_json_returns_fallback(self, mock_genai_client):
        """Verify fallback response when Gemini returns invalid JSON."""
        from tools.visual_diagnosis import diagnose_frame

        mock_response = MagicMock()
        mock_response.text = "This is not valid JSON at all"
        mock_genai_client.models.generate_content.return_value = mock_response

        result = diagnose_frame.__wrapped__(
            image_base64="dGVzdA==",
            description="Test",
            industry="solar",
            equipment_model="SMA-Sunny5000",
        )

        assert result["severity"] == "unknown"
        assert result["likely_fault"] == "Unable to parse visual"
        assert result["confidence"] == 0.0
        assert result["needs_closer_view"] is True
        assert result["safe_to_operate"] is False

    def test_api_error_raises_exception(self, mock_genai_client):
        """Verify API errors are re-raised after logging."""
        from tools.visual_diagnosis import diagnose_frame

        mock_genai_client.models.generate_content.side_effect = Exception(
            "API rate limit exceeded"
        )

        with pytest.raises(Exception, match="API rate limit exceeded"):
            diagnose_frame.__wrapped__(
                image_base64="dGVzdA==",
                description="Test",
                industry="solar",
                equipment_model="SMA-Sunny5000",
            )

    def test_needs_closer_view_response(self, mock_genai_client):
        """Verify proper handling of 'needs closer view' responses."""
        from tools.visual_diagnosis import diagnose_frame

        closer_view_response = {
            "issues_found": [],
            "severity": "unknown",
            "likely_fault": "Cannot determine — image too dark",
            "confidence": 0.1,
            "draw_attention_to": "",
            "immediate_action": "Shine a flashlight on the inverter panel",
            "parts_likely_needed": [],
            "safe_to_operate": True,
            "needs_closer_view": True,
            "closer_view_instruction": "Show the LED panel from directly in front, 30cm away",
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(closer_view_response)
        mock_genai_client.models.generate_content.return_value = mock_response

        result = diagnose_frame.__wrapped__(
            image_base64="dGVzdA==",
            description="Can't see the display",
            industry="solar",
            equipment_model="SMA-Sunny5000",
        )

        assert result["needs_closer_view"] is True
        assert "30cm" in result["closer_view_instruction"]
