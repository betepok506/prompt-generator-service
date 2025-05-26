from pydantic import BaseModel


class GeneratePromptRequest(BaseModel):
    request_id: str
    question: str


class GeneratePromptResponse(BaseModel):
    prompt: str
    status: str = "success"
