"""
Tools: lookup_similar_cases, save_resolved_case
Firestore-backed institutional memory of fault resolutions.
"""

from datetime import datetime, timezone


from google.cloud import firestore

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


def _get_db():
    """Get Firestore client instance."""
    return firestore.Client()


def lookup_similar_cases(
    fault_description: str,
    equipment_model: str,
    industry: str,
    limit: int = 3,
) -> dict:
    """
    Look up Firestore for previously resolved cases matching this fault
    on the same equipment model. Call this immediately after diagnosing
    the fault type. If results exist, mention them to the technician.

    Args:
        fault_description: Brief description of the fault observed
        equipment_model: Equipment model identifier
        industry: Industry category
        limit: Max cases to return

    Returns:
        List of similar resolved cases with resolution steps
    """
    db = _get_db()

    try:
        cases_ref = (
            db.collection(settings.firestore_collection)
            .where("equipment_model", "==", equipment_model)
            .where("resolved", "==", True)
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(50)
        )

        # Simple keyword matching for MVP (replace with embedding similarity in v2)
        fault_words = set(fault_description.lower().split())
        stop_words = {
            "the", "a", "an", "is", "it", "not", "and", "or", "in", "on",
            "to", "of", "for", "with", "has", "was", "are", "been", "be",
        }
        fault_words -= stop_words

        ranked = []
        for doc in cases_ref.stream():
            data = doc.to_dict()
            summary_words = set(data.get("fault_summary", "").lower().split())
            overlap = len(fault_words & summary_words)
            if overlap > 0:
                ranked.append((overlap, data, doc.id))

        ranked.sort(reverse=True)
        top = ranked[:limit]

        cases = []
        for _, data, doc_id in top:
            cases.append(
                {
                    "case_id": doc_id,
                    "fault_summary": data.get("fault_summary", ""),
                    "resolution": data.get("resolution", ""),
                    "steps_taken": data.get("steps_taken", []),
                    "technician_note": data.get("note", ""),
                    "resolved_date": data.get(
                        "timestamp", datetime.now(timezone.utc)
                    ).strftime("%Y-%m-%d"),
                    "technician_count": data.get("technician_count", 1),
                }
            )

        logger.info(
            "Case history lookup",
            equipment_model=equipment_model,
            results=len(cases),
        )

        return {
            "found": len(cases) > 0,
            "cases": cases,
            "message": (
                f"Found {len(cases)} similar resolved case(s) for {equipment_model}."
                if cases
                else f"No previous cases found for this fault on {equipment_model}."
            ),
        }

    except Exception as e:
        logger.error("Case lookup failed", error=str(e))
        return {"found": False, "cases": [], "message": "Case history unavailable."}


def save_resolved_case(
    equipment_model: str,
    industry: str,
    fault_summary: str,
    steps_taken: list[str],
    resolution: str,
    technician_id: str,
    technician_note: str = "",
    parts_replaced: list[str] | None = None,
) -> dict:
    """
    Save this successfully resolved repair case to Firestore.
    Call this ONLY when the technician confirms the fix worked.
    This builds institutional memory for future technicians.

    Args:
        equipment_model: Equipment model identifier
        industry: Industry category
        fault_summary: One-sentence description of the fault
        steps_taken: Ordered list of repair steps that were performed
        resolution: What ultimately fixed the problem
        technician_id: ID of the technician who resolved this
        technician_note: Optional note from the technician
        parts_replaced: List of parts that were replaced

    Returns:
        Confirmation with the saved case ID
    """
    db = _get_db()

    try:
        doc_data = {
            "equipment_model": equipment_model,
            "industry": industry,
            "fault_summary": fault_summary,
            "steps_taken": steps_taken,
            "resolution": resolution,
            "technician_id": technician_id,
            "note": technician_note,
            "parts_replaced": parts_replaced or [],
            "resolved": True,
            "technician_count": 1,
            "timestamp": datetime.now(timezone.utc),
        }

        _, doc_ref = db.collection(settings.firestore_collection).add(doc_data)

        logger.info(
            "Case saved",
            case_id=doc_ref.id,
            equipment_model=equipment_model,
            fault=fault_summary[:50],
        )

        return {
            "saved": True,
            "case_id": doc_ref.id,
            "message": "This case has been saved to your team's knowledge base.",
        }

    except Exception as e:
        logger.error("Case save failed", error=str(e))
        return {"saved": False, "case_id": None, "message": "Failed to save case."}
