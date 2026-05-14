from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    environment: str = "production"

    jwt_secret: str
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 30

    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str = "wardrobe-images"
    minio_secure: bool = False
    minio_external_endpoint: str = ""

    claude_api_key: str = ""
    claude_model: str = "claude-haiku-4-5-20251001"

    vision_backend: str = "local"  # "claude" | "local"
    ollama_host: str = "http://ollama:11434"
    vision_model: str = "llama3.2-vision:11b"
    text_model: str = "llama3.2"  # text-only model for outfit suggestions

    # Dev overrides — set in .env to use faster models during testing
    dev_vision_model: str = ""
    dev_text_model: str = ""

    # Ollama performance settings
    ollama_keep_alive: str = "0"   # "0" = unload from VRAM immediately; "5m" = keep warm for 5 minutes
    ollama_num_ctx: int = 4096     # context window — reduces peak VRAM vs llama3.2 default (up to 131072)

    @property
    def active_vision_model(self) -> str:
        return self.dev_vision_model or self.vision_model

    @property
    def active_text_model(self) -> str:
        return self.dev_text_model or self.text_model

    openweather_api_key: str
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5"
    openweather_default_city: str = "New York"
    openweather_default_country: str = "US"

    max_upload_size_bytes: int = 10 * 1024 * 1024  # 10 MB


settings = Settings()
