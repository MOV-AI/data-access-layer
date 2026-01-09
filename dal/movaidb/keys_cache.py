"""
This module provides functionality for managing a Redis-based indexed cache. It includes utilities for indexing Redis keys
based on their prefixes and types, as well as retrieving and managing these keys efficiently.
"""

import re
from enum import Enum
from typing import NamedTuple, Optional, Set, Union, List

import redis
from movai_core_shared import Log

LOGGER = Log.get_logger("dal.mov.ai.redis_indexed_cache")


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
    removing, and retrieving keys based on their prefixes and types.

    For key "Robot:2dd2cac0bb7b439f8cc923852a19a290,RobotName:" we'll store:
       - Add 'RobotName:' to set 'Robot:2dd2cac0bb7b439f8cc923852a19a290,'
       - Add '2dd2cac0bb7b439f8cc923852a19a290,' to set 'Robot:'

    When one searches for 'Robot:*,RobotName:' we'll:
       - Read items of 'Robot:', and we'll get '2dd2cac0bb7b439f8cc923852a19a290,'
       - Read items of 'Robot:2dd2cac0bb7b439f8cc923852a19a290,' and we'll get 'RobotName:'
       - return 'Robot:2dd2cac0bb7b439f8cc923852a19a290,RobotName:'
    """

    def __init__(self, redis_client: "redis.Redis", index_prefix: str = "__index__"):
        self._redis: "redis.Redis" = redis_client
        self.index_prefix = index_prefix

    def sadd(self, key: str, value: str):
        LOGGER.debug(f"Adding {value} to set {key}")
        self._redis.sadd(key, value)

    def smembers(self, key: str) -> Set[bytes]:
        LOGGER.debug(f"Getting members of set {key}")
        return self._redis.smembers(key)

    def _get_index_key(self, prefix: str) -> str:
        return f"{self.index_prefix}:{prefix}"

    def _remove_index_key(self, key: str) -> str:
        return key[len(self.index_prefix) + 1 :]

    def add_to_index(self, key: str, redis_type: Optional[RedisType] = None):
        if redis_type is None:
            redis_type = RedisType(self._redis.type(key))
        parts = re.findall(r"[a-zA-Z0-9]*[:,]?", key)
        # store parts in a reverse order
        for i, value in reversed(list(enumerate(parts[:-1]))):
            if i == 0:
                break
            subkey = self._get_index_key("".join(parts[:i]))
            # if it's the last part, we add the type
            if i == len(parts) - 2:
                value += f"|{redis_type.value}"
            self.sadd(subkey, value)

    def remove_from_index(self, key: str):
        match = re.match(r"(.*[:,])([a-zA-Z0-9]+[:,]?)", key)
        if not match:
            LOGGER.warning(
                f"Key {key} does not match the expected pattern. Skipping removal from index."
            )
            return
        parent_key, value = match.groups()
        index_key = self._get_index_key(parent_key)
        entries = self._redis.smembers(index_key)
        for entry in entries:
            if entry.decode().startswith(f"{value}|"):
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

    def get_keys_by_prefix(self, pattern: str) -> List[str]:
        """
        Resolves Redis hierarchical keys using wildcard pattern (splitting on '*'),
        traversing Redis Sets that represent each level of the hierarchy.
        Final step uses SMEMBERS of the composed parent to check for final segment.
        """

        def recurse(prefix, suffixes):
            if not suffixes:
                return []

            static_suffix = suffixes[0].lstrip(",")
            rest_suffixes = suffixes[1:]

            redis_key = prefix.encode("utf-8")
            children = self._redis.smembers(redis_key)
            children = [c.decode("utf-8") for c in children]

            results = []

            for child in children:
                new_prefix = prefix + child
                if rest_suffixes:
                    # More wildcards to process — keep traversing
                    results.extend(recurse(new_prefix + static_suffix, rest_suffixes))
                else:
                    # Final wildcard: check if static_suffix is in new_prefix's set
                    final_key = new_prefix.encode("utf-8")
                    final_children = self._redis.smembers(final_key)
                    final_children = [c.decode("utf-8") for c in final_children]
                    if static_suffix == "" or static_suffix in final_children:
                        results.append(new_prefix + static_suffix)

            return results

        parts = pattern.split("*")
        base_prefix = parts[0]
        suffixes = parts[1:]

        return recurse(base_prefix, suffixes)

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
