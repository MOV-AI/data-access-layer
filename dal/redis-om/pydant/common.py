from typing import Optional
import pydantic
from abc import abstractclassmethod
from ulid import ULID


class Arg(pydantic.BaseModel):
    Description: Optional[str] = None
    Value: object
    Type: Optional[str] = None


class AbstractPrimaryKey:
    @abstractclassmethod
    @staticmethod
    def create_pk(*args, **kwargs):
        """ A primary key generator"""


class MovaiPrimaryKey(AbstractPrimaryKey):
    @staticmethod
    def create_pk(*args, id: str = "", version: str = ""):
        return f"{id}:{version}"


class UlidPrimaryKey(AbstractPrimaryKey):
    """
    A client-side generated primary key that follows the ULID spec.
    https://github.com/ulid/javascript#specification
    """

    @staticmethod
    def create_pk(*args, **kwargs) -> str:
        return str(ULID())

PrimaryKey = UlidPrimaryKey

