import os
from prometheus_client import Counter, Gauge

# Конфиг
RABBITMQ_URI = os.getenv("RABBITMQ_URI", "amqp://guest:guest@rabbitmq/")
VECTORIZE_QUEUE = "vectorize_queue"
EMBEDDINGS_QUEUE = "prompt_generator_embeddings"

ELASTICSEARCH_API = os.getenv("ELASTICSEARCH_API", "http://elasticsearch:8000")
TEXT_DATA_API = os.getenv("TEXT_DATA_API", "http://textdata:8000")

# Метрики
CHUNKS_SENT = Counter('chunks_sent_total', 'Total chunks sent')
CHUNK_ERRORS = Counter('chunk_errors_total', 'Total chunk errors')
CURRENT_CHUNKS = Gauge('current_chunks_in_progress', 'Chunks currently being processed')
PROMPTS_GENERATED = Counter('prompts_generated_total', 'Total prompts generated')
PROMPT_ERRORS = Counter('prompt_errors_total', 'Total prompt errors')
CURRENT_PROMPTS = Gauge('current_prompts_in_progress', 'Prompts currently being processed')