from typing import List, Optional, Union
import pydantic
import json
from .redis_model import RedisModel, GLOBAL_KEY_PREFIX
from .common import PrimaryKey
from re import search
from movai_core_shared.logger import Log
from cachetools import TTLCache


DEFAULT_VERSION = "__UNVERSIONED__"
LOGGER = Log.get_logger("NEW Models")
cache = TTLCache(maxsize=100, ttl=1200)


class LastUpdate(pydantic.BaseModel):
    date: str
    user: str

    @pydantic.validator("date", pre=True)
    def _validate_date(cls, v):
        if not isinstance(v, str):
            return ""
        return v


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
    Dummy: Optional[bool] = False

    @pydantic.validator("LastUpdate", pre=True)
    def _validate_last_update(cls, v):
        if v is None or isinstance(v, str):
            return LastUpdate(date="", user="")
        return LastUpdate(**v)

    def __new__(cls, *args, **kwargs):
        if args:
            id = args[0]
            if kwargs:
                version = kwargs.get("version", DEFAULT_VERSION)
                project = kwargs.get("project", GLOBAL_KEY_PREFIX)
            else:
                version = DEFAULT_VERSION
                project = GLOBAL_KEY_PREFIX
            key = f"{project}:{cls.__name__}:{id}:{version}"
            if key in cache:
                LOGGER.warning(f"using cached models!!!!!!!!!!!, {key}")
                return cache[key]

            obj = cls.select(ids=[f"{id}:{version}"])
            if not obj:
                raise Exception(f"{cls.__name__} {args[0]} not found!")
            cache[key] = obj[0]
            return obj[0]
        return super().__new__(cls)

    def _additional_keys(self) -> List[str]:
        return super()._additional_keys() + ["name", "project", "Dummy"]

    @pydantic.validator("Dummy", pre=True)
    def _validate_dummy(cls, v):
        return v if v not in [None, ""] else False

    @staticmethod
    def _get_data_key(data: dict) -> str:
        if data and list(data.items()):
            _, struct_ = list(data.items())[0]
            name = list(struct_.keys())[0]
            return name
        return ""

    def __init__(self, *args, project: str = GLOBAL_KEY_PREFIX, **kwargs):
        LOGGER.warning(f"using new models, {self.scope}")
        if not kwargs:
            return
        version = DEFAULT_VERSION
        if "version" in kwargs:
            version = kwargs["version"]
        if list(kwargs.keys())[0] in valid_models:
            if list(kwargs.keys())[0] == self.scope:
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
                if "LastUpdate" not in struct_[name]:
                    struct_[name]["LastUpdate"] = {"date": "", "user": ""}
                super().__init__(**struct_[name], **params)
            else:
                raise ValueError(
                    f"wrong Data type, should be {self.scope}, instead got: {list(kwargs.keys())[0]}"
                )

    @property
    def scope(self):
        return self.__class__.__name__

    def schema_json(self):
        schema = json.loads(super().schema_json())
        [schema["properties"].pop(key) for key in self._additional_keys()]
        return schema

    def dict(self):
        dic = super().dict(exclude_none=True)
        [dic.pop(key) for key in self._additional_keys()]
        return {self.scope: {self.name: dic}}

    def has_scope_permission(self, user, permission) -> bool:
        if not user.has_permission(
            self.scope,
            "{prefix}.{permission}".format(prefix=self.name, permission=permission),
        ):
            if not user.has_permission(self.scope, permission):
                return False
        return True

    def has_permission(self, user, permission, app_name):
        """Override has_permission for the Scope Callback"""
        has_perm = self.has_scope_permission(user, permission)
        if not has_perm:
            # Check if user has the Callback on the authorized Applications Callbacks list.
            # If the user has authorization on the Application that is calling the callback, then authorize.
            if app_name in user.get_permissions("Applications"):
                ca = Application(name=app_name)
                if ca.Callbacks and self.name in ca.Callbacks:
                    has_perm = True

        return has_perm
