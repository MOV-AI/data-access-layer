import os

from redis import asyncio as redis

from dal.new_models.base_model.redis_config import RedisConfig

URL = os.environ.get("REDIS_URL", RedisConfig().redis_url)


def get_redis_connection(**kwargs) -> redis.Redis:
    """return an Asyncio based redis connection

    kwargs:
        decode_responses (bool): decode responses from redis
        url: a redis url to connect to

    Returns:
        redis.Redis: a redis client object.
    """
    # Decode from UTF-8 by default
    if "decode_responses" not in kwargs:
        kwargs["decode_responses"] = True

    url = kwargs.pop("url", URL)
    if url:
        return redis.Redis.from_url(url, **kwargs)

    return redis.Redis(**kwargs)
