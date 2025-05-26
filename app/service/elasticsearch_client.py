import httpx
from config import ELASTICSEARCH_API

__all__ = ["ElasticSearchClient"]


class ElasticSearchClient:
    def __init__(self, api_url=None):
        self.api_url = api_url or ELASTICSEARCH_API

    async def search_neighbors(self, vector: list[float], k: int = 3):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/search_neighbors",
                json={"vector": vector, "k": k},
            )
            return response.json()["data"]["items"]
