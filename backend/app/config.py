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

    claude_api_key: str
    claude_model: str = "claude-haiku-4-5-20251001"

    openweather_api_key: str
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5"
    openweather_default_city: str = "New York"
    openweather_default_country: str = "US"

    max_upload_size_bytes: int = 10 * 1024 * 1024  # 10 MB


settings = Settings()
