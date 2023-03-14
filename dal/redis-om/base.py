from typing import Optional, Union
import pydantic
from redis_om import Field, get_redis_connection, JsonModel


class LastUpdate(pydantic.BaseModel):
    date: str
    user: str


LABEL_REGEX = r"^[a-zA-Z0-9._-]+$"


class MovaiBaseModel(JsonModel):
    Info: Optional[str] = None
    Label: pydantic.constr(regex=LABEL_REGEX)
    Description: Optional[str] = None
    LastUpdate: Union[LastUpdate, str]
    Version: str = "__UNVERSIONED__"
    id: str = Field(default="", index=True)

    class Meta:
        global_key_prefix = "Models"
        database = get_redis_connection(url="redis://172.17.0.2", db=0)

    class Config:
        # Force Validation in case field value change
        validate_assignment = True
