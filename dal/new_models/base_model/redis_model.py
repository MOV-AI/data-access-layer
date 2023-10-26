from typing import List
from pydantic import ConfigDict, BaseModel
import redis
from dal.movaidb import Redis
from .cache import ThreadSafeCache
from .common import PrimaryKey, DEFAULT_VERSION


GLOBAL_KEY_PREFIX = "Movai"
cache = ThreadSafeCache()


class RedisModel(BaseModel):
    # pk: Primary key which is the key of the entry in Redis representing this object.
    pk: str
    model_config = ConfigDict(from_attributes=True, validate_assignment=True)

    @classmethod
    def _original_keys(cls) -> List[str]:
        return []

    @classmethod
    def db(cls, type: str) -> redis.Redis:
        if type == "global":
            return Redis().db_global
        elif type == "local":
            return Redis().db_local

    @property
    def keyspace_pattern(self) -> str:
        return f"__keyspace@0__:{self.pk}"

    def save(self, db_type="global", version=None) -> str:
        """_summary_

        Returns:
            str: _description_
        """
        if version is None:
            version = self.Version
        if version != self.pk.split(":")[-1]:
            self.pk = PrimaryKey.create_pk(
                project=self.project, scope=self.scope, id=self.name, version=version
            )
        self.db(db_type).json().delete(self.pk)
        self.Version = version
        self.db(db_type).json().set(
            self.pk,
            "$",
            self.model_dump(by_alias=True, exclude_unset=True, exclude_none=True),
        )
        cache[self.pk] = self
        return self.pk

    @classmethod
    def select(cls, ids: List[str] = None, project=GLOBAL_KEY_PREFIX) -> list:
        """query objects from redis by id and project
        if id is not provided, all objects of type cls will be returned

        Args:
            ids (List[str]): list of ids to search for
        """
        ret = []
        if not ids:
            # get all objects of type cls
            ids = [
                key.decode()
                for key in cls.db("global").keys(f"{project}:{cls.__name__}:*")
            ]
        for id in ids:
            if len(id.split(":")) == 1:
                # no version in id
                id = f"{id}:{DEFAULT_VERSION}"
            if cls.__name__ not in str(id):
                id = f"{project}:{cls.__name__}:{id}"
            obj = cls.db("global").json().get(id)
            if obj is not None:
                ret.append(cls(**obj))
        return ret
