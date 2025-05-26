from typing import Dict, List, Optional
from uuid import UUID
import asyncio

from config import PROMPTS_GENERATED, PROMPT_ERRORS, EMBEDDINGS_QUEUE
from app.core.prompt_builder import PromptBuilder
from app.service.vectorizer_client import VectorizerClient
from app.service.elasticsearch_client import ElasticSearchClient
from app.service.text_data_client import TextDataClient
import logging

logger = logging.getLogger("PromptService")

__all__ = [
    "PromptService"
]

class PromptService:
    def __init__(
        self,
        vectorizer: VectorizerClient,
        es_client: ElasticSearchClient,
        text_client: TextDataClient,
        prompt_builder: PromptBuilder,
    ):
        self.vectorizer = vectorizer
        self.es_client = es_client
        self.text_client = text_client
        self.prompt_builder = prompt_builder
        self.pending_requests = {}  # {request_id: future}

    async def generate_prompt(self, request_id: str, question: str) -> str:
        """Создание промпта"""
        logger.info(f"[?] Обработка запроса {request_id[:8]}...")

        # Шаг 1: Запрос на векторизацию
        await self.vectorizer.request_vector(message_id=request_id, 
                                             text=question,
                                             callback_queue=EMBEDDINGS_QUEUE,
                                             metadata=None)

        # Шаг 2: Ожидание эмбеддинга
        embedding = await self.wait_for_embedding(request_id)
        if not embedding:
            raise TimeoutError("Не удалось получить вектор")

        # Шаг 3: Поиск ближайших документов
        neighbors = await self.es_client.search_neighbors(embedding["embedding"])
        elastic_ids = [item["doc_id"] for item in neighbors]

        # Шаг 4: Получение текстов
        texts = await self.text_client.get_texts_by_ids(elastic_ids)

        # Шаг 5: Формирование промпта
        context = [t["text"] for t in texts]
        prompt = self.prompt_builder.build_prompt(context, user_question)

        PROMPTS_GENERATED.inc()
        logger.info(f"[$] Промпт готов для {request_id[:8]}...")
        return prompt

    async def wait_for_embedding(
        self, request_id: str, timeout: int = 10
    ) -> Optional[Dict]:
        """Ожидание результата от Embedding Service"""
        future = asyncio.get_event_loop().create_future()
        self.pending_requests[request_id] = future

        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            logger.error(f"[X] Таймаут ожидания вектора для {request_id[:8]}")
            PROMPT_ERRORS.inc()
            return None

    def handle_embedding_response(self, data: dict):
        """Callback от RabbitMQ при получении вектора"""
        request_id = data.get("request_id")
        embedding = data.get("embedding")

        if request_id and request_id in self.pending_requests:
            future = self.pending_requests.pop(request_id)
            future.set_result({"request_id": request_id, "embedding": embedding})
