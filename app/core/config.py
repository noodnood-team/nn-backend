from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = Field(default="nn-backend", alias="APP_NAME")
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")

    allowed_origins: str = Field(default="http://localhost:3000", alias="ALLOWED_ORIGINS")

    max_image_size_bytes: int = Field(default=5 * 1024 * 1024, alias="MAX_IMAGE_SIZE_BYTES")

    food_clip_model_id: str = Field(
        default="openai/clip-vit-base-patch32",
        alias="FOOD_CLIP_MODEL_ID",
    )
    food_clip_threshold: float = Field(
        default=0.55,
        alias="FOOD_CLIP_THRESHOLD",
        ge=0.0,
        le=1.0,
    )

    inference_base_url: str = Field(default="http://localhost:8001", alias="INFERENCE_BASE_URL")
    inference_predict_path: str = Field(default="/predict", alias="INFERENCE_PREDICT_PATH")
    inference_timeout_seconds: float = Field(default=10.0, alias="INFERENCE_TIMEOUT_SECONDS")


@lru_cache
def get_settings() -> Settings:
    return Settings()
