import uuid
from typing import Any

from minio import MinIOClient, MinIOSettings
from rabbitmq import RabbitMQConnection, RabbitMQConsumer, RabbitMQPublisher, RabbitMQSettings

from .polly import PollyClient
from .settings import PollySettings


class TTSWorker:
    CONSUME_EXCHANGE = "tts"
    CONSUME_QUEUE = "tts.worker"
    CONSUME_ROUTING_KEY = "tts.worker"
    PUBLISH_EXCHANGE = "tts"
    PUBLISH_ROUTING_KEY = "tts.bot"

    def __init__(
        self,
        polly_settings: PollySettings | None = None,
        minio_settings: MinIOSettings | None = None,
        rabbitmq_settings: RabbitMQSettings | None = None,
    ):
        self.polly = PollyClient(polly_settings)
        self.minio = MinIOClient(minio_settings)

        self.rabbitmq_conn = RabbitMQConnection(rabbitmq_settings)
        self.consumer = RabbitMQConsumer(self.rabbitmq_conn)
        self.publisher = RabbitMQPublisher(self.rabbitmq_conn)

    def _handle_message(self, message: dict[str, Any]) -> None:
        text = message.get("text", "")
        guild_id = message.get("guild_id")

        if not text:
            return

        audio_data = self.polly.synthesize(text)

        object_name = f"{uuid.uuid4()}.mp3"
        self.minio.upload_bytes(object_name, audio_data, content_type="audio/mpeg")

        self.publisher.publish(
            exchange_name=self.PUBLISH_EXCHANGE,
            routing_key=self.PUBLISH_ROUTING_KEY,
            message={
                "object_name": object_name,
                "guild_id": guild_id,
            },
        )

    def run(self) -> None:
        self.consumer.consume(
            queue_name=self.CONSUME_QUEUE,
            handler=self._handle_message,
            exchange_name=self.CONSUME_EXCHANGE,
            routing_key=self.CONSUME_ROUTING_KEY,
        )
        self.consumer.start_consuming()

    def stop(self) -> None:
        self.consumer.close()
        self.publisher.close()
        self.rabbitmq_conn.close()
