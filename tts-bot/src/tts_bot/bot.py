import discord
from discord.ext import commands
from minio import MinIOClient, MinIOSettings
from rabbitmq import RabbitMQConnection, RabbitMQConsumer, RabbitMQPublisher, RabbitMQSettings

from .settings import BotSettings

COGS = [
    "tts_bot.cogs.voice",
    "tts_bot.cogs.tts",
]


class TTSBot(commands.Bot):
    def __init__(
        self,
        bot_settings: BotSettings | None = None,
        minio_settings: MinIOSettings | None = None,
        rabbitmq_settings: RabbitMQSettings | None = None,
    ):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True

        super().__init__(command_prefix="!", intents=intents)

        self.bot_settings = bot_settings or BotSettings()
        self.minio = MinIOClient(minio_settings)

        # publisher와 consumer는 별도 connection 사용 (pika는 thread-safe하지 않음)
        self._publisher_conn = RabbitMQConnection(rabbitmq_settings)
        self._consumer_conn = RabbitMQConnection(rabbitmq_settings)
        self.publisher = RabbitMQPublisher(self._publisher_conn)
        self.consumer = RabbitMQConsumer(self._consumer_conn)

    async def setup_hook(self) -> None:
        for cog in COGS:
            await self.load_extension(cog)

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user}")

    def run_bot(self) -> None:
        self.run(self.bot_settings.token)

    async def close(self) -> None:
        self.consumer.close()
        self.publisher.close()
        self._consumer_conn.close()
        self._publisher_conn.close()
        await super().close()
