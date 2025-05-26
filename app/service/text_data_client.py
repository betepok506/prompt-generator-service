import httpx
from config import TEXT_DATA_API

__all__ = [
    "TextDataClient"
]

class TextDataClient:
    def __init__(self, api_url=None):
        self.api_url = api_url or TEXT_DATA_API

    async def get_texts_by_ids(self, elastic_ids: list[str]):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/elastic_ids/", json=elastic_ids
            )
            return response.json()["data"]["items"]
