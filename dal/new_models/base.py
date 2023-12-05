"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2023
   - Erez Zomer (erez@mov.ai) - 2023
"""
from datetime import datetime
import json
import re
from typing import List, Optional, Union
from typing_extensions import Annotated

from pydantic import field_validator
from redis_om import JsonModel, EmbeddedJsonModel

from movai_core_shared.exceptions import DoesNotExist
from movai_core_shared.logger import Log

from .base_model.cache import ThreadSafeCache
from .base_model.redis_model import DEFAULT_PROJECT
from .base_model.common import PrimaryKey, DEFAULT_VERSION


LOGGER = Log.get_logger("BaseModel.mov.ai")
cache = ThreadSafeCache()


class LastUpdate(EmbeddedJsonModel):
    """A class for implementing the lastupdate field."""
    date: datetime
    user: str = "movai"

    @field_validator("date", mode="before")
    def _validate_date(cls, value) -> datetime:
        """a method for validating the date.

        Args:
            value (datetime): a datetime value.

        Returns:
            datetime: the supplied date.
        """
        if not isinstance(value, str) or not value or value == "N/A":
            return datetime.now().replace(microsecond=0)
        if "at" not in value:
            return datetime.strptime(value, "%d/%m/%Y %H:%M:%S")
        return datetime.strptime(value, "%d/%m/%Y at %H:%M:%S")

    def update(self):
        """Updates the object current date."""
        self.date = datetime.now().replace(microsecond=0)


LABEL_REGEX = r"^[a-zA-Z 0-9._-]*(/[a-zA-Z0-9._-]+){0,}$"
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


class MovaiBaseModel(JsonModel):
    """The basic movai model."""
    Info: Optional[str] = None
    #Label: Annotated[str, StringConstraints(pattern=LABEL_REGEX)] = ""
    Label: str
    Description: Optional[str] = None
    LastUpdate: Union[LastUpdate, str]    
    name: str = ""
    Dummy: Optional[bool] = False

    @field_validator("LastUpdate", mode="before")
    def _validate_last_update(cls, value) -> LastUpdate:
        """validate last update field

        Args:
            value (str/dict): last update field

        Returns:
            LastUpdate: LastUpdate Model
        """
        if value is None or isinstance(value, str):
            # TODO: changed default values.
            return LastUpdate(date="", user="")
        return LastUpdate(**value)

    def __new__(cls, *args, **kwargs):
        if args:
            id = args[0]
            # support for old format
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
            project = kwargs.get("project", DEFAULT_PROJECT) if kwargs else DEFAULT_PROJECT
            db = kwargs.get("db", "global") if kwargs else "global"
            key = PrimaryKey.create_pk(
                        project=project, scope=scope, id=id, version=version
                    )
            cache_key = f"{db}::{key}"
            if cache_key in cache:
                return cache[cache_key]

            obj = cls.find(ids=[id], version=version, project=project, db=db)
            if not obj:
                raise DoesNotExist(f"{cls.__name__} {args[0]} not found in DB {db}!")
            return obj[0]
        return super().__new__(cls)

    def save(self, db="global", version=None, project=None, save_to_file=None) -> str:
        self.LastUpdate.update()
        super().save()
        super().save(db=db, version=version, project=project, save_to_file=save_to_file)

    @property
    def path(self):
        return f"global/{self.scope}/{self.name}/{self.Version}"

    @property
    def ref(self) -> str:
        return self.name

    @classmethod
    def _original_keys(cls) -> List[str]:
        """keys that are originally defined part of the model

        Returns:
            List[str]: list including the original keys
        """
        return super()._original_keys() + ["Info", "Label", "Description", "LastUpdate", "Version"]

    @field_validator("Dummy", mode="before")
    def _validate_dummy(cls, value):
        return value if value not in [None, ""] else False

    def __init__(self, *args, project: str = DEFAULT_PROJECT, db: str = "global", **kwargs):
        if not kwargs or self.scope not in kwargs:
            return
        version = DEFAULT_VERSION
        if "version" in kwargs:
            version = kwargs["version"]
        scope = next(iter(kwargs))
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
                raise ValueError(f"Validation Error for {scope} name:({name}), data:{kwargs}")

            struct_[name]["Version"] = version
            if "LastUpdate" not in struct_[name]:
                struct_[name]["LastUpdate"] = {"date": "", "user": ""}
            super().__init__(**struct_[name], **params)
            cache_key = f"{db}::{self.pk}"
            cache[cache_key] = self
        else:
            raise ValueError(
                f"wrong Data type, should be {self.scope}, recieved: {scope}, instead got: {list(kwargs.keys())[0]}"
            )

    @property
    def scope(self) -> str:
        """return the scope of the model (Class name)

        Returns:
            str: scope of the model
        """
        return self.__class__.__name__

    @classmethod
    def json_schema(cls) -> dict:
        """Generate a JSON Schema for the model

        Returns:
            dict: JSON Schema
        """
        schema = json.loads(cls.model_json_schema(by_alias=True))
        to_remove = []
        for key in schema["properties"]:
            if key not in cls._original_keys():
                to_remove.append(key)
        [schema["properties"].pop(key) for key in to_remove]
        return schema

    def _fix_flow_links(self):
        """will fix flow links to use strings instead of objects

        Returns:
            _type_: _description_
        """
        if self.scope != "Flow":
            return None
        dic = super().model_dump(exclude_none=True, by_alias=True)
        for id, link in self.Links.items():
            dic["Links"][id]["From"] = link.From.str
            dic["Links"][id]["To"] = link.To.str

        return dic

    def model_dump(
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
        if self.scope == "Flow":
            """somehow the model_dump in pydantic v2 does not take into consideration the
               overriden model_dump in inner classes, so we need to call it explicitly here.
            """
            dic = self._fix_flow_links()
        else:
            dic = super().model_dump(exclude_none=exclude_none, by_alias=True)
        if "LastUpdate" in dic and isinstance(dic["LastUpdate"]["date"], datetime):
            dic["LastUpdate"]["date"] = dic["LastUpdate"]["date"].strftime("%d/%m/%Y at %H:%M:%S")
        to_remove = []
        for key in dic:
            if key not in self._original_keys():
                to_remove.append(key)
        dic = {key: value for key, value in dic.items() if key not in to_remove}
        return {self.scope: {self.name: dic}}

    def has_scope_permission(self, user, permission) -> bool:
        """Check if user has permission on the scope

        Args:
            user (_type_): _description_
            permission (_type_): type of the permission

        Returns:
            bool: True if user has permission, False otherwise
        """
        if not user.has_permission(
            self.scope,
            f"{self.name}.{permission}",
        ) and not user.has_permission(self.scope, permission):
            return False
        return True

    def has_permission(self, user, permission, app_name):
        """Override has_permission for the Scope Callback"""
        has_perm = self.has_scope_permission(user, permission)
        if not has_perm:
            # Check if user has the Callback on the authorized Applications Callbacks list.
            # If the user has authorization on the Application that is calling the callback, then authorize.
            if app_name in user.get_permissions("Applications"):
                from .application import Application
                ca = Application(app_name)
                if ca.Callbacks and self.name in ca.Callbacks:
                    has_perm = True
        return has_perm
