import pydantic
from typing import Union, Optional, Dict
from base import BaseSchema
from redis_model import RedisModel
from pydantic.types import StrictStr
import time


ValidStr = pydantic.constr(regex=r"^[a-zA-Z_]+$")
ValidStrNums = pydantic.constr(regex=r"^[a-zA-Z0-9_]+$")


class Py3LibValue(pydantic.BaseModel):
    Class: Union[StrictStr, bool] = None
    Module: str


class CallbackSchema(BaseSchema):
    Code: Optional[str] = None
    Message: Optional[str] = None
    Py3Lib: Optional[Dict[ValidStr, Py3LibValue]] = None


class Callback(RedisModel):
    name: str = None
    struct: CallbackSchema

    def __init__(self, value: dict, version: str = "v1") -> None:
        super().__init__(value, version)

    def create_validate_dict(self, val: dict):
        self.struct = CallbackSchema(**val)
        return self.struct

    @classmethod
    def get(cls, name: str, version: str = "v1"):
        id = Callback._generate_id("Callback", name, version)
        ret = cls.db().json().get(id)
        return Callback({"Callback": {name: ret}}, version)

    class Config:
        # Force Validation in case field value change
        validate_assignment = True


r = Callback(
    {
        "Callback": {
            "annotations_init": {
                "Info": "asglksdjlkdsjf",
                "Label": "annotations_init",
                "LastUpdate": {"date": "18/01/2023 at 16:42:49", "user": "movai"},
                "Message": "movai_msgs/Init",
                "Py3Lib": {
                    "Annotation": {"Class": "Annotation", "Module": "movai.models"}
                },
                "User": "",
                "Version": "",
                "VersionDelta": {},
            }
        }
    }
)

r.save()
r.struct.Label = 5

start = time.time()
callback: Callback = Callback.get("annotations_init")
end = time.time()
print(f"Searching and Object Creation took {(end-start)*1000}ms")

start = time.time()
print("Fetching Data")
print(
    callback.struct.Code,
    callback.struct.Info,
    callback.struct.Label,
    callback.struct.Message,
    callback.struct.LastUpdate,
    callback.struct.Version,
    callback.struct.Py3Lib,
)
end = time.time()
print(f"Fetching Fields (after object Creation) took {(end - start) * 1000}ms")
"""
print("====================================================")
print("the old ugly Scopes\n")

from deprecated.api.models.callback import Callback as ScopesCallback

start = time.time()
callback = ScopesCallback("Choose_DS_start")
end = time.time()
print(f"Searching and Object Creation took {(end-start)*1000}ms")

start = time.time()
print("Fetching Data")
print(
    callback.Code,
    callback.Info,
    callback.Label,
    callback.Message,
    callback.LastUpdate,
    callback.Version,
    callback.User,
)
end = time.time()
print(f"Fetching Fields (after object Creation) took {(end - start) * 1000}ms")

print("====================================================")
print("the Models mechanism\n")

from movai.models.callback import Callback as ModelsCallback

start = time.time()
callback = ModelsCallback("Choose_DS_start")
end = time.time()
print(f"Searching and Object Creation took {(end-start)*1000}ms")

start = time.time()
print("Fetching Data")
print(
    callback.Code,
    callback.Info,
    callback.Label,
    callback.Message,
    callback.LastUpdate,
    callback.Version,
    callback.User,
)
end = time.time()

print(f"Fetching Fields (after object Creation) took {(end - start) * 1000}ms")
"""
