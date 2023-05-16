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

    def _additional_keys(self) -> List[str]:
        return ["pk"]

    @classmethod
    def db(cls) -> redis.Redis:
        global pool
        return redis.Redis(connection_pool=pool)

    def save(self) -> str:
        main_key = f"{GLOBAL_KEY_PREFIX}:{self.Meta.model_key_prefix}:{self.pk}"
        if self.project != "":
            main_key = f"{self.project}:{self.Meta.model_key_prefix}:{self.name}"
        self.db().json().set(
            main_key,
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
            ids = [
                key.decode()
                for key in cls.db().keys(
                    f"{GLOBAL_KEY_PREFIX}:{cls.Meta.model_key_prefix}:*"
                )
            ]
        for id in ids:
            if len(id.split(":")) == 1:
                # no version in id
                id = f"{id}:__UNVERSIONED__"
            if cls.Meta.model_key_prefix not in str(id):
                id = f"{GLOBAL_KEY_PREFIX}:{cls.Meta.model_key_prefix}:{id}"
            obj = cls.db().json().get(id)
            if obj is not None:
                ret.append(cls(**obj))
        return ret
