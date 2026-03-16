"""
Tool: search_manual
RAG over equipment manuals stored in Cloud Storage as pre-embedded chunks.
No external vector DB required — cosine similarity in-process for MVP.

Ingestion: run tools/ingest_pdf.py once per manual.
Storage: gs://{bucket}/{industry}/{equipment_model}/chunks.json
"""

import json

import numpy as np
from functools import lru_cache
from google.adk.tools import tool
from google.cloud import storage
from google import genai

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=20)
def _load_chunks(industry: str, equipment_model: str) -> tuple[dict, ...]:
    """Load and cache chunks from Cloud Storage. Returns tuple for hashability."""
    gcs = storage.Client()
    bucket = gcs.bucket(settings.gcs_bucket_name)
    blob = bucket.blob(f"{industry}/{equipment_model}/chunks.json")

    if not blob.exists():
        logger.warning(
            "No knowledge base found",
            industry=industry,
            equipment_model=equipment_model,
        )
        return ()

    chunks = json.loads(blob.download_as_text())
    return tuple(chunks) if isinstance(chunks, list) else ()


def _embed(text: str) -> list[float]:
    """Embed text using Vertex AI text-embedding-004."""
    client = genai.Client()
    response = client.models.embed_content(
        model=settings.embedding_model,
        content=text,
    )
    return response.embeddings[0].values


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two embedding vectors."""
    a_arr = np.array(a)
    b_arr = np.array(b)
    norm = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if norm == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / norm)


@tool
def search_manual(
    query: str,
    industry: str,
    equipment_model: str,
    top_k: int = 3,
) -> dict:
    """
    Search the equipment manual knowledge base for relevant sections.
    ALWAYS call this before giving repair advice. The results must be
    cited in your response with section and page number.

    Args:
        query: The technical question or fault description to search for
        industry: Equipment industry (solar, telecom, hvac, lab, factory)
        equipment_model: Specific model identifier
        top_k: Number of results to return (default 3)

    Returns:
        Top matching manual sections with citation references
    """
    chunks_tuple = _load_chunks(industry, equipment_model)
    chunks = list(chunks_tuple)

    if not chunks:
        return {
            "found": False,
            "message": f"No manual loaded for {equipment_model}. Proceeding from general knowledge.",
            "results": [],
        }

    query_embedding = _embed(query)

    scored = []
    for chunk in chunks:
        if "embedding" not in chunk:
            continue
        score = _cosine_similarity(query_embedding, chunk["embedding"])
        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]

    results = []
    for score, chunk in top:
        if score < 0.3:  # Relevance threshold
            continue
        results.append(
            {
                "text": chunk["text"][:600],  # Truncate for context window
                "citation": f"{chunk['source']} §{chunk['section']} · p.{chunk['page']}",
                "source": chunk["source"],
                "section": chunk["section"],
                "page": chunk["page"],
                "relevance_score": round(score, 3),
            }
        )

    logger.info(
        "KB search complete",
        query=query[:50],
        results_found=len(results),
    )

    return {
        "found": len(results) > 0,
        "results": results,
    }
