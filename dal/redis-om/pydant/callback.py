import pydantic
from typing import Union, Optional, Dict
from base import MovaiBaseModel
from pydantic.types import StrictStr
import time


ValidStr = pydantic.constr(regex=r"^[a-zA-Z_]+$")
ValidStrNums = pydantic.constr(regex=r"^[a-zA-Z0-9_]+$")


class Py3LibValue(pydantic.BaseModel):
    Class: Union[StrictStr, bool] = None
    Module: str


class Callback(MovaiBaseModel):
    name: str = None
    Code: Optional[str] = None
    Message: Optional[str] = None
    Py3Lib: Optional[Dict[ValidStr, Py3LibValue]] = None

    class Meta:
        model_key_prefix = "Callback"


if __name__ == "__main__":
    r = Callback(
        **{
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
    r.dict()
    pk = r.save()
    # because Label is string, the 5 will be converted automatically to string "5"
    r.Label = 5
    pk = r.save()

    start = time.time()
    callbacks = Callback.select(ids=[pk])
    print(callbacks)
    cs = Callback.select()
    print("$$$$$$$$$$$$$$$$$$$")
    print(cs)
    if callbacks:
        callback: Callback = callbacks[0]
        print(callback.dict())
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
            callback.Py3Lib,
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
