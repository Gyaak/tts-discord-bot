"""User repository for database operations."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tts_bot.orm.user import User


class UserRepository:
    """Repository for User database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def get_user(self, discord_id: int, guild_id: int) -> Optional[User]:
        """Get user by discord_id and guild_id.

        Args:
            discord_id: Discord user ID
            guild_id: Discord guild (server) ID

        Returns:
            User object if found, None otherwise
        """
        stmt = select(User).where(
            User.discord_id == discord_id,
            User.guild_id == guild_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        discord_id: int,
        guild_id: int,
        username: str,
        rate: int = 100,
        pitch: int = 0
    ) -> User:
        """Create a new user.

        Args:
            discord_id: Discord user ID
            guild_id: Discord guild (server) ID
            username: Discord username
            rate: Speech rate percentage (20-200, default: 100)
            pitch: Speech pitch offset (-50 to +50, default: 0)

        Returns:
            Created User object
        """
        user = User(
            discord_id=discord_id,
            guild_id=guild_id,
            username=username,
            rate=rate,
            pitch=pitch
        )
        self.session.add(user)
        await self.session.flush()  # Get the ID
        return user

    async def update_user_voice(
        self,
        discord_id: int,
        guild_id: int,
        rate: int,
        pitch: int
    ) -> Optional[User]:
        """Update user's voice settings.

        Args:
            discord_id: Discord user ID
            guild_id: Discord guild (server) ID
            rate: New speech rate percentage (20-200)
            pitch: New speech pitch offset (-50 to +50)

        Returns:
            Updated User object if found, None otherwise
        """
        user = await self.get_user(discord_id, guild_id)
        if user:
            user.rate = rate
            user.pitch = pitch
            await self.session.flush()
        return user

    async def get_or_create_user(
        self,
        discord_id: int,
        guild_id: int,
        username: str
    ) -> User:
        """Get existing user or create new one with default settings.

        Args:
            discord_id: Discord user ID
            guild_id: Discord guild (server) ID
            username: Discord username

        Returns:
            User object (existing or newly created)
        """
        user = await self.get_user(discord_id, guild_id)
        if not user:
            user = await self.create_user(discord_id, guild_id, username)
        return user

    async def delete_user(self, discord_id: int, guild_id: int) -> bool:
        """Delete user.

        Args:
            discord_id: Discord user ID
            guild_id: Discord guild (server) ID

        Returns:
            True if deleted, False if not found
        """
        user = await self.get_user(discord_id, guild_id)
        if user:
            await self.session.delete(user)
            await self.session.flush()
            return True
        return False
