"""Application configuration using Pydantic settings."""

from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via .env file or environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    secret_key: str = Field(min_length=32)
    # Accept str or List[str] to handle both env var formats
    cors_origins: str | List[str] = Field(default="http://localhost:3000")

    # Database
    database_url: str = Field(
        description="PostgreSQL connection string",
        examples=["postgresql://user:pass@localhost:5432/evo_ai"]
    )
    database_pool_size: int = Field(default=20, ge=1, le=100)
    database_max_overflow: int = Field(default=10, ge=0, le=50)

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string"
    )
    redis_cache_ttl: int = Field(default=3600, ge=60)

    # S3 Storage
    s3_endpoint: str = Field(default="http://localhost:9000")
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str = Field(default="evo-ai-reports")
    s3_region: str = Field(default="us-east-1")

    # OpenAI
    openai_api_key: str
    openai_default_model: str = Field(default="gpt-4o")
    openai_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    openai_max_tokens: int = Field(default=4000, ge=100, le=128000)

    # Anthropic (optional)
    anthropic_api_key: str = Field(default="")

    # Ray
    ray_address: str = Field(default="ray://localhost:10001")
    ray_namespace: str = Field(default="evo_ai")

    # Observability
    otel_exporter_otlp_endpoint: str = Field(default="http://localhost:4317")
    otel_service_name: str = Field(default="evo-ai-backend")
    otel_service_version: str = Field(default="1.0.0")

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")  # 'json' or 'console'

    # JWT
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_minutes: int = Field(default=60, ge=5)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str] | None) -> List[str]:
        """Parse CORS origins from comma-separated string or list."""
        # Handle None or empty string - use default
        if v is None or (isinstance(v, str) and not v.strip()):
            return ["http://localhost:3000"]

        # Parse comma-separated string
        if isinstance(v, str):
            origins = [origin.strip() for origin in v.split(",") if origin.strip()]
            return origins if origins else ["http://localhost:3000"]

        # Already a list
        return v if v else ["http://localhost:3000"]


# Global settings instance
settings = Settings()  # type: ignore[call-arg]
