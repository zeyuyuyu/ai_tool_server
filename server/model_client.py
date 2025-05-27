"""
统一封装 OpenAI / Anthropic Chat Completion 调用
✓ 兼容 openai>=1.18 的新客户端
✓ stream=True 时返回异步生成器，yield 原生 chunk 对象
✓ 非流式返回原生 ChatCompletion 对象（保持 tool_calls 为对象）
"""

from typing import List, Dict, Any, AsyncGenerator, Union
import openai
import anthropic
from config import get_settings

settings = get_settings()

# -- OpenAI v1 client --------------------------------------------------------
sync_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY, timeout=60)
async_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY, timeout=60)

# -- Anthropic client --------------------------------------------------------
anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


async def chat_completion(
    model: str,
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    stream: bool = False,
    **kwargs,
) -> Union[openai.types.chat.ChatCompletion, AsyncGenerator]:
    # ---------- Claude ------------------------------------------------------
    if model.startswith("claude"):
        headers = {"anthropic-beta": "token-efficient-tools-2025-02-19"}
        resp = anthropic_client.messages.create(
            model=model,
            messages=messages,
            tools=tools,
            max_tokens=kwargs.get("max_tokens", 1024),
            stream=stream,
            extra_headers=headers,
        )
        if stream:
            async def agen() -> AsyncGenerator:
                async for chunk in resp:
                    yield chunk
            return agen()
        return resp

    # ---------- OpenAI ------------------------------------------------------
    param = dict(model=model, messages=messages, tools=tools, **kwargs)

    if stream:
        async def agen() -> AsyncGenerator:
            async for chunk in async_client.chat.completions.create(stream=True, **param):
                yield chunk
        return agen()
    else:
        return sync_client.chat.completions.create(**param)
