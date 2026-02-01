from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from tts_bot.orm.guild_channel import GuildChannel


class GuildChannelRepository:
    """Repository for guild channels operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_channel(self, guild_id: int, channel_id: int) -> GuildChannel:
        """Add a channel to the guild's TTS channels."""
        guild_channel = GuildChannel(guild_id=guild_id, channel_id=channel_id)
        self.session.add(guild_channel)
        await self.session.commit()
        await self.session.refresh(guild_channel)
        return guild_channel

    async def remove_channel(self, guild_id: int, channel_id: int) -> bool:
        """Remove a channel from the guild's TTS channels. Returns True if removed, False if not found."""
        stmt = delete(GuildChannel).where(
            GuildChannel.guild_id == guild_id, GuildChannel.channel_id == channel_id
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def get_guild_channels(self, guild_id: int) -> list[GuildChannel]:
        """Get all TTS-enabled channels for a guild."""
        stmt = select(GuildChannel).where(GuildChannel.guild_id == guild_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def is_channel_enabled(self, guild_id: int, channel_id: int) -> bool:
        """Check if a channel is TTS-enabled for a guild."""
        stmt = select(GuildChannel).where(
            GuildChannel.guild_id == guild_id, GuildChannel.channel_id == channel_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
