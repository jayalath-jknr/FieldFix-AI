from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # GCP
    gcp_project_id: str = "fieldfix-demo"
    gcp_region: str = "us-central1"
    gcs_bucket_name: str = "fieldfix-knowledge-base"
    firestore_collection: str = "fault_cases"

    # Gemini
    gemini_live_model: str = "gemini-2.5-flash-live"
    gemini_vision_model: str = "gemini-2.5-flash"
    embedding_model: str = "text-embedding-004"

    # App
    environment: Literal["local", "staging", "production"] = "local"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173"]
    max_frame_size_bytes: int = 500_000  # 500KB max per frame
    frame_sample_interval_ms: int = 2500  # Sample camera every 2.5s

    class Config:
        env_file = ".env"


settings = Settings()
