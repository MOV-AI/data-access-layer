from typing import List, Optional, Union
import pydantic
import json
from .redis_model import RedisModel, GLOBAL_KEY_PREFIX
from .common import PrimaryKey
import re
from movai_core_shared.logger import Log
from .cache import ThreadSafeCache
from datetime import datetime


LOGGER = Log.get_logger("BaseModel.mov.ai")
DEFAULT_VERSION = "__UNVERSIONED__"
cache = ThreadSafeCache()


class LastUpdate(pydantic.BaseModel):
    date: datetime
    user: str = "movai"

    @pydantic.validator("date", pre=True, always=True)
    def _validate_date(cls, v):
        if not isinstance(v, str) or not v:
            return datetime.now().replace(microsecond=0)
        if "at" not in v:
            return datetime.strptime(v, "%d/%m/%Y %H:%M:%S")
        return datetime.strptime(v, "%d/%m/%Y at %H:%M:%S")

    def dict(
        self,
        *,
        include=None,
        exclude=None,
        by_alias: bool = False,
        skip_defaults: Optional[bool] = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = True,
    ) -> dict:
        return {"user": self.user, "date": self.date.strftime("%d/%m/%Y at %H:%M:%S")}


LABEL_REGEX = r"^[a-zA-Z0-9._-]+(/[a-zA-Z0-9._-]+){0,}$"
valid_models = [
    "Flow",
    "Node",
    "Callback",
    "Annotation",
    "GraphicScene",
    "Layout",
    "Application",
    "Configuration",
    "Ports",
]
path_regex = re.compile(r"([^\/]+)\/([^\/]+)\/(.*)")
label_regex = re.compile(LABEL_REGEX)


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
            # {workspace}/{scope}/{ref}/{version}
            m = path_regex.search(id)
            version = kwargs.get("version", DEFAULT_VERSION) if kwargs else DEFAULT_VERSION
            if m is not None:
                workspace = m.group(1)
                scope = m.group(2)
                id = m.group(3)
                if "/" in id:
                    id, version = id.split("/")
            else:
                scope = cls.__name__
            project = kwargs.get("project", GLOBAL_KEY_PREFIX) if kwargs else GLOBAL_KEY_PREFIX
            key = f"{project}:{scope}:{id}:{version}"
            if key in cache:
                return cache[key]

            obj = cls.select(ids=[f"{id}:{version}"])
            if not obj:
                raise Exception(f"{cls.__name__} {args[0]} not found!")
            return obj[0]
        return super().__new__(cls)

    @property
    def path(self):
        return f"global/{self.scope}/{self.name}/{self.Version}"

    @property
    def ref(self) -> str:
        return self.name

    def _original_keys(self) -> List[str]:
        return super()._original_keys() + ["Info", "Label", "Description", "LastUpdate", "Version"]

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
                if label_regex.search(name) is None:
                    raise ValueError(
                        f"Validation Error for {scope} name:({name}), data:{kwargs}"
                    )

                struct_[name]["Version"] = version
                if "LastUpdate" not in struct_[name]:
                    struct_[name]["LastUpdate"] = {"date": "", "user": ""}
                super().__init__(**struct_[name], **params)
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
        to_remove = []
        for key in schema["properties"]:
            if key not in self._original_keys():
                to_remove.append(key)
        [schema["properties"].pop(key) for key in to_remove]
        return schema

    def dict(
        self,
        *,
        include=None,
        exclude=None,
        by_alias: bool = True,
        skip_defaults: Optional[bool] = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = True,
    ):
        """Generate a dictionary representation of the model

        Returns:
            dict: dictionary representation of the model
        """
        dic = super().dict(
            exclude_none=exclude_none
        )
        to_remove = []
        for key in dic:
            if key not in self._original_keys():
                to_remove.append(key)
        dic = {key: value for key, value in dic.items() if key not in to_remove}
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
