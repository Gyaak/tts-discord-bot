from datetime import datetime
from sqlalchemy import BigInteger, Integer
from sqlalchemy.orm import Mapped, mapped_column
from postgres.connection import Base


class GuildSettings(Base):
    """ORM model for guild_settings table."""

    __tablename__ = "guild_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)
    default_voice_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
