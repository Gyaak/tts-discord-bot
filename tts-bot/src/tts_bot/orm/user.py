"""User ORM model for TTS Bot.

Stores per-user voice settings for each guild (server).
- rate: Speech rate (default: medium, range: x-slow, slow, medium, fast, x-fast)
- pitch: Speech pitch (default: medium, range: x-low, low, medium, high, x-high)
"""

from datetime import datetime
from sqlalchemy import BigInteger, String, DateTime, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column
from postgres.connection import Base


class User(Base):
    """User table.

    Stores TTS voice settings per Discord user per guild (server).
    Each user can have different settings in different guilds.
    """

    __tablename__ = "users"

    # Primary Key (Auto-increment)
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Primary key"
    )

    # Discord User ID
    discord_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="Discord user ID"
    )

    # Discord Guild (Server) ID
    guild_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="Discord guild (server) ID"
    )

    # Discord Username (for information)
    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Discord username"
    )

    # Speech rate setting (percentage: 20-200, default: 100)
    # 100 = normal speed, 150 = 1.5x speed, 50 = 0.5x speed
    rate: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        comment="Speech rate percentage (20-200, default: 100)"
    )

    # Speech pitch setting (percentage offset: -50 to +50, default: 0)
    # 0 = normal pitch, +20 = higher pitch, -20 = lower pitch
    pitch: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Speech pitch offset (-50 to +50, default: 0)"
    )

    # Creation time
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Creation timestamp"
    )

    # Update time
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Last update timestamp"
    )

    # Unique constraint: one setting per user per guild
    __table_args__ = (
        Index('ix_user_guild', 'discord_id', 'guild_id', unique=True),
    )

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, discord_id={self.discord_id}, guild_id={self.guild_id}, "
            f"username='{self.username}', rate='{self.rate}', pitch='{self.pitch}')>"
        )

    def to_dict(self) -> dict:
        """Convert user information to dict."""
        return {
            "id": self.id,
            "discord_id": self.discord_id,
            "guild_id": self.guild_id,
            "username": self.username,
            "rate": self.rate,
            "pitch": self.pitch,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
