from typing import Optional
from dataclasses import dataclass, asdict
from redis import asyncio as redis


@dataclass
class RedisConfig:
    """A config object for connecting to redis"""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    encoding: Optional[str] = "utf-8"

    @property
    def redis_url(self) -> str:
        """Returns a redis url to connect to"""
        protocol = "rediss" if self.ssl else "redis"
        if self.password is None:
            return f"{protocol}://{self.host}:{self.port}/{self.db}"
        return f"{protocol}://:{self.password}@{self.host}:{self.port}/{self.db}"

    def dict(self):
        return asdict(self)


# RedisConfig("redis-master").redis_url
