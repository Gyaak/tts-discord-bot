import json
from typing import Any

import pika
from pika.adapters.blocking_connection import BlockingChannel

from .connections import RabbitMQConnection, get_rabbitmq_connection


class RabbitMQPublisher:
    def __init__(self, connection: RabbitMQConnection | None = None):
        self.connection = connection or get_rabbitmq_connection()
        self._channel: BlockingChannel | None = None

    def _get_channel(self, force_new: bool = False) -> BlockingChannel:
        # force_new가 True이거나 채널이 없거나 닫혀있으면 새로 생성
        if force_new or self._channel is None or self._channel.is_closed:
            try:
                # 기존 채널 정리
                if self._channel and self._channel.is_open:
                    self._channel.close()
            except Exception:
                pass

            # 연결 확인 및 새 채널 생성
            self.connection.ensure_connection()
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
        if isinstance(message, dict):
            body = json.dumps(message).encode()
        elif isinstance(message, str):
            body = message.encode()
        else:
            body = message

        properties = pika.BasicProperties(
            delivery_mode=pika.DeliveryMode.Persistent if persistent else pika.DeliveryMode.Transient,
        )

        # First attempt with existing channel
        try:
            channel = self._get_channel()

            channel.exchange_declare(
                exchange=exchange_name,
                exchange_type=exchange_type,
                durable=True,
            )

            channel.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=body,
                properties=properties,
            )
        except (pika.exceptions.StreamLostError, pika.exceptions.AMQPConnectionError,
                pika.exceptions.ChannelWrongStateError, BrokenPipeError) as e:
            # Connection lost, create new connection and retry once
            print(f"[RABBITMQ] Connection lost: {e}, creating new connection...")

            # Force close old connection
            try:
                self.close()
                self.connection.close()
            except Exception:
                pass

            # Get fresh channel (will create new connection)
            channel = self._get_channel(force_new=True)

            channel.exchange_declare(
                exchange=exchange_name,
                exchange_type=exchange_type,
                durable=True,
            )

            channel.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=body,
                properties=properties,
            )
            print(f"[RABBITMQ] Reconnection successful")

    def close(self) -> None:
        if self._channel and self._channel.is_open:
            self._channel.close()
        self._channel = None
