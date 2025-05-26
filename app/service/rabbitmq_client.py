import aio_pika
import json
import asyncio
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from config import CHUNKS_SENT, CHUNK_ERRORS, CURRENT_CHUNKS

logger = logging.getLogger("RabbitMQClient")
__all__ = ["RabbitMQClient"]


class RabbitMQClient:
    def __init__(self, url: str):
        self.connection = None
        self.channel = None
        self.handlers = {}
        self._is_connecting = False
        self.exchanges = {}
        self.url = url

    @retry(
        stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, max=10)
    )
    async def connect(self):
        if self._is_connecting:
            return
        self._is_connecting = True
        try:
            self.connection = await aio_pika.connect_robust(self.url, timeout=10)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)
            print("[x] Connected to RabbitMQ")
        finally:
            self._is_connecting = False

    async def close(self):
        if self.connection:
            await self.connection.close()

    def register_handler(self, queue_name: str, handler: callable):
        self.handlers[queue_name] = handler

    async def declare_exchange(
        self,
        exchange_name: str,
        type: aio_pika.ExchangeType = aio_pika.ExchangeType.DIRECT,
    ):
        """Создает exchange, если его нет"""
        if not self.connection or self.connection.is_closed:
            await self.connect()
        
        if exchange_name in self.exchanges:
            return self.exchanges[exchange_name]

        exchange = await self.channel.declare_exchange(
            exchange_name, type, durable=True
        )
        self.exchanges[exchange_name] = exchange
        logger.info(f"[x] Declared exchange '{exchange_name}'")
        return exchange

    async def declare_queue(self, queue_name: str, durable: bool = True):
        """Создает очередь, если её нет"""
        if not self.connection or self.connection.is_closed:
            await self.connect()
        
        queue = await self.channel.declare_queue(queue_name, durable=durable)
        logger.info(f"[x] Declared queue '{queue_name}'")
        return queue

    async def consume(self, queue_name: str):
        if not self.connection or self.connection.is_closed:
            await self.connect()

        try:
            queue = await self.channel.get_queue(queue_name)
        except Exception:
            queue = await self.declare_queue(queue_name)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    if queue_name in self.handlers:
                        await self.handlers[queue_name](message)
                    else:
                        logger.error(f"[!] No handler for queue {queue_name}")

    async def publish(self, queue_name: str, message: dict):
        if not self.connection or self.connection.is_closed:
            await self.connect()

        try:
            CURRENT_CHUNKS.inc()
            message_json = json.dumps(message, ensure_ascii=False)
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=message_json.encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=queue_name,
            )
            CHUNKS_SENT.inc()
            logger.info(f"[x] Sent message to {queue_name}")
        except Exception as e:
            CHUNK_ERRORS.inc()
            logger.error(f"[!] Error sending message: {e}")
        finally:
            CURRENT_CHUNKS.dec()

    async def start_consumers(self):
        for queue_name in self.handlers.keys():
            asyncio.create_task(self.consume(queue_name))
