from typing import Optional
import pydantic
from abc import abstractmethod, ABC

# from ulid import ULID

DEFAULT_DB = "global"
DEFAULT_VERSION = "__UNVERSIONED__"


class Arg(pydantic.BaseModel):
    Description: Optional[str] = None
    Value: object = pydantic.Field(default_factory=dict)
    Type: Optional[str] = None


class AbstractPrimaryKey(ABC):
    @classmethod
    @abstractmethod
    def create_pk(*args, **kwargs):
        """A primary key generator"""


class UlidPrimaryKey(AbstractPrimaryKey):
    """
    A client-side generated primary key that follows the ULID spec.
    https://github.com/ulid/javascript#specification
    """

    @classmethod
    def create_pk(*args, **kwargs) -> str:
        return str("")  # ULID())


class MovaiPrimaryKey(AbstractPrimaryKey):
    @classmethod
    def create_pk(*args, scope: str = "", id: str = "", version: str = ""):
        # return f"{id}:{version}:{UlidPrimaryKey.create_pk()}"
        return f"{scope}:{id}:{version}"


class RobotKey(AbstractPrimaryKey):
    @classmethod
    def create_pk(*args, fleet: str = "", scope: str = "", id: str = "", version: str = ""):
        return f"Fleet:{fleet}:{scope}:{id}"


PrimaryKey = MovaiPrimaryKey
