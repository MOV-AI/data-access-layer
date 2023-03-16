import pydantic
from typing import Union, Optional, Dict
from pydantic.types import StrictStr
from redis_om import Migrator
from base import MovaiBaseModel


ValidStr = pydantic.constr(regex=r"^[a-zA-Z_]+$")
ValidStrNums = pydantic.constr(regex=r"^[a-zA-Z0-9_]+$")


class Py3LibValue(pydantic.BaseModel):
    Class: Union[StrictStr, bool] = None
    Module: str


class Callback(MovaiBaseModel):
    Code: Optional[str] = None
    Message: Optional[str] = None
    Py3Lib: Dict[ValidStr, Py3LibValue]

    class Meta:
        model_key_prefix = "Callback"


callback = Callback(
    **{
        "Callback": {
            "annotations_initxxxx": {
                "Code": 1,
                "Info": "asglksdjlkdsjf",
                "Label": "annotations_init",
                "LastUpdate": {"date": "18/01/2023 at 16:42:49", "user": "movai"},
                "Message": "movai_msgs/Init",
                "Py3Lib": {
                    "Annotation": {"Class": "Annotation", "Module": "movai.models"}
                },
                "User": "",
                "Version": "v5",
                "VersionDelta": {},
            }
        }
    }, version_="v5"
)
Migrator().run()
#print(Callback.find(Callback.LastUpdate.user == "movai").first())
print(callback.save())
print(Callback.find(Callback.id == "Callback:annotations_initxxxx:v5").first())
print(callback.schema_json())
"""
start = time.time()
#callback.save()
pk = callback.pk
end = time.time()
print(f"saved successfully {callback.pk}")
print(f"saving into redis took {(end-start)*1000}ms\n")


start = time.time()
callback: Callback = Callback.get(pk)
end = time.time()
print(f"Searching and Object Creation using Global ID {(end-start)*1000}ms\n")

start = time.time()
print("Fetching Data")
print(
    callback.Code,
    callback.Info,
    callback.Label,
    callback.Message,
    callback.LastUpdate,
    callback.Version,
    callback.Py3Lib
)
end = time.time()
print(f"Fetching Fields (after object Creation) took {(end - start) * 1000}ms\n")

start = time.time()
print("Searching by Index")
print(Callback.find(Callback.Label == "annotations_init").all())
print(Callback.find(Callback.LastUpdate.user == "movai"))
end = time.time()
print(f"searching by Index and creating instance took {(end - start) * 1000}ms\n")

print("Running FOR LOOP")
for i in range(10000):
    callback = Callback(
        **{
            "Callback": {
                "annotations_init": {
                    "Code": 1,
                    "Info": "asglksdjlkdsjf",
                    "Label": "annotations_init",
                    "LastUpdate": {"date": "18/01/2023 at 16:42:49", "user": "movai"},
                    "Message": "movai_msgs/Init",
                    "Py3Lib": {
                        "Annotation": {"Class": "Annotation", "Module": "movai.models"}
                    },
                    "User": "",
                    "Version": f"v{i}",
                    "VersionDelta": {},
                }
            }
        }
    )
    #callback.save()

start = time.time()
for i in range(10000):
    c = Callback.find(Callback.Version == f"v{i}").first()
    if c is not None:
        print(f"Callback {c.pk} FOUND ....... V")
    else:
        print(f"Callback version v{i} NOT FOUND ...... X")
end = time.time()
print(f"searching by Index for 10000 elements took {(end - start) * 1000}ms\n")
"""
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
