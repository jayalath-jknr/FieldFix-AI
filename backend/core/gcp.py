"""
GCP client singletons for Firestore, Cloud Storage, and Vertex AI.
Uses Application Default Credentials (ADC) — never hardcode keys.
"""

from functools import lru_cache

from google.cloud import firestore
from google.cloud import storage

from core.config import settings


@lru_cache(maxsize=1)
def get_firestore() -> firestore.Client:
    """Get or create the Firestore client singleton."""
    return firestore.Client(project=settings.gcp_project_id)


@lru_cache(maxsize=1)
def get_gcs_client() -> storage.Client:
    """Get or create the Cloud Storage client singleton."""
    return storage.Client(project=settings.gcp_project_id)


@lru_cache(maxsize=1)
def get_gcs_bucket() -> storage.Bucket:
    """Get the knowledge base bucket."""
    client = get_gcs_client()
    return client.bucket(settings.gcs_bucket_name)
