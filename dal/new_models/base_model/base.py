from typing import List, Optional, Union
import pydantic
import json
from .redis_model import RedisModel
from .common import PrimaryKey
from re import search


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
    "GraphicScene",
    "Layout",
    "Application",
]


class MovaiBaseModel(RedisModel):
    Info: Optional[str] = None
    Label: pydantic.constr(regex=LABEL_REGEX)
    Description: Optional[str] = None
    LastUpdate: Union[LastUpdate, str]
    Version: str = DEFAULT_VERSION
    name: str = ""
    project: str = ""

    def __new__(cls, *args, **kwargs):
        if not kwargs:
            if not args:
                raise Exception("No arguments provided")
            id = args[0]
            version = DEFAULT_VERSION
            if len(args > 1):
                version = args[1]
            obj = cls.select(ids=[f"{id}:{version}"])
            if not obj:
                raise Exception(f"Model {args[0]} not found!")
            return obj[0]
        return super().__new__(cls)

    def _additional_keys(self) -> List[str]:
        return super()._additional_keys() + ["name", "project"]

    def __init__(self, *args, project: str = "", **kwargs):
        if not kwargs:
            return
        version = DEFAULT_VERSION
        if "version" in kwargs:
            version = kwargs["version"]
        cls = self.__class__.__name__
        if list(kwargs.keys())[0] in valid_models:
            if list(kwargs.keys())[0] == cls:
                if kwargs is None or not isinstance(kwargs, dict):
                    return
                type, struct_ = list(kwargs.items())[0]
                name = list(struct_.keys())[0]
                params = {"name": name, "project": project}
                if "pk" not in struct_[name]:
                    pk = PrimaryKey.create_pk(id=name, version=version)
                    params.update({"pk": pk})
                if search(LABEL_REGEX, name) is None:
                    raise ValueError(
                        f"Validation Error for {type} name:({name}), data:{kwargs}"
                    )

                struct_[name]["Version"] = version
                super().__init__(**struct_[name], **params)
            else:
                raise ValueError(
                    f"wrong Data type, should be {cls}, instead got: {list(kwargs.keys())[0]}"
                )

    def schema_json(self):
        schema = json.loads(super().schema_json())
        [schema["properties"].pop(key) for key in self._additional_keys()]
        return schema

    def dict(self):
        dic = super().dict()
        [dic.pop(key) for key in self._additional_keys()]
        return {self.__class__.__name__: {self.name: dic}}

