from typing import Dict, Any

from config import VECTORIZE_QUEUE
from app.service.rabbitmq_client import RabbitMQClient
from app.schemas import VectorizeRequestSchema


__all__ = ["VectorizerClient"]


class VectorizerClient:
    def __init__(self, rabbitmq: RabbitMQClient):
        self.rabbitmq = rabbitmq

    async def request_vector(
        self,
        message_id: str,
        text: str,
        callback_queue: str,
        metadata: Dict[str, Any] | None,
    ):
        message = VectorizeRequestSchema(
            message_id=message_id,
            text=text,
            callback_queue=callback_queue,
            metadata=metadata,
        ).model_json_schema()
        await self.rabbitmq.publish(VECTORIZE_QUEUE, message)
        return message_id
