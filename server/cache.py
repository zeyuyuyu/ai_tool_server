"""
简单 Redis 缓存工具（仅用于 Claude prompt cache）
环境变量：
    REDIS_HOST   (默认 localhost)
    REDIS_PORT   (默认 6379)
"""

import os
import redis
import orjson

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=False,  # 原样 bytes，交给 orjson
)


def get(key: str):
    val = r.get(key)
    return orjson.loads(val) if val else None


def set(key: str, value, ttl: int = 1800):
    r.setex(key, ttl, orjson.dumps(value))
