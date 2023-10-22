from typing import List
from pydantic import BaseModel
import redis
from dal.movaidb import Redis
from .cache import ThreadSafeCache


GLOBAL_KEY_PREFIX = "Movai"
cache = ThreadSafeCache()


class RedisModel(BaseModel):
    pk: str

    class Config:
        # https://stackoverflow.com/questions/75211183/what-does-pydantic-orm-mode-exactly-do
        orm_mode = True
        validate_assignment = True

    class Meta:
        model_key_prefix = "Redis"

    def _original_keys(self) -> List[str]:
        return []

    def _additional_keys(self) -> List[str]:
        return ["pk"]

    @classmethod
    def db(cls, type: str) -> redis.Redis:
        if type == "global":
            return Redis().db_global
        elif type == "local":
            return Redis().db_local

    @property
    def keyspace_pattern(self) -> str:
        return f"__keyspace@0__:{self.pk}"

    def save(self, db_type="global") -> str:
        """_summary_

        Returns:
            str: _description_
        """
        self.db(db_type).json().delete(self.pk)
        self.db(db_type).json().set(
            self.pk,
            "$",
            self.dict(),
        )
        cache[self.pk] = self
        return self.pk

    @classmethod
    def select(cls, ids: List[str] = None, project=GLOBAL_KEY_PREFIX) -> list:
        """_summary_

        Args:
            ids (List[str]): list of ids to search for
        """
        ret = []
        if not ids:
            # get all objects of type cls
            ids = [
                key.decode()
                for key in cls.db().keys(f"{project}:{cls.Meta.model_key_prefix}:*")
            ]
        for id in ids:
            if len(id.split(":")) == 1:
                # no version in id
                id = f"{id}:__UNVERSIONED__"
            if cls.Meta.model_key_prefix not in str(id):
                id = f"{project}:{cls.Meta.model_key_prefix}:{id}"
            obj = cls.db().json().get(id)
            if obj is not None:
                ret.append(cls(**obj))
        return ret
