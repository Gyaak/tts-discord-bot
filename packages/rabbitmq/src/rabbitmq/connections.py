import pika
from pika import BlockingConnection
from pika.adapters.blocking_connection import BlockingChannel

from .settings import RabbitMQSettings


class RabbitMQConnection:
    def __init__(self, settings: RabbitMQSettings | None = None):
        self.settings = settings or RabbitMQSettings()
        self._connection: BlockingConnection | None = None

    def _get_credentials(self) -> pika.PlainCredentials:
        return pika.PlainCredentials(
            username=self.settings.username,
            password=self.settings.password,
        )

    def _get_parameters(self) -> pika.ConnectionParameters:
        return pika.ConnectionParameters(
            host=self.settings.host,
            port=self.settings.port,
            virtual_host=self.settings.vhost,
            credentials=self._get_credentials(),
            heartbeat=600,  # 10분마다 heartbeat
            blocked_connection_timeout=300,  # 5분 block timeout
        )

    def ensure_connection(self) -> BlockingConnection:
        if self._connection is None or self._connection.is_closed:
            self._connection = pika.BlockingConnection(self._get_parameters())
        return self._connection

    def create_channel(self) -> BlockingChannel:
        connection = self.ensure_connection()
        return connection.channel()

    def close(self) -> None:
        if self._connection and self._connection.is_open:
            self._connection.close()
        self._connection = None


_default_connection: RabbitMQConnection | None = None


def get_rabbitmq_connection(settings: RabbitMQSettings | None = None) -> RabbitMQConnection:
    global _default_connection
    if _default_connection is None:
        _default_connection = RabbitMQConnection(settings)
    return _default_connection
