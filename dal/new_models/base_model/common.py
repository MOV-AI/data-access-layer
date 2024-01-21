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
    def create_pk(cls, *args, **kwargs):
        """A primary key generator"""


class UlidPrimaryKey(AbstractPrimaryKey):
    """
    A client-side generated primary key that follows the ULID spec.
    https://github.com/ulid/javascript#specification
    """

    @classmethod
    def create_pk(cls, *args, **kwargs) -> str:
        return str("")  # ULID())


class MovaiPrimaryKey(AbstractPrimaryKey):
    """A primary key for MovaAi models in db.
    """
    @classmethod
    def create_pk(cls, name: str, version: str = DEFAULT_VERSION) -> str:
        """Create a primary key in the format of: Scope:Name:Version

        Args:
            name (str, optional): The name of the object. Defaults to "".
            version (str, optional): The version of the object. Defaults to "".

        Returns:
            str: A key in the required format.
        """
        scope = cls.__name__
        return f"{scope}:{name}:{version}"


class RobotKey(MovaiPrimaryKey):
    """A primary key for specific for the Robot model.
    """
    @classmethod
    def create_pk(cls, fleet: str, name: str, version: str = DEFAULT_VERSION):
        pk = super().create_pk(name, version)
        return f"Fleet:{fleet}:{pk}"


PrimaryKey = MovaiPrimaryKey
