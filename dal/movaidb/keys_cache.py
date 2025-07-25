"""
This module provides functionality for managing a Redis-based indexed cache. It includes utilities for indexing Redis keys
based on their prefixes and types, as well as retrieving and managing these keys efficiently.
"""

from enum import Enum
from typing import Iterable, NamedTuple, Optional, Union

from movai_core_shared import Log
import redis

LOGGER = Log.get_logger("dal.mov.ai")


class RedisType(Enum):
    """Enum representing the different Redis data types (STRING, HASH, LIST, SET, ZSET)"""

    STRING = "string"
    HASH = "hash"
    LIST = "list"
    SET = "set"
    ZSET = "zset"


KeyInfo = NamedTuple(
    "KeyInfo",
    [
        ("key", str),
        ("type", RedisType),
    ],
)


class RedisIndexedCache:
    """A class for managing an indexed cache in Redis. It provides methods for adding,
    removing, and retrieving keys based on their prefixes and types."""

    def __init__(self, redis_client: redis.Redis, index_prefix: str = "__index__"):
        self._redis: redis.Redis = redis_client
        self.index_prefix = index_prefix

    def _get_index_key(self, prefix: str) -> str:
        return f"{self.index_prefix}:{prefix}"

    def _get_prefix(self, key: str) -> str:
        parts = key.split(",")
        for part in parts:
            if ":" in part:
                return part  # e.g., Flow:abc
        return "misc"

    def add_to_index(self, key: str, redis_type: Optional[RedisType] = None):
        if redis_type is None:
            redis_type = RedisType(self._redis.type(key))
        prefix = self._get_prefix(key)
        index_key = self._get_index_key(prefix)
        entry = f"{key}|{redis_type.value}"
        self._redis.sadd(index_key, entry)

    def remove_from_index(self, key: str):
        prefix = self._get_prefix(key)
        index_key = self._get_index_key(prefix)
        entries = self._redis.smembers(index_key)
        for entry in entries:
            if entry.decode().startswith(f"{key}|"):
                self._redis.srem(index_key, entry)
                break

    def _fetch_by_type(self, key: str, key_type: str) -> Optional[Union[str, dict, list, set]]:
        if key_type == "string":
            return self._redis.get(key)
        if key_type == "hash":
            return self._redis.hgetall(key)
        if key_type == "list":
            return self._redis.lrange(key, 0, -1)
        if key_type == "set":
            return self._redis.smembers(key)
        if key_type == "zset":
            return self._redis.zrange(key, 0, -1, withscores=True)
        return None

    def get_keys_by_prefix(self, prefix: str) -> Iterable[KeyInfo]:
        index_key = self._get_index_key(prefix)
        entries = self._redis.smembers(index_key)
        results = set()
        for entry in entries:
            try:
                key, key_type = entry.decode().rsplit("|", 1)
                results.add(KeyInfo(key=key, type=RedisType(key_type)))
            except ValueError:
                LOGGER.warning(f"Invalid entry format in index: {entry}")
        return results

    def initialize_keys_cache(self):
        """Initialize the keys cache by scanning all keys in Redis and adding them to the index."""
        cursor = 0
        added_keys = 0
        while True:
            cursor, keys = self._redis.scan(cursor=cursor, match="*", count=1000)
            for key in keys:
                key = key.decode() if isinstance(key, bytes) else key
                try:
                    key_type = RedisType(self._redis.type(key).decode())
                    self.add_to_index(key, key_type)
                except redis.RedisError as error:
                    LOGGER.error(f"Error adding key {key} to index: {error}")
            added_keys += len(keys)
            if cursor == 0:
                break
        LOGGER.info("Keys cache initialized successfully. %s keys indexed.", added_keys)
