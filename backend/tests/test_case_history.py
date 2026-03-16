"""Tests for case_history.py — Firestore case lookup and save."""

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest


def _make_mock_doc(doc_id: str, data: dict):
    """Create a mock Firestore document."""
    mock_doc = MagicMock()
    mock_doc.id = doc_id
    mock_doc.to_dict.return_value = data
    return mock_doc


SAMPLE_CASES = [
    _make_mock_doc(
        "case_001",
        {
            "equipment_model": "SMA-Sunny5000",
            "industry": "solar",
            "fault_summary": "Red LED blinking DC overvoltage",
            "steps_taken": ["Checked voltage", "Reconfigured string"],
            "resolution": "Reduced string size",
            "note": "Common in summer",
            "resolved": True,
            "technician_count": 3,
            "timestamp": datetime.now(timezone.utc) - timedelta(days=18),
        },
    ),
    _make_mock_doc(
        "case_002",
        {
            "equipment_model": "SMA-Sunny5000",
            "industry": "solar",
            "fault_summary": "No AC output grid impedance fault",
            "steps_taken": ["Verified grid voltage", "Adjusted threshold"],
            "resolution": "Adjusted impedance threshold",
            "note": "Local grid issue",
            "resolved": True,
            "technician_count": 2,
            "timestamp": datetime.now(timezone.utc) - timedelta(days=35),
        },
    ),
    _make_mock_doc(
        "case_003",
        {
            "equipment_model": "SMA-Sunny5000",
            "industry": "solar",
            "fault_summary": "Fan noise vibration bearing worn",
            "steps_taken": ["Inspected fan", "Replaced bearing"],
            "resolution": "Replaced fan bearing",
            "note": "",
            "resolved": True,
            "technician_count": 1,
            "timestamp": datetime.now(timezone.utc) - timedelta(days=60),
        },
    ),
]


@pytest.fixture
def mock_firestore():
    """Mock Firestore client with sample cases."""
    with patch("tools.case_history.firestore.Client") as mock_cls:
        mock_db = MagicMock()
        mock_cls.return_value = mock_db

        mock_collection = MagicMock()
        mock_db.collection.return_value = mock_collection

        # Chain .where().where().order_by().limit()
        mock_query = MagicMock()
        mock_collection.where.return_value = mock_query
        mock_query.where.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = iter(SAMPLE_CASES)

        yield mock_db


class TestLookupSimilarCases:
    """Tests for lookup_similar_cases tool."""

    def test_keyword_overlap_ranking(self, mock_firestore):
        """Verify cases are ranked by keyword overlap with fault description."""
        from tools.case_history import lookup_similar_cases

        result = lookup_similar_cases.__wrapped__(
            fault_description="DC overvoltage red LED blinking",
            equipment_model="SMA-Sunny5000",
            industry="solar",
            limit=3,
        )

        assert result["found"] is True
        assert len(result["cases"]) > 0
        # case_001 has more keyword overlap ("red", "LED", "blinking", "DC", "overvoltage")
        assert result["cases"][0]["case_id"] == "case_001"

    def test_no_matching_keywords_returns_empty(self, mock_firestore):
        """Verify empty results when no keywords match."""
        from tools.case_history import lookup_similar_cases

        result = lookup_similar_cases.__wrapped__(
            fault_description="completely unrelated description xyz abc",
            equipment_model="SMA-Sunny5000",
            industry="solar",
            limit=3,
        )

        assert result["found"] is False
        assert len(result["cases"]) == 0

    def test_stop_words_are_filtered(self, mock_firestore):
        """Verify common stop words don't affect ranking."""
        from tools.case_history import lookup_similar_cases

        result = lookup_similar_cases.__wrapped__(
            fault_description="the is a an overvoltage",
            equipment_model="SMA-Sunny5000",
            industry="solar",
            limit=3,
        )

        assert result["found"] is True
        # Should match based on "overvoltage" only, not stop words
        assert any("overvoltage" in c["fault_summary"].lower() for c in result["cases"])

    def test_limit_respected(self, mock_firestore):
        """Verify limit parameter caps results."""
        from tools.case_history import lookup_similar_cases

        result = lookup_similar_cases.__wrapped__(
            fault_description="LED fault grid impedance overvoltage fan noise",
            equipment_model="SMA-Sunny5000",
            industry="solar",
            limit=1,
        )

        assert len(result["cases"]) <= 1


class TestSaveResolvedCase:
    """Tests for save_resolved_case tool."""

    def test_save_round_trip(self, mock_firestore):
        """Verify case data is saved correctly to Firestore."""
        from tools.case_history import save_resolved_case

        # Mock the add method to return a doc ref
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "new_case_123"
        mock_firestore.collection.return_value.add.return_value = (
            None,
            mock_doc_ref,
        )

        result = save_resolved_case.__wrapped__(
            equipment_model="SMA-Sunny5000",
            industry="solar",
            fault_summary="Test fault",
            steps_taken=["Step 1", "Step 2"],
            resolution="Fixed it",
            technician_id="tech_test",
            technician_note="Test note",
            parts_replaced=["Part A"],
        )

        assert result["saved"] is True
        assert result["case_id"] == "new_case_123"

        # Verify the data passed to Firestore
        call_args = mock_firestore.collection.return_value.add.call_args
        saved_data = call_args[0][0]
        assert saved_data["equipment_model"] == "SMA-Sunny5000"
        assert saved_data["fault_summary"] == "Test fault"
        assert saved_data["steps_taken"] == ["Step 1", "Step 2"]
        assert saved_data["resolved"] is True

    def test_save_failure_handled(self, mock_firestore):
        """Verify save failures return error gracefully."""
        from tools.case_history import save_resolved_case

        mock_firestore.collection.return_value.add.side_effect = Exception(
            "Firestore unavailable"
        )

        result = save_resolved_case.__wrapped__(
            equipment_model="SMA-Sunny5000",
            industry="solar",
            fault_summary="Test fault",
            steps_taken=["Step 1"],
            resolution="Fixed it",
            technician_id="tech_test",
        )

        assert result["saved"] is False
        assert result["case_id"] is None
