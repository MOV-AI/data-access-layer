from typing import Optional, Union
import pydantic
import json
from re import search
from redis_model import RedisModel


DEFAULT_VERSION = "__UNVERSIONED__"


class LastUpdate(pydantic.BaseModel):
    date: str
    user: str


LABEL_REGEX = r"^[a-zA-Z0-9._-]+$"
valid_models = [
    "Flow",
    "Node",
    "Callback",
    "Annotation",
    "GraphicScene"
]


class MovaiBaseModel(RedisModel):
    Info: Optional[str] = None
    Label: pydantic.constr(regex=LABEL_REGEX)
    Description: Optional[str] = None
    LastUpdate: Union[LastUpdate, str]
    Version: str = DEFAULT_VERSION
    id_: str = pydantic.Field(alias="id")

    def __init__(self, *args, **kwargs):
        version = "__UNVERSIONED__"
        if "version" in kwargs:
            version = kwargs["version"]
        cls = self.__class__.__name__
        if list(kwargs.keys())[0] in valid_models:
            if list(kwargs.keys())[0] == cls:
                if kwargs is None or not isinstance(kwargs, dict):
                    return
                type, struct_ = list(kwargs.items())[0]
                name = list(struct_.keys())[0]
                self._generate_id(cls, name, version)
                id = self._generate_id(cls, name, version)
                if search(r"^[a-zA-Z0-9_]+$", name) is None:
                    raise ValueError(f"Validation Error for {type} name:({name}), data:{kwargs}")

                struct_[name]["Version"] = version
                super().__init__(**struct_[name], id=id, name=name)
            else:
                raise ValueError(f"wrong Data type, should be {cls}, instead got: {list(kwargs.keys())[0]}")

    def dict(self):
        dic = super().dict()
        return {self.__class__.__name__: {self.name: dic}}

    def schema_json(self):
        schema = json.loads(super().schema_json())
        schema["properties"].pop("pk")
        return schema
