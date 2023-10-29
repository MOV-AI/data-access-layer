from typing import List
from pydantic import ConfigDict, BaseModel
import redis
from dal.movaidb import Redis
from .cache import ThreadSafeCache
from .common import PrimaryKey, DEFAULT_VERSION


DEFAULT_PROJECT = "Movai"
cache = ThreadSafeCache()


class RedisModel(BaseModel):
    # pk: Primary key which is the key of the entry in Redis representing this object.
    pk: str
    model_config = ConfigDict(from_attributes=True, validate_assignment=True)

    class Meta:
        # variables added here will be treated as a class variables and initialized once.
        # var1 = ""
        # access them self.Meta.var1
        pass

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

    def save(self, db_type="global", version=None, project=None) -> str:
        """dump object to json and save it in redis json using key=pk (PrimaryKey)

        Returns:
            str: _description_
        """
        version = self.Version if version is None else version
        project = self.project if project is None else project
        self.project, self.Version = project, version
        self.pk = PrimaryKey.create_pk(
            project=project, scope=self.scope, id=self.name, version=version
        )

        self.db(db_type).json().set(
            self.pk,
            "$",
            self.model_dump(by_alias=True, exclude_unset=True, exclude_none=True),
        )
        cache[self.pk] = self
        return self.pk

    @classmethod
    def fetch_project_ids(cls, project=None) -> List[tuple]:
        """returns a list of tuples including all of the keys from the
           same project in Redis.
           a Tuple will indicate (project, id, version)
 
        Args:
            project: project id to search for, if None, all projects will be returned

        Returns:
            List[tuple]: list of tuples of all keys in DB that belongs to that project
                         and class type Tuples include (project, id, version)
        """
        project = "*" if project is None else project
        return [
            tuple([key.decode().split(":")[0]] + key.decode().split(":")[2:])
            for key in cls.db("global").keys(f"{project}:{cls.__name__}:*")
        ]

    @classmethod
    def select(
        cls, ids: List[str] = None, project=DEFAULT_PROJECT, version=DEFAULT_VERSION
    ) -> List["RedisModel"]:
        """query objects from redis by id and project
        if id is not provided, all objects of type cls will be returned

        Args:
            ids (List[str]): list of ids to search for.
                            either it's a list of simple id, etc, tugbot_flow, node1
                            or it's a list of ids of object id and a version seperated by
                            ":" flow1:v1, flow2:v2, in the last case version param won't
                            be taken into consideration
            project: a project id
            version: version of the object
        """
        ret = []
        if not ids:
            # get all objects of type cls
            ids = [
                key.decode()
                for key in cls.db("global").keys(f"{project}:{cls.__name__}:*:{version}")
            ]
        for id in ids:
            if len(id.split(":")) == 1:
                # no version in id
                id = f"{id}:{version}"
            if cls.__name__ not in id:
                id = f"{project}:{cls.__name__}:{id}"
            obj = cls.db("global").json().get(id)
            if obj is not None:
                ret.append(cls(**obj, version=version, project=project))
        return ret
