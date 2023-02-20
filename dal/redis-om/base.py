import enum
from typing import Optional, Union
from pydantic import BaseModel, constr
from pydantic.config import BaseConfig


class LastUpdate(BaseModel):
    date: str
    user: str


class BaseSchema(BaseModel):
    class Config(BaseConfig):
        exclude = ["Version"]

    Info: Optional[str] = None
    Label: constr(regex=r"^[a-zA-Z0-9._-]+$")
    Description: Optional[str] = None
    LastUpdate: Union[LastUpdate, str]
    Version: str = "__UNVERSIONED__"  # added for tests


class CSVColumns(enum.Enum):
    LastUpdate_date = "LastUpdate.date"
    LastUpdate_user = "LastUpdate.user"
