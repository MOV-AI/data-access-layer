"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
from deprecated.api.core.redis import (GDRedis, GDRedisInit, Redis, RedisClient)
from deprecated.api.core.redis import (REDIS_SLAVE_HOST, REDIS_SLAVE_PORT, REDIS_LOCAL_HOST,
                            REDIS_LOCAL_PORT, REDIS_MASTER_HOST, REDIS_MASTER_PORT)


__all__ = [
    "GDRedis",
    "GDRedisInit",
    "Redis",
    "RedisClient",
    "REDIS_SLAVE_HOST",
    "REDIS_SLAVE_PORT",
    "REDIS_LOCAL_HOST",
    "REDIS_LOCAL_PORT",
    "REDIS_MASTER_HOST",
    "REDIS_MASTER_PORT"
]
