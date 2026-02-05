from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tts_bot.orm.guild_settings import GuildSettings


class GuildSettingsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_guild_settings(self, guild_id: int) -> GuildSettings | None:
        """Get guild settings by guild_id."""
        stmt = select(GuildSettings).where(GuildSettings.guild_id == guild_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_or_create_guild_settings(self, guild_id: int) -> GuildSettings:
        """Get or create guild settings."""
        settings = await self.get_guild_settings(guild_id)
        if settings:
            return settings

        settings = GuildSettings(guild_id=guild_id)
        self.session.add(settings)
        await self.session.commit()
        await self.session.refresh(settings)
        return settings

    async def set_default_voice_channel(self, guild_id: int, channel_id: int) -> GuildSettings:
        """Set default voice channel for guild."""
        settings = await self.get_or_create_guild_settings(guild_id)
        settings.default_voice_channel_id = channel_id
        await self.session.commit()
        await self.session.refresh(settings)
        return settings

    async def get_default_voice_channel(self, guild_id: int) -> int | None:
        """Get default voice channel ID for guild."""
        settings = await self.get_guild_settings(guild_id)
        return settings.default_voice_channel_id if settings else None
