from dotenv import find_dotenv
from pydantic_settings import BaseSettings


class DBSettings(BaseSettings):
    POSTGRES_HOST: str ="localhost"
    POSTGRES_PORT: int = 5678
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "postgres"

    class Config:
        env_file = find_dotenv()
        env_file_encoding = "utf-8"
        extra = "ignore"

db_settings = DBSettings()
