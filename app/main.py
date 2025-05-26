import os
from fastapi import FastAPI
from config import RABBITMQ_URI

# from app.service.rabbitmq_client import RabbitMQClient
# from app.service.vectorizer_client import VectorizerClient
# from app.service.elasticsearch_client import ElasticSearchClient
# from app.service.text_data_client import TextDataClient
# from app.service.prompt_service import PromptService
from app.core.prompt_builder import PromptBuilder
from app.service import (
    PromptService,
    TextDataClient,
    RabbitMQClient,
    VectorizerClient,
    ElasticSearchClient,
)
from app.schemas import GeneratePromptRequest, GeneratePromptResponse
import logging
import json
import config
from uuid import UUID

logger = logging.getLogger("PromptGeneratorService")
app = FastAPI(title="Prompt Generator Service", debug=True)

# --- Инициализация компонентов ---
rabbitmq = RabbitMQClient(url=RABBITMQ_URI)
vectorizer = VectorizerClient(rabbitmq)
es_client = ElasticSearchClient()
text_client = TextDataClient()
prompt_builder = PromptBuilder()
prompt_service = PromptService(
    vectorizer, es_client, text_client, prompt_builder
)


# --- Callback для RabbitMQ ---
async def on_embedding_message(message):
    data = json.loads(message.body.decode())
    logger.info(f"[+] Получен вектор для {data['request_id']}")
    prompt_service.handle_embedding_response(data)


# --- FastAPI маршруты ---
@app.post("/generate_prompt")
async def generate_prompt_route(request: GeneratePromptRequest):
    request_id = request.request_id or str(UUID(int=os.urandom(16).hex))
    user_question = request.question

    if not user_question:
        return {"error": "Нет вопроса"}

    prompt = await prompt_service.generate_prompt(request_id, user_question)
    return {"prompt": prompt, "request_id": request_id}


# --- Запуск сервиса ---
async def start_rabbitmq_listener():
    await rabbitmq.connect()
    rabbitmq.register_handler(config.EMBEDDINGS_QUEUE, on_embedding_message)
    await rabbitmq.start_consumers()


def run_app():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)


if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.create_task(start_rabbitmq_listener())
    loop.run_until_complete(run_app())
