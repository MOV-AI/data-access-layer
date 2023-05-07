from typing import List
from pydantic import BaseModel
import redis


pool = redis.ConnectionPool(host="172.17.0.2", port=6379, db=1)
valid_models = ["Flow", "Node", "Callback", "Annotation", "GraphicScene"]
GLOBAL_KEY_PREFIX = "Movai"


class RedisModel(BaseModel):
    pk: str

    class Config:
        orm_mode = True
        validate_assignment = True

    class Meta:
        model_key_prefix = "Redis"

    @classmethod
    def db(cls) -> redis.Redis:
        global pool
        return redis.Redis(connection_pool=pool)

    def save(self) -> str:
        self.db().json().set(
            self.pk,
            "$",
            self.dict(),
        )
        return self.pk

    @classmethod
    def select(cls, ids: List[str] = None) -> list:
        """_summary_

        Args:
            ids (List[str]): list of ids to search for
        """
        ret = []
        if not ids:
            # get all objects of type cls
            ids = cls.db().keys(f"{GLOBAL_KEY_PREFIX}:{cls.Meta.model_key_prefix}:*")
        for id in ids:
            obj = cls.db().json().get(id)
            if obj is not None:
                ret.append(cls(**obj))
        return ret
