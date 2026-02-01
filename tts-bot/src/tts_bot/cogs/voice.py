import discord
from discord.ext import commands
from discord import ui, app_commands
from postgres.connection import get_async_session_context
from tts_bot.repository import UserRepository, GuildChannelRepository


class VoiceSettingsModal(ui.Modal, title="Voice Settings"):
    """Modal for configuring voice settings."""

    def __init__(self, discord_id: int, guild_id: int, username: str, current_rate: int = 100, current_pitch: int = 0):
        super().__init__()
        self.discord_id = discord_id
        self.guild_id = guild_id
        self.username = username

        # Create text inputs with current values
        self.rate = ui.TextInput(
            label="Speech Rate (20-200)",
            placeholder="100 = normal, 150 = 1.5x speed, 50 = 0.5x speed",
            default=str(current_rate),
            max_length=3,
        )

        self.pitch = ui.TextInput(
            label="Speech Pitch (-50 to +50)",
            placeholder="0 = normal, +20 = higher, -20 = lower",
            default=str(current_pitch),
            max_length=3,
        )

        # Add the text inputs to the modal
        self.add_item(self.rate)
        self.add_item(self.pitch)

    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission."""
        # Parse and validate rate
        try:
            rate_value = int(self.rate.value.strip() or "100")
            if not 20 <= rate_value <= 200:
                await interaction.response.send_message(
                    "Rate must be between 20 and 200!",
                    ephemeral=True
                )
                return
        except ValueError:
            await interaction.response.send_message(
                "Rate must be a number!",
                ephemeral=True
            )
            return

        # Parse and validate pitch
        try:
            pitch_value = int(self.pitch.value.strip() or "0")
            if not -50 <= pitch_value <= 50:
                await interaction.response.send_message(
                    "Pitch must be between -50 and +50!",
                    ephemeral=True
                )
                return
        except ValueError:
            await interaction.response.send_message(
                "Pitch must be a number!",
                ephemeral=True
            )
            return

        # Create new session for this submission
        async with get_async_session_context() as session:
            user_repository = UserRepository(session)

            # Get or create user - Check if user exists, if not create it
            await user_repository.get_or_create_user(self.discord_id, self.guild_id, self.username)

            # Update existing user
            await user_repository.update_user_voice(
                self.discord_id,
                self.guild_id,
                rate_value,
                pitch_value
            )
            await interaction.response.send_message(
                f"Voice settings updated!\nRate: {rate_value}% (100 = normal)\nPitch: {pitch_value:+d} (0 = normal)",
                ephemeral=True
            )


class VoiceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="join")
    async def join(self, ctx: commands.Context) -> None:
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("음성 채널에 먼저 입장해주세요.")
            return

        channel = ctx.author.voice.channel
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect(reconnect=True, timeout=60.0)
        await ctx.send(f"{channel.name}에 입장했습니다.")

    @commands.command(name="leave")
    async def leave(self, ctx: commands.Context) -> None:
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("음성 채널에서 나갔습니다.")
        else:
            await ctx.send("봇이 음성 채널에 없습니다.")

    @commands.command(name="set-channel")
    async def set_channel(self, ctx: commands.Context) -> None:
        """Register the current channel for TTS."""
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return

        async with get_async_session_context() as session:
            channel_repo = GuildChannelRepository(session)

            # Check if already registered
            if await channel_repo.is_channel_enabled(ctx.guild.id, ctx.channel.id):
                await ctx.send(f"채널 {ctx.channel.mention}은 이미 TTS 채널로 등록되어 있습니다.")
                return

            # Add channel
            await channel_repo.add_channel(ctx.guild.id, ctx.channel.id)
            await ctx.send(f"채널 {ctx.channel.mention}을 TTS 채널로 등록했습니다.")

    @commands.command(name="rm-channel")
    async def rm_channel(self, ctx: commands.Context) -> None:
        """Unregister the current channel from TTS."""
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return

        async with get_async_session_context() as session:
            channel_repo = GuildChannelRepository(session)

            # Remove channel
            removed = await channel_repo.remove_channel(ctx.guild.id, ctx.channel.id)

            if removed:
                await ctx.send(f"채널 {ctx.channel.mention}을 TTS 채널에서 제거했습니다.")
            else:
                await ctx.send(f"채널 {ctx.channel.mention}은 TTS 채널로 등록되어 있지 않습니다.")

    @app_commands.command(name="gyak-voice-config", description="Configure your TTS voice settings (rate and pitch)")
    async def gyak_voice_config(self, interaction: discord.Interaction) -> None:
        """Open voice settings modal to configure pitch and rate."""
        if not interaction.guild:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True
            )
            return

        # Get current user settings from database (quickly)
        current_rate = 100
        current_pitch = 0

        try:
            async with get_async_session_context() as session:
                user_repository = UserRepository(session)
                user = await user_repository.get_user(interaction.user.id, interaction.guild.id)

                if user:
                    current_rate = user.rate
                    current_pitch = user.pitch
        except Exception:
            pass  # Use defaults if DB query fails

        # Create modal with current values
        modal = VoiceSettingsModal(
            interaction.user.id,
            interaction.guild.id,
            str(interaction.user),
            current_rate,
            current_pitch
        )

        # Send modal directly (no button needed for slash commands)
        await interaction.response.send_modal(modal)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VoiceCog(bot))
