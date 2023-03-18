from typing import Optional, Union
from redis_om import Field, get_redis_connection, JsonModel
import pydantic
import json
from re import search


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
                id = f"{cls}:{name}:{version}"
                if search(r"^[a-zA-Z0-9_]+$", name) is None:
                    raise ValueError(f"Validation Error for {type} name:({name}), data:{kwargs}")

                super().__init__(**struct_[name], id=id)
            else:
                raise ValueError(f"wrong Data type, should be {cls}, instead got: {list(kwargs.keys())[0]}")

    def dict(self):
        dic = super().dict(exclude_unset=True)
        id = dic.pop('id')
        return {self.__class__.__name__: {id.split(":")[1]: dic}}

    def schema_json(self):
        schema = json.loads(super().schema_json())
        schema["properties"].pop("pk")
        schema["properties"].pop("id")
        return schema
