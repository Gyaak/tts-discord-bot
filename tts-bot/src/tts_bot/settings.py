from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DISCORD_",
        env_file=".env",
        extra="ignore",
    )

    token: str
