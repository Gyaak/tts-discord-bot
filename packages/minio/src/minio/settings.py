from pydantic_settings import BaseSettings, SettingsConfigDict


class MinIOSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MINIO_",
        env_file=".env",
        extra="ignore",
    )

    endpoint_url: str = "http://localhost:9000"
    access_key: str = "guest"
    secret_key: str = "guest"
    bucket_name: str = "tts"
