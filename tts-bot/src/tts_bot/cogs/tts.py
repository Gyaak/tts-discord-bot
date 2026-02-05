import asyncio
import threading
from io import BytesIO
from typing import Any, TYPE_CHECKING
import re
import discord
from discord.ext import commands
from minio import MinIOClient
from rabbitmq import RabbitMQConsumer, RabbitMQPublisher
from postgres.connection import get_async_session_context
from tts_bot.repository import UserRepository, GuildChannelRepository, GuildSettingsRepository

if TYPE_CHECKING:
    from ..bot import TTSBot


class TTSCog(commands.Cog):
    PUBLISH_EXCHANGE = "tts"
    PUBLISH_ROUTING_KEY = "tts.worker"
    CONSUME_EXCHANGE = "tts"
    CONSUME_QUEUE = "tts.bot"
    CONSUME_ROUTING_KEY = "tts.bot"

    def __init__(self, bot: "TTSBot"):
        self.bot = bot
        self.minio: MinIOClient = bot.minio
        self.publisher: RabbitMQPublisher = bot.publisher
        self.consumer: RabbitMQConsumer = bot.consumer

        self._consumer_thread: threading.Thread | None = None
        self._audio_queues: dict[int, asyncio.Queue[bytes]] = {}
        self._player_tasks: dict[int, asyncio.Task] = {}

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self._start_consumer_thread()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        if not message.guild:
            return

        # 명령어는 처리하지 않음
        if message.content.startswith(self.bot.command_prefix):
            return

        # 링크 제거 필터
        message.content = re.sub(r'https?://\S+', '', message.content)

        # 멘션 제거 필터
        message.content = re.sub(r'<[^>]*>', '', message.content)

        # 특수문자 제거 필터
        message.content = re.sub(r'[^\w\s]|_', '', message.content)

        # 빈 메시지는 무시
        if not message.content.strip():
            return

        print(f"[MESSAGE] Received message from {message.author}: '{message.content}'", flush=True)

        # Check if channel is registered for TTS first
        try:
            async with get_async_session_context() as session:
                channel_repo = GuildChannelRepository(session)
                if not await channel_repo.is_channel_enabled(message.guild.id, message.channel.id):
                    print(f"[MESSAGE] Channel {message.channel.id} not enabled for TTS", flush=True)
                    return
        except Exception as e:
            print(f"[ERROR] Failed to check channel registration: {e}")
            return

        # 봇이 음성 채널에 연결되어 있지 않으면 기본 음성 채널에 자동 입장
        if not message.guild.voice_client:
            try:
                async with get_async_session_context() as session:
                    settings_repo = GuildSettingsRepository(session)
                    default_voice_channel_id = await settings_repo.get_default_voice_channel(message.guild.id)

                    if not default_voice_channel_id:
                        print(f"[VOICE] No default voice channel set for guild {message.guild.id}", flush=True)
                        return

                    # Get voice channel
                    voice_channel = message.guild.get_channel(default_voice_channel_id)
                    if not voice_channel:
                        print(f"[VOICE] Default voice channel {default_voice_channel_id} not found", flush=True)
                        return

                    # Join the voice channel (same as !join command)
                    print(f"[VOICE] Auto-joining voice channel {voice_channel.name}", flush=True)
                    await voice_channel.connect(reconnect=True, timeout=60.0)
                    print(f"[VOICE] Successfully joined {voice_channel.name}", flush=True)

                    # Wait for voice client to be fully ready
                    max_wait = 5  # 최대 5초 대기
                    for i in range(max_wait * 10):  # 0.1초씩 체크
                        if message.guild.voice_client and message.guild.voice_client.is_connected():
                            print(f"[VOICE] Voice client is ready after {i * 0.1:.1f}s", flush=True)
                            break
                        await asyncio.sleep(0.1)
                    else:
                        print(f"[ERROR] Voice client not ready after {max_wait}s wait", flush=True)
                        return
            except Exception as e:
                print(f"[ERROR] Failed to auto-join voice channel: {e}")
                import traceback
                traceback.print_exc()
                return

        # Verify voice client is connected
        if not message.guild.voice_client or not message.guild.voice_client.is_connected():
            print(f"[ERROR] Voice client not connected, skipping TTS", flush=True)
            return

        # Get or create user settings
        try:
            async with get_async_session_context() as session:
                user_repository = UserRepository(session)
                user = await user_repository.get_or_create_user(
                    discord_id=message.author.id,
                    guild_id=message.guild.id,
                    username=str(message.author)
                )

                print(f"[DEBUG] User retrieved: id={user.id}, discord_id={user.discord_id}, rate={user.rate}, pitch={user.pitch}")

                # Publish message with user's voice settings
                self.publisher.publish(
                    exchange_name=self.PUBLISH_EXCHANGE,
                    routing_key=self.PUBLISH_ROUTING_KEY,
                    message={
                        "text": message.content,
                        "guild_id": message.guild.id,
                        "rate": user.rate,
                        "pitch": user.pitch,
                    },
                )
        except Exception as e:
            print(f"[ERROR] Failed to process message: {e}")
            import traceback
            traceback.print_exc()

    def _start_consumer_thread(self) -> None:
        self._consumer_thread = threading.Thread(target=self._consume_messages, daemon=True)
        self._consumer_thread.start()

    def _consume_messages(self) -> None:
        self.consumer.consume(
            queue_name=self.CONSUME_QUEUE,
            handler=self._handle_tts_response,
            exchange_name=self.CONSUME_EXCHANGE,
            routing_key=self.CONSUME_ROUTING_KEY,
        )
        self.consumer.start_consuming()

    def _handle_tts_response(self, message: dict[str, Any]) -> None:
        object_name = message.get("object_name")
        guild_id = message.get("guild_id")

        if not object_name or not guild_id:
            return

        guild_id = int(guild_id)
        audio_data = self.minio.download_bytes(object_name)

        self.bot.loop.call_soon_threadsafe(
            lambda gid=guild_id, data=audio_data: self.bot.loop.create_task(
                self._enqueue_audio(gid, data)
            )
        )

    async def _enqueue_audio(self, guild_id: int, audio_data: bytes) -> None:
        if guild_id not in self._audio_queues:
            self._audio_queues[guild_id] = asyncio.Queue()

        await self._audio_queues[guild_id].put(audio_data)
        queue_size = self._audio_queues[guild_id].qsize()
        print(f"[AUDIO] Enqueued audio for guild {guild_id}, queue size: {queue_size}", flush=True)

        # 플레이어 태스크가 없거나 완료되었으면 새로 시작
        if guild_id not in self._player_tasks or self._player_tasks[guild_id].done():
            print(f"[AUDIO] Starting new player loop for guild {guild_id}", flush=True)
            self._player_tasks[guild_id] = self.bot.loop.create_task(self._player_loop(guild_id))
        else:
            print(f"[AUDIO] Player loop already running for guild {guild_id}", flush=True)

    async def _player_loop(self, guild_id: int) -> None:
        queue = self._audio_queues[guild_id]

        while True:
            try:
                # Wait for audio with timeout to check if we should stop
                audio_data = await asyncio.wait_for(queue.get(), timeout=0.1)
                await self._play_audio(guild_id, audio_data)
            except asyncio.TimeoutError:
                # Check if queue is empty and voice client is still connected
                if queue.empty():
                    guild = self.bot.get_guild(guild_id)
                    if not guild or not guild.voice_client:
                        break
                    # Queue is empty, exit loop
                    break

    async def _play_audio(self, guild_id: int, audio_data: bytes) -> None:
        guild = self.bot.get_guild(guild_id)
        if not guild:
            print(f"[AUDIO] Guild {guild_id} not found", flush=True)
            return

        voice_client = guild.voice_client
        if not voice_client:
            print(f"[AUDIO] Voice client not found for guild {guild_id}", flush=True)
            return

        print(f"[AUDIO] Playing audio for guild {guild_id}, size: {len(audio_data)} bytes", flush=True)

        audio_source = None
        try:
            audio_source = discord.FFmpegPCMAudio(BytesIO(audio_data), pipe=True)

            play_finished = asyncio.Event()

            def after_play(error: Exception | None) -> None:
                if error:
                    print(f"[AUDIO] Play error: {error}", flush=True)
                else:
                    print(f"[AUDIO] Finished playing audio for guild {guild_id}", flush=True)
                self.bot.loop.call_soon_threadsafe(play_finished.set)

            voice_client.play(audio_source, after=after_play)

            await play_finished.wait()
        finally:
            # Cleanup audio source to prevent flush error
            if audio_source:
                try:
                    audio_source.cleanup()
                except Exception:
                    pass  # Ignore cleanup errors


async def setup(bot: "TTSBot") -> None:
    await bot.add_cog(TTSCog(bot))
