import asyncio
from os import getenv
import warnings

import aioredis
import redis
from redis import Connection
from movai_core_shared import Log

from dal.classes.common.singleton import Singleton


REDIS_MASTER_HOST = getenv("REDIS_MASTER_HOST", "redis-master")
REDIS_MASTER_PORT = int(getenv("REDIS_MASTER_PORT", 6379))
REDIS_SLAVE_HOST = getenv("REDIS_SLAVE_HOST", REDIS_MASTER_HOST)
REDIS_SLAVE_PORT = int(getenv("REDIS_SLAVE_PORT", REDIS_MASTER_PORT))
REDIS_LOCAL_HOST = getenv("REDIS_LOCAL_HOST", "redis-local")
REDIS_LOCAL_PORT = int(getenv("REDIS_LOCAL_PORT", 6379))

LOGGER = Log.get_logger("dal.mov.ai")


class AioRedisClient(metaclass=Singleton):
    """
    A Singleton class implementing AioRedis API.
    """

    _databases = {}
    loop = asyncio.get_event_loop()

    @classmethod
    def _register_databases(cls):
        if not cls._databases:
            cls._databases = {
                "db_slave": {
                    "name": "db_slave",
                    "host": REDIS_SLAVE_HOST,
                    "port": REDIS_SLAVE_PORT,
                    "mode": None,
                    "enabled": True,
                },
                "db_local": {
                    "name": "db_local",
                    "host": REDIS_LOCAL_HOST,
                    "port": REDIS_LOCAL_PORT,
                    "mode": None,
                    "enabled": True,
                },
                "slave_pubsub": {
                    "name": "slave_pubsub",
                    "host": REDIS_SLAVE_HOST,
                    "port": REDIS_SLAVE_PORT,
                    "mode": "SUB",
                    "enabled": True,
                },
                "local_pubsub": {
                    "name": "local_pubsub",
                    "host": REDIS_LOCAL_HOST,
                    "port": REDIS_LOCAL_PORT,
                    "mode": "SUB",
                    "enabled": True,
                },
                "db_global": {
                    "name": "db_global",
                    "host": REDIS_MASTER_HOST,
                    "port": REDIS_MASTER_PORT,
                    "mode": None,
                    "enabled": False,
                },
            }

    async def shutdown(self):
        """shutdown connections"""
        for conn, _ in type(self)._databases.items():
            if getattr(self, conn) is not None:
                getattr(self, conn).close()
        tasks = [
            getattr(self, db_name).wait_closed()
            for db_name in type(self)._databases.keys()
            if getattr(self, db_name) is not None
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    @classmethod
    async def get_client(cls):
        """will return class singleton instance

        Returns:
            AioRedisClient: object of class AioRedisClient
        """
        cls._register_databases()
        instance = cls()
        await instance._init_databases()
        return instance

    async def _init_databases(self):
        """will initialize connection pools"""

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            for conn_name, conn_config in type(self)._databases.items():
                conn_enabled = conn_config.get("enabled", False)
                _conn = None
                if conn_enabled:
                    _conn = getattr(self, conn_name, None)
                    if not _conn or _conn.closed:
                        try:
                            address = (conn_config["host"], conn_config["port"])
                            if conn_config.get("mode") == "SUB":
                                _conn = await aioredis.create_pool(
                                    address,
                                    minsize=1,
                                    maxsize=100,
                                    pool_cls=aioredis.ConnectionsPool,
                                )
                            else:
                                _conn = await aioredis.create_redis_pool(
                                    address,
                                    minsize=2,
                                    maxsize=100,
                                    timeout=1,
                                    pool_cls=aioredis.ConnectionsPool,
                                )

                        except Exception as e:
                            LOGGER.error(e, exc_info=True)
                            raise e
                setattr(self, conn_name, _conn)

    @classmethod
    def enable_db(cls, db_name):
        """will enable the given db name

        Args:
            db_name (str): database name
        """
        cls._register_databases()
        cls._databases[db_name]["enabled"] = True


class Redis(metaclass=Singleton):
    """
    A Singleton class implementing Redis API.
    """

    def __init__(self):
        self.master_pool = redis.ConnectionPool(
            connection_class=Connection,
            host=REDIS_MASTER_HOST,
            port=REDIS_MASTER_PORT,
            db=0,
        )
        self.slave_pool = redis.ConnectionPool(
            connection_class=Connection,
            host=REDIS_SLAVE_HOST,
            port=REDIS_SLAVE_PORT,
            db=0,
        )
        self.local_pool = redis.ConnectionPool(
            connection_class=Connection,
            host=REDIS_LOCAL_HOST,
            port=REDIS_LOCAL_PORT,
            db=0,
        )

        self.thread = None

    @property
    def db_global(self) -> redis.Redis:
        return redis.Redis(connection_pool=self.master_pool, decode_responses=False)

    @property
    def db_slave(self) -> redis.Redis:
        return redis.Redis(connection_pool=self.slave_pool, decode_responses=False)

    @property
    def db_local(self) -> redis.Redis:
        return redis.Redis(connection_pool=self.local_pool, decode_responses=False)

    @property
    def slave_pubsub(self) -> redis.client.PubSub:
        return self.db_slave.pubsub()

    def local_pubsub(self) -> redis.client.PubSub:
        return self.db_local.pubsub()
