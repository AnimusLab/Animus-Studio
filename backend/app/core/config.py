from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── App & Identity ───────────────────────────────────────
    app_name: str = "Animus Studio"
    app_version: str = "0.1.0"
    studio_name: str = "Animus Studio"
    studio_version: str = "0.1.0"
    instance_id: str = "local-dev"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:80", "http://localhost:3000"]

    # ─── Mission Defaults ─────────────────────────────────────
    default_language: str = "en"
    default_brand: str = "AnimusLab"
    default_audience: str = "Software Engineers"
    default_tone: str = "Professional"

    # ─── Worker Configuration ─────────────────────────────────
    worker_timeout: int = 600
    worker_max_retries: int = 3
    worker_concurrency: int = 2

    # ─── Database & Redis ─────────────────────────────────────
    database_url: str = "postgresql+asyncpg://animus:animuspass@localhost:5432/animus"
    redis_url: str = "redis://localhost:6379/0"

    # ─── Auth ─────────────────────────────────────────────────
    access_token_expire_minutes: int = 60 * 24  # 24h
    algorithm: str = "HS256"

    # ─── LLM & Feature Flags ──────────────────────────────────
    enable_local_models: bool = True
    enable_cloud_models: bool = False
    enable_human_approval: bool = True
    enable_memory: bool = True
    enable_sandbox: bool = False
    enable_event_replay: bool = True
    enable_mission_timeline: bool = True
    enable_provider_healthcheck: bool = True
    enable_runtime_doctor: bool = True

    # ─── Providers ────────────────────────────────────────────
    voice_provider: str = "auto"  # auto | kokoro | piper | elevenlabs
    kokoro_voice: str = "af_heart"
    piper_model: str = "en_US-lessac-medium"
    whisper_model: str = "small"
    
    litellm_model: str = "openai/gpt-4o"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    groq_api_key: str = ""
    openrouter_api_key: str = ""
    google_api_key: str = ""
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""
    tavily_api_key: str = ""
    brave_api_key: str = ""
    serper_api_key: str = ""

    # ─── Memory & Tuning ──────────────────────────────────────
    memory_retention_days: int = 365
    memory_top_k: int = 10
    memory_min_similarity: float = 0.82

    # ─── Runtime Bounds & Storage ─────────────────────────────
    max_upload_size_mb: int = 2048
    temp_directory: str = "./tmp"
    cache_directory: str = "./cache"
    storage_backend: str = "local"
    storage_local_path: str = "./storage"
    s3_bucket: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_endpoint_url: str = ""

    # ─── Platforms ────────────────────────────────────────────
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    youtube_redirect_uri: str = "http://localhost:8000/api/v1/integrations/youtube/callback"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
