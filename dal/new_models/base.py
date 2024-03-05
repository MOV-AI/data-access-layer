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
from typing import List, Optional
from typing_extensions import Annotated

from pydantic import StringConstraints, field_validator, BaseModel, Field

from movai_core_shared.exceptions import AlreadyExist, DoesNotExist, InvalidStructure
from movai_core_shared.logger import Log

from .base_model.redis_model import CACHE, RedisModel
from .base_model.common import MovaiPrimaryKey, DEFAULT_DB, DEFAULT_VERSION


class LastUpdated(BaseModel):
    """A field represent the last time object was updated."""

    date: datetime = Field(default_factory=lambda: datetime.now())
    user: str = ""

    @field_validator("date", mode="before")
    @classmethod
    def _validate_date(cls, v):
        """Valdation function.

        Args:
            v (datetime): the current time and date.

        Returns:
            datetime: A validated time and date.
        """
        if isinstance(v, datetime):
            return v.replace(microsecond=0)
        if not isinstance(v, str) or not v or v == "N/A":
            return datetime.now().replace(microsecond=0)
        if "at" not in v:
            return datetime.strptime(v, "%d/%m/%Y %H:%M:%S")
        return datetime.strptime(v, "%d/%m/%Y at %H:%M:%S")

    def update(self):
        """Updates the date and time to now."""
        self.date = datetime.now().replace(microsecond=0)


LABEL_REGEX = r"^[a-zA-Z 0-9._-]*(/[a-zA-Z0-9._-]+){0,}$"
path_regex = re.compile(r"([^\/]+)\/([^\/]+)\/(.*)")
label_regex = re.compile(LABEL_REGEX)


