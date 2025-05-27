"""
model_client.py — OpenAI / Anthropic 封装
✓ 兼容 openai>=1.18 v1 客户端
✓ 新增 Claude prompt 缓存（Redis）
"""

import hashlib
from typing import List, Dict, Any, AsyncGenerator, Union

import openai
import anthropic
import orjson

from config import get_settings
from cache import get as cache_get, set as cache_set  

settings = get_settings()

# OpenAI clients
sync_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY, timeout=60)
async_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY, timeout=60)

# Anthropic client
anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


async def chat_completion(
    model: str,
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    stream: bool = False,
    **kwargs,
) -> Union[openai.types.chat.ChatCompletion, AsyncGenerator]:
    # ---------- Anthropic Claude ------------------------------------------
    if model.startswith("claude"):
        # —— Prompt cache key：对最近 6 条消息做 md5 —— #
        key_source = (model, messages[-6:])
        key = "claude:" + hashlib.md5(orjson.dumps(key_source)).hexdigest()

        if not stream:
            if (cached := cache_get(key)):
                return cached  #  命中缓存直接返回

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

        #  非流式：写入缓存并返回
        cache_set(key, resp.model_dump(mode="python"))
        return resp

    # ---------- OpenAI -----------------------------------------------------
    param = dict(model=model, messages=messages, tools=tools, **kwargs)
    if stream:
        async def agen() -> AsyncGenerator:
            async for chunk in async_client.chat.completions.create(stream=True, **param):
                yield chunk
        return agen()

    return sync_client.chat.completions.create(**param)
