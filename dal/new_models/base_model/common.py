"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2023
   - Erez Zomer (erez@mov.ai) - 2023
"""
from typing import Optional
from typing_extensions import Annotated

from pydantic import BaseModel, Field, StringConstraints, computed_field

from movai_core_shared.exceptions import PrimaryKeyError

DEFAULT_DB = "global"
DEFAULT_VERSION = "__UNVERSIONED__"
KEY_REGEX = Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9./_-]+$")]


class Arg(BaseModel):
    Description: Optional[str] = None
    Value: object = Field(default_factory=dict)
    Type: Optional[str] = None


class MovaiPrimaryKey(BaseModel):
    """A primary key for MovaAi models in db.
    """
    db: KEY_REGEX = Field(default=DEFAULT_DB, min_length=1)
    model: KEY_REGEX = Field(min_length=1)
    name: KEY_REGEX = Field(min_length=1)
    version: KEY_REGEX = Field(default=DEFAULT_VERSION, min_length=1)

    @computed_field
    @property
    def pk(self) -> str:
        return f"{self.db}:{self.model}:{self.name}:{self.version}"


class RobotKey(MovaiPrimaryKey):
    """A primary key for specific for the Robot model.
    """
    @classmethod
    def create_pk(cls, fleet: str, name: str, version: str = DEFAULT_VERSION):
        pk = super().create_pk(name, version)
        return f"Fleet:{fleet}:{pk}"


class PrimaryKeyFactory:
    @classmethod
    def create_movai_pk(cls, db: str, model: str, name: str, version: str):
        """Create a primary key in the format of: Scope:Name:Version

        Args:
            db (str): The db where the object is stored, usually 'global'.
            model (str): The type of model of the object.
            name (str): The name of the object.
            version (str): The version of the object.

        Returns:
            str: A key in the required format.
        """
        return MovaiPrimaryKey(f"{db}:{model}:{name}:{version}")
