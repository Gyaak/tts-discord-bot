import time
import uuid
from typing import Any

from minio import MinIOClient, MinIOSettings
from rabbitmq import RabbitMQConnection, RabbitMQConsumer, RabbitMQPublisher, RabbitMQSettings
import pika.exceptions

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
        rate = message.get("rate", 100)  # Default: 100%
        pitch = message.get("pitch", 0)  # Default: 0 (normal)

        if not text:
            return

        audio_data = self.polly.synthesize(text, rate=rate, pitch=pitch)

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
        """Run worker with automatic reconnection on connection loss."""
        retry_delay = 5  # seconds

        while True:
            try:
                print("[INFO] Starting TTS worker...")
                self.consumer.consume(
                    queue_name=self.CONSUME_QUEUE,
                    handler=self._handle_message,
                    exchange_name=self.CONSUME_EXCHANGE,
                    routing_key=self.CONSUME_ROUTING_KEY,
                )
                print("[INFO] Worker connected. Waiting for messages...")
                self.consumer.start_consuming()
            except (pika.exceptions.StreamLostError, pika.exceptions.AMQPConnectionError,
                    pika.exceptions.ConnectionClosedByBroker, ConnectionResetError) as e:
                print(f"[ERROR] Connection lost: {e}")
                print(f"[INFO] Reconnecting in {retry_delay} seconds...")

                # Clean up old connection
                try:
                    self.consumer.close()
                    self.publisher.close()
                    self.rabbitmq_conn.close()
                except Exception:
                    pass

                # Wait before reconnecting
                time.sleep(retry_delay)

                # Create new connection
                self.rabbitmq_conn = RabbitMQConnection()
                self.consumer = RabbitMQConsumer(self.rabbitmq_conn)
                self.publisher = RabbitMQPublisher(self.rabbitmq_conn)
            except KeyboardInterrupt:
                print("[INFO] Shutting down worker...")
                break
            except Exception as e:
                print(f"[ERROR] Unexpected error: {e}")
                import traceback
                traceback.print_exc()
                print(f"[INFO] Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

    def stop(self) -> None:
        self.consumer.close()
        self.publisher.close()
        self.rabbitmq_conn.close()
