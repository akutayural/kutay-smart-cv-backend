from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=1000)


class Source(BaseModel):
    title: str
    content_preview: str


class ChatResponse(BaseModel):
    answer: str
    refused: bool = False
    sources: list[Source] = []
