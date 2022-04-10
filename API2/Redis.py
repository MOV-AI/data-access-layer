"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi  (moawiya@mov.ai) - 2022
"""
from dal.movaidb import Redis, RedisClient, MovaiDB

REDIS_SLAVE_HOST = MovaiDB.REDIS_SLAVE_HOST
REDIS_SLAVE_PORT = MovaiDB.REDIS_SLAVE_PORT
REDIS_LOCAL_HOST = MovaiDB.REDIS_LOCAL_HOST
REDIS_LOCAL_PORT = MovaiDB.REDIS_LOCAL_PORT
REDIS_MASTER_HOST = MovaiDB.REDIS_MASTER_HOST
REDIS_MASTER_PORT = MovaiDB.REDIS_MASTER_PORT

__all__ = [
    "Redis",
    "RedisClient",
    "REDIS_SLAVE_HOST",
    "REDIS_SLAVE_PORT",
    "REDIS_LOCAL_HOST",
    "REDIS_LOCAL_PORT",
    "REDIS_MASTER_HOST",
    "REDIS_MASTER_PORT"
]
