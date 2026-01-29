from pydantic_settings import BaseSettings, SettingsConfigDict


class PollySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AWS_",
        env_file=".env",
        extra="ignore",
    )

    access_key_id: str
    secret_access_key: str
    region_name: str = "ap-northeast-2"
    voice_id: str = "Seoyeon"
