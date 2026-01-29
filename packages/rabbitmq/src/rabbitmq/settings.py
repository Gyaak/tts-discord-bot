from pydantic_settings import BaseSettings, SettingsConfigDict


class RabbitMQSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RABBITMQ_",
        env_file=".env",
        extra="ignore",
    )

    host: str = "localhost"
    port: int = 5672
    username: str = "guest"
    password: str = "guest"
    vhost: str = "/"

    @property
    def url(self) -> str:
        return f"amqp://{self.username}:{self.password}@{self.host}:{self.port}/{self.vhost}"
