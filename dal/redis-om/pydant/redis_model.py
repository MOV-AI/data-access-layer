from abc import ABC, abstractmethod, abstractclassmethod
from pydantic import BaseModel
import re
import redis


pool = redis.ConnectionPool(host="172.17.0.2", port=6379, db=1)
valid_models = [
    "Flow",
    "Node",
    "Callback",
    "Annotation",
    "GraphicScene"
]

class RedisModel(BaseModel):
    class Config:
        orm_mode = True
        validate_assignment = True

    @staticmethod
    def _generate_id(type: str, name: str, version: str):
        return f"{type}:{name}:{version}"

    @property
    def id(self):
        return RedisModel._generate_id(self.__class__.__name__, self.name, self.Version)

    @classmethod
    def db(cls) -> redis.Redis:
        global pool
        return redis.Redis(connection_pool=pool)

    def save(self) -> str:
        self.db().json().set(self.id, "$", self.dict())

    @abstractclassmethod
    def select(cls, names: list, version: str):
        """_summary_

        Args:
            name (str): _description_
            version (str): _description_
        """

    def dict(self):
        return {self.__class__.__name__: {self.name: super().dict()}}

    def __str__(self) -> str:
        return f"{self.dict()}"
