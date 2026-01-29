import asyncio
import threading
from io import BytesIO
from typing import Any, TYPE_CHECKING

import discord
from discord.ext import commands
from minio import MinIOClient
from rabbitmq import RabbitMQConsumer, RabbitMQPublisher

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

        # 봇이 음성 채널에 연결되어 있는지 확인
        if not message.guild.voice_client:
            return

        self.publisher.publish(
            exchange_name=self.PUBLISH_EXCHANGE,
            routing_key=self.PUBLISH_ROUTING_KEY,
            message={
                "text": message.content,
                "guild_id": message.guild.id,
            },
        )

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

        # 플레이어 태스크가 없거나 완료되었으면 새로 시작
        if guild_id not in self._player_tasks or self._player_tasks[guild_id].done():
            self._player_tasks[guild_id] = self.bot.loop.create_task(self._player_loop(guild_id))

    async def _player_loop(self, guild_id: int) -> None:
        queue = self._audio_queues[guild_id]

        while not queue.empty():
            audio_data = await queue.get()
            await self._play_audio(guild_id, audio_data)

    async def _play_audio(self, guild_id: int, audio_data: bytes) -> None:
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        voice_client = guild.voice_client
        if not voice_client:
            return
        audio_source = discord.FFmpegPCMAudio(BytesIO(audio_data), pipe=True)

        play_finished = asyncio.Event()

        def after_play(error: Exception | None) -> None:
            self.bot.loop.call_soon_threadsafe(play_finished.set)

        voice_client.play(audio_source, after=after_play)

        await play_finished.wait()


async def setup(bot: "TTSBot") -> None:
    await bot.add_cog(TTSCog(bot))
