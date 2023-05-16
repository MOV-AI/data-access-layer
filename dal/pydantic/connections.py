import os
from redis import asyncio as redis

URL = os.environ.get("REDIS_URL", None)


def get_redis_connection(**kwargs) -> redis.Redis:
    # Decode from UTF-8 by default
    if "decode_responses" not in kwargs:
        kwargs["decode_responses"] = True

    url = kwargs.pop("url", URL)
    if url:
        return redis.Redis.from_url(url, **kwargs)

    return redis.Redis(**kwargs)
