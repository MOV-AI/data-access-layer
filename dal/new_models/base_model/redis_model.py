from typing import List, Tuple
from pydantic import ConfigDict, BaseModel
import redis
from dal.movaidb import Redis
from .cache import ThreadSafeCache
from .common import PrimaryKey, DEFAULT_VERSION
from .redis_config import RedisConfig


DEFAULT_PROJECT = "Movai"
cache = ThreadSafeCache()


def connect_to_redis(redis_config=RedisConfig()) -> redis.Redis:
    """Connects to redis.
        TODO: check this.
        another option for a redis connection in case we are removing movaidb
    """
    return redis.from_url(
        redis_config.redis_url,
        encoding=redis_config.encoding,
        decode_responses=True,
    )


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
        """keys to be included in the final model_dump function

        Returns:
            List[str]: desired key for the model_dump function
        """
        return []

    @classmethod
    def db(cls, type: str) -> redis.Redis:
        """return the redis connection object

        Args:
            type (str): type of redis connection, global or local
                        global for master/slave, local for local

        Returns:
            redis.Redis: redis connection
        """
        if type == "global":
            return Redis().db_global
        elif type == "local":
            return Redis().db_local

    @property
    def keyspace_pattern(self) -> str:
        """return the keyspace pattern of the object in Redis

        Returns:
            str: keyspace patter for redis.
        """
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

    def delete(self, db_type="global") -> None:
        """delete object from redis

        Returns:
            None: None
        """
        self.db(db_type).delete(self.pk)
        if self.pk in cache:
            del cache[self.pk]

    @classmethod
    def model_fetch_ids(cls, project=None, version=None, db="global") -> List[Tuple[str, str, str]]:
        """returns a list of tuples including all of the keys from the
           same class in Redis according to the calling class (Flow/Node/Callback/...).
           a Tuple will indicate (project, id, version)
 
        Args:
            project: project id to search for, if None, all projects will be returned
            version: version to search for, if None, all versions will be returned
            db: global(redis-master) or local(redis-local), default: global

        Time Complexity:
            O(n) where n is the number of keys in Redis
            this can be enhaned by storing the ids strings inside a Redis SET and fetching
            it instead of fetching all keys and filtering them, which would result in O(1)

        Returns:
            List[tuple]: list of tuples of all keys in DB that belongs to that project
                         and class type Tuples include (project, id, version)
        """
        project = "*" if project is None else project
        version = "*" if version is None else version
        return [
            tuple([key.decode().split(":")[0]] + key.decode().split(":")[2:])
            for key in cls.db(db).keys(f"{project}:{cls.__name__}:*:{version}")
        ]

    @classmethod
    def select(
        cls, ids: List[str] = None, project=DEFAULT_PROJECT, version=DEFAULT_VERSION, db="global"
    ) -> List:
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
            db: global(redis-master) or local(redis-local), default: global
        """
        ret = []
        if not ids:
            # get all objects of type cls
            ids = [
                key.decode()
                for key in cls.db(db).keys(f"{project}:{cls.__name__}:*:{version}")
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


def get_project_ids(project, db="global", version=None) -> List[tuple]:
    """
        returns a list of tuples of all objects existing in DB for the given project

    Args:
        project (str): the project id.
        db (str, optional): type of database to use "local"/"global". Defaults to "global".
        version (str, optional): desired version. Defaults to None.
                                if None, all versions will be returned

    Returns:
        tuple: tuple of (type, id, version)
    """
    database = RedisModel.db(db)
    version = "*" if not version else version
    return [
        tuple(key.decode().split(":")[1:])
        for key in database.keys(f"{project}:*:*:{version}")
    ]
