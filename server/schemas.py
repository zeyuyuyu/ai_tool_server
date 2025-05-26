from pydantic import BaseModel
from typing import List, Dict, Any

class Message(BaseModel):
    role: str
    content: str | None = None
    name: str | None = None
    tool_call_id: str | None = None

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    stream: bool | None = False
    temperature: float | None = 0.7
    max_tokens: int | None = 1024
    tools: List[Dict[str, Any]] | None = None
