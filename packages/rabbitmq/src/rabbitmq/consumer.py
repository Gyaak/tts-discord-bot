import json
from typing import Any, Callable

from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from .connections import RabbitMQConnection, get_rabbitmq_connection


MessageHandler = Callable[[dict[str, Any] | bytes], None]


class RabbitMQConsumer:
    def __init__(self, connection: RabbitMQConnection | None = None):
        self.connection = connection or get_rabbitmq_connection()
        self._channel: BlockingChannel | None = None
        self._consumer_tags: list[str] = []

    def _get_channel(self) -> BlockingChannel:
        if self._channel is None or self._channel.is_closed:
            self._channel = self.connection.create_channel()
        return self._channel

    def consume(
        self,
        queue_name: str,
        handler: MessageHandler,
        prefetch_count: int = 1,
        auto_ack: bool = False,
        parse_json: bool = True,
    ) -> str:
        channel = self._get_channel()
        channel.basic_qos(prefetch_count=prefetch_count)

        channel.queue_declare(queue=queue_name, durable=True)

        def on_message(
            ch: BlockingChannel,
            method: Basic.Deliver,
            properties: BasicProperties,
            body: bytes,
        ) -> None:
            try:
                if parse_json:
                    data = json.loads(body.decode())
                else:
                    data = body
                handler(data)
                if not auto_ack:
                    ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception:
                if not auto_ack:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                raise

        consumer_tag = channel.basic_consume(
            queue=queue_name,
            on_message_callback=on_message,
            auto_ack=auto_ack,
        )
        self._consumer_tags.append(consumer_tag)
        return consumer_tag

    def start_consuming(self) -> None:
        channel = self._get_channel()
        channel.start_consuming()

    def stop(self) -> None:
        if self._channel and self._channel.is_open:
            for tag in self._consumer_tags:
                self._channel.basic_cancel(tag)
        self._consumer_tags.clear()

    def close(self) -> None:
        self.stop()
        if self._channel and self._channel.is_open:
            self._channel.close()
        self._channel = None
