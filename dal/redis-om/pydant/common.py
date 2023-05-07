from typing import Optional
import pydantic
from abc import abstractmethod, ABC
from ulid import ULID


class Arg(pydantic.BaseModel):
    Description: Optional[str] = None
    Value: object
    Type: Optional[str] = None


class AbstractPrimaryKey(ABC):
    @classmethod
    @abstractmethod
    def create_pk(*args, **kwargs):
        """ A primary key generator"""


class UlidPrimaryKey(AbstractPrimaryKey):
    """
    A client-side generated primary key that follows the ULID spec.
    https://github.com/ulid/javascript#specification
    """
    @classmethod
    def create_pk(*args, **kwargs) -> str:
        return str(ULID())


class MovaiPrimaryKey(AbstractPrimaryKey):
    @classmethod
    def create_pk(*args, id: str = "", version: str = ""):
        return f"{id}:{version}:{UlidPrimaryKey.create_pk()}"


PrimaryKey = MovaiPrimaryKey
