import openai, anthropic
from typing import List, Dict, Any
from config import get_settings

settings = get_settings()
openai.api_key = settings.OPENAI_API_KEY
anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

async def chat_completion(model: str,
                          messages: List[Dict[str, Any]],
                          tools: List[Dict[str, Any]],
                          stream: bool = False,
                          **kwargs):
    if model.startswith("claude"):
        headers = {"anthropic-beta": "token-efficient-tools-2025-02-19"}
        resp = anthropic_client.messages.create(
            model=model,
            max_tokens=kwargs.get("max_tokens", 1024),
            messages=messages,
            tools=tools,
            stream=stream,
            extra_headers=headers
        )
        return resp
    else:
        param = dict(model=model, messages=messages, tools=tools,
                     stream=stream, **kwargs)
        resp = openai.ChatCompletion.acreate(**param) if stream else openai.ChatCompletion.create(**param)
        return resp
