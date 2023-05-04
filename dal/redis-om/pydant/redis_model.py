from abc import ABC, abstractmethod, abstractclassmethod
from typing import List
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
    pk: str
    class Config:
        orm_mode = True
        validate_assignment = True

    class Meta:
        model_key_prefix = "Movai"

    @classmethod
    def db(cls) -> redis.Redis:
        global pool
        return redis.Redis(connection_pool=pool)

    def save(self) -> str:
        self.db().json().set(f"{self.__class__.__name__}:{self.pk}:", "$", self.dict())
        return self.pk

    @abstractclassmethod
    def select(cls, ids: List[str] = None):
        """_summary_

        Args:
            ids (List[str]): list of ids to search for
        """

    def dict(self):
        dic = super().dict()
        if "name" in dic:
            dic.pop("name")
        if "id_" in dic:
            dic.pop("id_")
        return {self.__class__.__name__: {self.name: dic}}

    def __str__(self) -> str:
        return f"{self.dict()}"
