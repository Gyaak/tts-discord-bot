import json
from typing import Any

import pika
from pika.adapters.blocking_connection import BlockingChannel

from .connections import RabbitMQConnection, get_rabbitmq_connection


class RabbitMQPublisher:
    def __init__(self, connection: RabbitMQConnection | None = None):
        self.connection = connection or get_rabbitmq_connection()
        self._channel: BlockingChannel | None = None

    def _get_channel(self) -> BlockingChannel:
        # 타임아웃 방지용 연결 확인 코드
        self.connection.ensure_connection()
        if self._channel is None or self._channel.is_closed:
            self._channel = self.connection.create_channel()
        return self._channel

    def publish(
        self,
        exchange_name: str,
        routing_key: str,
        message: dict[str, Any] | str | bytes,
        exchange_type: str = "direct",
        persistent: bool = True,
    ) -> None:
        channel = self._get_channel()

        channel.exchange_declare(
            exchange=exchange_name,
            exchange_type=exchange_type,
            durable=True,
        )

        if isinstance(message, dict):
            body = json.dumps(message).encode()
        elif isinstance(message, str):
            body = message.encode()
        else:
            body = message

        properties = pika.BasicProperties(
            delivery_mode=pika.DeliveryMode.Persistent if persistent else pika.DeliveryMode.Transient,
        )

        channel.basic_publish(
            exchange=exchange_name,
            routing_key=routing_key,
            body=body,
            properties=properties,
        )

    def close(self) -> None:
        if self._channel and self._channel.is_open:
            self._channel.close()
        self._channel = None
