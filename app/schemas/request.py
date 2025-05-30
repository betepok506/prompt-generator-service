from pydantic import BaseModel
from typing import Optional, Dict, Any

__all__ = ["VectorizeRequestSchema"]


class VectorizeRequestSchema(BaseModel):
    """Схема данных, описывающая формат сообщений, отправляемых микросервису векторизации"""

    message_id: str
    text: str
    callback_queue: str
    metadata: Dict[str, Any] | None = {}

    class Config:
        extra = "forbid"  # Запрет лишних полей
        json_schema_extra = {
            "example": {
                "text": "Пример текста",
                "message_id": "550e8400-e29b-41d4-a716-446655440000",
                "callback_queue": "prompt_generator_embeddings",
                "metadata": {"source": "web"},
            }
        }