class MovaiBaseModel(RedisModel):
    """A base class for all MOV.AI models."""

    Info: Optional[str] = None
    Label: Annotated[str, StringConstraints(pattern=LABEL_REGEX)] = ""
    Description: Optional[str] = ""
    LastUpdate: Optional[LastUpdated]
    name: Annotated[str, StringConstraints(pattern=LABEL_REGEX)] = ""
    Dummy: Optional[bool] = False

    @field_validator("LastUpdate", mode="before")
    @classmethod
    def _validate_lastupdate(cls, value):
        if value is None or isinstance(value, str):
            return LastUpdated(**{})
        return value

    def __init__(self, *args, db: str = DEFAULT_DB, version: str = DEFAULT_VERSION, **kwargs):
        """Initialize or create a new pydantic object. if given args assumes that it needs to initailize
        an existing object while the first argument wil be the object's name.
        if given kwargs assumes a new object should be created and ignore args.

        Args:
            db (str, optional): Specify which db the object will be stored. Defaults to DEFAULT_DB.
            version (str, optional): Specifies the version of the object. Defaults to DEFAULT_VERSION.

        Raises:
            ValueError: In case args weren't given to load an object.
        """
        if not args and kwargs:
            obj_dict = self._create_object_dict(db, version, kwargs)
            super().__init__(**obj_dict)
        else:
            if not args:
                raise ValueError("Object's name must be provided inorder to initialize object.")
            obj_name = args[0]
            obj_dict = self._fetch_object_dict(db, version, obj_name)
            super().__init__(**obj_dict)

    def _create_object_dict(self, db: str, version: str, obj_dict: dict) -> dict:
        """Creates a dictionary that can initialize an object in the OM (object mapping).

        Args:
            db (str): The db to store the object, global or local.
            version (str): The version of the object.
            obj_dict (dict): The initial dictionary with the object's data.

        Raises:
            InvalidStructure: In case the initial dict doesn't contain the model name.
            ValueError: In case the model name is different than the class.
            AlreadyExist: In case this object aleady exist in the required db.

        Returns:
            dict:  A dictionary represent the object's structure.
        """
        if self.model not in obj_dict:
            raise InvalidStructure(f"The supplied dict is invalid for model: {self.model}")

        model = next(iter(obj_dict))

        if model != self.model:
            raise ValueError(
                f"wrong Data type, should be {self.model}, recieved: {model}, instead got: {list(obj_dict.keys())[0]}"
            )

        obj_dict = obj_dict[model]
        name = next(iter(obj_dict))
        obj_dict = obj_dict[name]
        version = obj_dict.get("Version", version)
        pk = MovaiPrimaryKey(db=db, model=model, name=name, version=version)
        if pk.pk in self.get_model_keys(db, version):
            raise AlreadyExist(f"The key: {pk.pk} is already exist!")
        obj_dict["pk"] = pk.pk
        if "name" not in obj_dict:
            obj_dict["name"] = name
        if "LastUpdate" not in obj_dict:
            obj_dict["LastUpdate"] = {}
        CACHE[pk.pk] = obj_dict
        return obj_dict

    def _fetch_object_dict(self, db: str, version: str, name: str) -> dict:
        """Fetch a dictionary of an object from the db.

        Args:
            db (str): global or local db.
            version (str): The version of the object to fetch.
            name (str): The name of the object to fetch.

        Raises:
            DoesNotExist: In case the the object could not be found.

        Returns:
            dict: A dictionary representing the object's structure.
        """
        if name.count("/") == 3:
            db, model, name, version = name.split("/")
        else:
            model = self.model

        pk = MovaiPrimaryKey(db=db, model=model, name=name, version=version)

        if pk.pk in CACHE:
            model_dict = CACHE[pk.pk]
            return model_dict

        obj_dict = self.db_handler(db).json().get(pk.pk)
        if not obj_dict:
            raise DoesNotExist(f"The key {pk.pk} does not exist!")
        obj_dict = obj_dict[self.model][name]
        obj_dict["name"] = name
        obj_dict["pk"] = pk.pk
        CACHE[pk.pk] = obj_dict
        return obj_dict

    def save(self, db=DEFAULT_DB, version=DEFAULT_VERSION) -> None:
        """Saves the object to the DB.

        Args:
           db (str, optional): specifies which DB to save the object. Defaults to "global".
           version (_type_, optional): What is the version of the object. Defaults to None.

        Returns:
            str: _description_
        """
        self.LastUpdate.update()
        super().save(db=db, version=version)

    @property
    def path(self) -> str:
        """The path of the object in the db.

        Returns:
            str: a string representing the path.
        """
        return f"{self.db}/{self.model}/{self.name}/{self.Version}"

    @property
    def ref(self) -> str:
        """A property representing object name, added for backward compatiblity.

        Returns:
            str: The objects name.
        """
        return self.name

    @classmethod
    def _original_keys(cls) -> List[str]:
        """keys that are originally defined part of the model

        Returns:
            List[str]: list including the original keys
        """
        return super()._original_keys() + ["Info", "Label", "Description", "LastUpdate", "Version"]

    @field_validator("Dummy", mode="before")
    @classmethod
    def _validate_dummy(cls, v):
        return v if v not in [None, ""] else False

    @property
    def model(self) -> str:
        """return the model of the model (Class name)

        Returns:
            str: model of the model
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

    def model_dump(
        self,
        *,
        include=None,
        exclude=None,
        by_alias: bool = True,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = True,
        round_trip: bool = False,
        warnings: bool = False
    ):
        """Generate a dictionary representation of the model

        Returns:
            dict: dictionary representation of the model
        """
        obj_dict = super().model_dump(include=include,
                                      exclude=exclude,
                                      by_alias=by_alias,
                                      exclude_unset=exclude_unset,
                                      exclude_defaults=exclude_defaults,
                                      exclude_none=exclude_none,
                                      round_trip=round_trip,
                                      warnings=warnings)

        if "LastUpdate" in obj_dict and isinstance(obj_dict["LastUpdate"]["date"], datetime):
            obj_dict["LastUpdate"]["date"] = obj_dict["LastUpdate"]["date"].strftime("%d/%m/%Y at %H:%M:%S")
#        to_remove = []
#        for key in obj_dict:
#            if key not in self._original_keys():
#                to_remove.append(key)
        obj_dict = {key: value for key, value in obj_dict.items() if key in self._original_keys()}
        return {self.model: {self.name: obj_dict}}

    def has_scope_permission(self, user, permission) -> bool:
        """Check if user has permission on the model

        Args:
            user (_type_): _description_
            permission (_type_): type of the permission

        Returns:
            bool: True if user has permission, False otherwise
        """
        if not user.has_permission(
            self.model,
            f"{self.name}.{permission}",
        ) and not user.has_permission(self.model, permission):
            return False
        return True

    def has_permission(self, user, permission, app_name):
        """Override has_permission for the Scope Callback"""
        has_perm = self.has_scope_permission(user, permission)
        if not has_perm:
            # Check if user has the Callback on the authorized Applications Callbacks list.
            # If the user has authorization on the Application that is calling the callback, then authorize.
            if app_name in user.get_permissions("Applications"):
                from dal.scopes.application import Application
                ca = Application(app_name)
                if ca.Callbacks and self.name in ca.Callbacks:
                    has_perm = True
        return has_perm
