"""
CLI script: PDF ingestion pipeline.
Run once per manual before deploying.

Usage:
    python -m tools.ingest_pdf \
        --pdf manuals/sma_inverter.pdf \
        --industry solar \
        --model SMA-Sunny5000 \
        --source "SMA Inverter Manual"
"""

import json
import argparse

import fitz  # PyMuPDF
from google import genai
from google.cloud import storage

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)

CHUNK_SIZE = 350  # words per chunk
CHUNK_OVERLAP = 50  # word overlap between chunks


def detect_section(lines: list[str]) -> str:
    """Heuristic section heading detection."""
    for line in lines[:5]:
        line = line.strip()
        if not line:
            continue
        # Numbered section (e.g. "4.3 DC Connection Procedure")
        if line and (line[0].isdigit() or line.isupper()):
            return line[:60]
    return "—"


def chunk_text(text: str, page_num: int, source: str) -> list[dict]:
    """Chunk a page's text into overlapping windows."""
    words = text.split()
    chunks = []
    step = CHUNK_SIZE - CHUNK_OVERLAP
    for i in range(0, max(1, len(words) - CHUNK_SIZE + CHUNK_OVERLAP), step):
        chunk_words = words[i : i + CHUNK_SIZE]
        if len(chunk_words) < 30:
            continue
        chunk_str = " ".join(chunk_words)
        lines = chunk_str.split("\n")
        chunks.append(
            {
                "text": chunk_str,
                "source": source,
                "section": detect_section(lines),
                "page": page_num,
            }
        )
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Add embeddings to all chunks using Vertex AI text-embedding-004."""
    import os
    api_key = os.environ.get("GOOGLE_API_KEY")
    if api_key:
        client = genai.Client(api_key=api_key)
    else:
        client = genai.Client(
            vertexai=True,
            project=settings.gcp_project_id,
            location=settings.gcp_region,
        )
    embedded = []

    batch_size = 5  # Embed in batches to respect rate limits
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c["text"] for c in batch]

        for j, text in enumerate(texts):
            response = client.models.embed_content(
                model=settings.embedding_model,
                contents=text,
            )
            batch[j]["embedding"] = response.embeddings[0].values

        embedded.extend(batch)
        logger.info(
            f"Embedded {min(i + batch_size, len(chunks))}/{len(chunks)} chunks"
        )

    return embedded


def upload_to_gcs(
    chunks: list[dict],
    industry: str,
    equipment_model: str,
) -> str:
    """Upload embedded chunks JSON to Cloud Storage."""
    gcs = storage.Client()
    bucket = gcs.bucket(settings.gcs_bucket_name)
    path = f"{industry}/{equipment_model}/chunks.json"
    blob = bucket.blob(path)
    blob.upload_from_string(
        json.dumps(chunks),
        content_type="application/json",
    )
    return f"gs://{settings.gcs_bucket_name}/{path}"


def ingest(pdf_path: str, industry: str, equipment_model: str, source: str):
    """Full ingestion pipeline: PDF → chunks → embeddings → GCS."""
    logger.info(f"Opening {pdf_path}")
    doc = fitz.open(pdf_path)
    all_chunks = []

    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        if not text.strip():
            continue
        page_chunks = chunk_text(text, page_num, source)
        all_chunks.extend(page_chunks)

    logger.info(f"Generated {len(all_chunks)} chunks from {len(doc)} pages")
    embedded = embed_chunks(all_chunks)
    uri = upload_to_gcs(embedded, industry, equipment_model)
    logger.info(f"Uploaded to {uri}")
    return uri


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingest a PDF manual into the FieldFix knowledge base."
    )
    parser.add_argument("--pdf", required=True, help="Path to the PDF manual")
    parser.add_argument(
        "--industry",
        required=True,
        help="Industry category (solar, telecom, hvac, lab, factory)",
    )
    parser.add_argument("--model", required=True, help="Equipment model identifier")
    parser.add_argument("--source", required=True, help="Manual source name for citations")
    args = parser.parse_args()
    ingest(args.pdf, args.industry, args.model, args.source)
