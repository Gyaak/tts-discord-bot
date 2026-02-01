from datetime import datetime
from sqlalchemy import BigInteger, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column
from postgres.connection import Base


class GuildChannel(Base):
    """ORM model for guild channels table."""

    __tablename__ = "guild_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    __table_args__ = (Index("uq_guild_channel", "guild_id", "channel_id", unique=True),)
