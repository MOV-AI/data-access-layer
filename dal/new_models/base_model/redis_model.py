"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2023
   - Erez Zomer (erez@mov.ai) - 2023
"""
import json
from logging import Logger
from typing import List, Set, ClassVar

from pydantic import ConfigDict, BaseModel, PrivateAttr
import redis

from movai_core_shared.logger import Log

from dal.archive import Archive
from dal.movaidb import Redis

from .cache import ThreadSafeCache
from .common import MovaiPrimaryKey, DEFAULT_DB, DEFAULT_VERSION
from .redis_config import RedisConfig


CACHE = ThreadSafeCache()


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
    """The very basic model for implementing object mapping (OM)."""

    # pk: Primary key which is the key of the entry in Redis representing this object.
    pk: str
    model_config = ConfigDict(from_attributes=True, validate_assignment=True)
    db: str = DEFAULT_DB
    Version: str = DEFAULT_VERSION
    _logger: ClassVar[Logger] = Log.get_logger(__name__)

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
    def db_handler(cls, db_type: str = DEFAULT_DB) -> redis.Redis:
        """return the redis connection object

        Args:
            type (str): type of redis connection, global or local
                        global for master/slave, local for local

        Returns:
            redis.Redis: redis connection
        """
        if not isinstance(db_type, str):
            raise ValueError("The argument db_type must be a string!")

        db_type = db_type.lower()

        if db_type == "global":
            return Redis().db_global
        elif db_type == "local":
            return Redis().db_local
        else:
            raise ValueError(f"The requested db: '{db_type}' is unknown!")

    @property
    def keyspace_pattern(self) -> str:
        """return the keyspace pattern of the object in Redis

        Returns:
            str: keyspace patter for redis.
        """
        return f"__keyspace@0__:{self.pk}"

    def list_versions(self, db=DEFAULT_DB) -> List[str]:
        """return a list of all versions of the object in Redis

        Returns:
            List[str]: list of versions
        """
        return [
            key.decode().split(":")[-1]
            for key in self.db_handler(db).keys(f"{db}:{self.model}:{self.name}:*")
        ]

    def save(self, db=DEFAULT_DB, version=DEFAULT_VERSION) -> str:
        """dump object to json and save it in redis json using key=pk (PrimaryKey)

        Returns:
            str: _description_
        """
        self.db = db
        self.Version = version
        self.pk = MovaiPrimaryKey(db=db, model=self.model, name=self.name, version=version).pk
        obj = self.model_dump(by_alias=True, exclude_unset=True, exclude_none=True)
        try:
            self.db_handler(db).json().set(self.pk, "$", obj)
        except Exception as exc:
            self._logger.error(
                f"While trying to save model to DB, got the following exception: {exc}."
            )
        CACHE[self.pk] = self.__dict__
        return self.pk

    def delete(self) -> None:
        """delete object from redis

        Returns:
            None: None
        """
        self.db_handler(self.db).delete(self.pk)
        if self.pk in CACHE:
            del CACHE[self.pk]

    def remove(self, **kwargs) -> None:
        """Like delete() for backward compatible with the old OM.
        """
        self.delete()

    @classmethod
    def get_model_keys(cls, db: str = DEFAULT_DB, version: str = DEFAULT_VERSION) -> List[MovaiPrimaryKey]:
        """Fetch the Model keys from db.

        Args:
            version (str, optional): The version of the keys to fetch. Defaults to 
            "__UNVERSIONED__".
            db (str, optional): The db to fetch the keys from. Defaults to "global".

        Returns:
            List[str]: A list of all the keys related to that Model in the specified version.
        """
        model = cls.__name__
        keys = []
        for key in cls.db_handler(db).keys(f"{db}:{model}:*:{version}"):
            keys.append(key.decode())
        return keys

    @classmethod
    def get_model_names(cls, db: str = DEFAULT_DB, version: str = DEFAULT_VERSION) -> Set[str]:
        """returns a list of tuples including all of the names of the
           same Model in DB according to the calling Model (Flow/Node/Callback/...).
           a Tuple will indicate (name, version)

        Args:
            version: version to search for, Defaults to '__UNVERSIONED__'.
            db: global(redis-master) or local(redis-local), Default to 'global'.

        Time Complexity:
            O(n) where n is the number of keys in Redis
            this can be enhaned by storing the ids strings inside a Redis SET and fetching
            it instead of fetching all keys and filtering them, which would result in O(1)

        Returns:
            List[tuple]: list of tuples of all names in DB and version.
            Tuples include (name, version)
        """
        models_keys = cls.get_model_keys(db, version)
        names = set()
        for key in models_keys:
            name = key.split(":")[2]
            names.add(name)
        return names

    @classmethod
    def get_model_objects(
        cls, names: List[str] = None, db=DEFAULT_DB, version=DEFAULT_VERSION
    ) -> List[BaseModel]:
        """query objects from redis by id if id is not provided,
        all objects of type cls will be returned

        Args:
            names (List[str]): list of names to search for.
                            either it's a list of simple name, etc, tugbot_flow, node1
                            or it's a list of names of object id and a version seperated by
                            ":" global:Flow:flow1:v1, global:Flow:flow2:v2, in the last case version param won't
                            be taken into consideration
            db (str): global(redis-master) or local(redis-local), default to 'global'.
            version (str): version of the object, default to '__UNVERSIONED__'.
        """
        if not names:
            names = cls.get_model_names(db, version)
        ret = [cls(name) for name in names]
        return ret

    @classmethod
    def select_git(cls, remote: str, file_path: str, version: str):
        """find object from git archive and load it inside instance

        Args:
            remote (str): the git remote url
            file_path (str): file path from root of the remote
            version (str): desired file version

        Returns:
            _type_: _description_
        """
        archive = Archive(user="TEMP")
        # local_path_repo = archive.local_path(remote)
        path = archive.get(file_path, remote, version)
        with path.open("r") as f:
            return cls.model_validate(json.load(f), version=version)
