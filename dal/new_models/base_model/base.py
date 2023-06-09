from typing import List, Optional, Union
import pydantic
import json
from .redis_model import RedisModel, GLOBAL_KEY_PREFIX
from .common import PrimaryKey
from re import search
from movai_core_shared.logger import Log
from .cache import ThreadSafeCache


LOGGER = Log.get_logger("BaseModel.mov.ai")
DEFAULT_VERSION = "__UNVERSIONED__"


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
    def _validate_last_update(cls, v) -> LastUpdate:
        """validate last update field

        Args:
            v (str/dict): last update field

        Returns:
            LastUpdate: LastUpdate Model
        """
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
            cache = ThreadSafeCache()
            if key in cache:
                return cache[key]

            obj = cls.select(ids=[f"{id}:{version}"])
            if not obj:
                raise Exception(f"{cls.__name__} {args[0]} not found!")
            return obj[0]
        return super().__new__(cls)

    def _additional_keys(self) -> List[str]:
        """additional keys to be removed from the dictionary representation of the model
        used only for innear use

        Returns:
            List[str]: list of keys
        """
        return super()._additional_keys() + ["name", "project", "Dummy"]

    @pydantic.validator("Dummy", pre=True)
    def _validate_dummy(cls, v):
        return v if v not in [None, ""] else False

    def __init__(self, *args, project: str = GLOBAL_KEY_PREFIX, **kwargs):
        if not kwargs:
            return
        version = DEFAULT_VERSION
        if "version" in kwargs:
            version = kwargs["version"]
        scope = next(iter(kwargs))
        if scope in valid_models:
            if scope == self.scope:
                struct_ = kwargs[scope]
                name = next(iter(struct_))
                params = {"name": name, "project": project}
                if "pk" not in struct_[name]:
                    pk = PrimaryKey.create_pk(
                        project=project, scope=self.scope, id=name, version=version
                    )
                    params.update({"pk": pk})
                if search(LABEL_REGEX, name) is None:
                    raise ValueError(
                        f"Validation Error for {scope} name:({name}), data:{kwargs}"
                    )

                struct_[name]["Version"] = version
                if "LastUpdate" not in struct_[name]:
                    struct_[name]["LastUpdate"] = {"date": "", "user": ""}
                super().__init__(**struct_[name], **params)
                cache = ThreadSafeCache()
                cache[pk] = self
            else:
                raise ValueError(
                    f"wrong Data type, should be {self.scope}, recieved: {scope}, instead got: {list(kwargs.keys())[0]}"
                )
        else:
            raise ValueError(
                f"scope not supported ({scope}), should be one of {valid_models}"
            )

    @property
    def scope(self) -> str:
        """return the scope of the model (Class name)

        Returns:
            str: scope of the model
        """
        return self.__class__.__name__

    def schema_json(self) -> dict:
        """Generate a JSON Schema for the model

        Returns:
            dict: JSON Schema
        """
        schema = json.loads(super().schema_json(by_alias=True))
        [schema["properties"].pop(key) for key in self._additional_keys()]
        return schema

    def dict(self) -> dict:
        """Generate a dictionary representation of the model

        Returns:
            dict: dictionary representation of the model
        """
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
