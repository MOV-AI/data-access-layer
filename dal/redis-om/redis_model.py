from abc import ABC, abstractmethod, abstractclassmethod
from re import search
import redis


pool = redis.ConnectionPool(host="172.29.0.7", port=6379, db=1)


class RedisModel(ABC):
    def __init__(self, value: dict, version: str = "v1") -> None:
        if value is None or not isinstance(value, dict):
            return
        type, struct_ = list(value.items())[0]
        # TODO validate types
        if type != "Callback":
            # TODO
            raise Exception()

        self.type = type
        self.check_type()
        self.version = version
        self.name = list(struct_.keys())[0]
        if search(r"^[a-zA-Z0-9_]+$", self.name) is None:
            raise ValueError(
                f"Validation Error for {type} name:({self.name}), data:{value}"
            )

        # Validate fields
        self.struct = self.create_validate_dict(struct_[self.name])

    @staticmethod
    def _generate_id(type: str, name: str, version: str):
        return f":{type}:{name}:{version}"

    @property
    def id(self):
        return RedisModel._generate_id(self.type, self.name, self.version)

    def check_type(self):
        pass

    @abstractmethod
    def create_validate_dict(self, val: dict):
        """_summary_

        Args:
            val (dict): _description_

        Returns:
            _type_: _description_
        """

    @classmethod
    def db(cls) -> redis.Redis:
        global pool
        return redis.Redis(connection_pool=pool)

    def save(self) -> str:
        self.db().json().set(self.id, "$", self.struct.dict())

    @abstractclassmethod
    def get(cls, name: str, version: str):
        """_summary_

        Args:
            name (str): _description_
            version (str): _description_
        """

    def dict(self):
        return {self.type: {self.name: self.struct.dict()}}

    def __str__(self) -> str:
        return f"{self.dict()}"
