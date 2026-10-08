"""
Copyright (C) Mov.ai  - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential

Developers:
- Manuel Silva (manuel.silva@mov.ai) - 2020
- Tiago Paulino (tiago@mov.ai) - 2020

Attributes:
    SCOPES_TO_VALIDATE: List of scopes that will be validated before writing into redis.

"""
import re
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Dict, List, Optional, Set
from functools import cached_property
from movai_core_shared.exceptions import DoesNotExist, AlreadyExist
from .structures import Struct
from dal.movaidb import MovaiDB
from dal.movaidb.db_schema import DBSchema


SCOPES_TO_VALIDATE: List[str] = ["Translation", "Alert", "Node"]

# {(db, scope): {name: [keys]}} while Scope.batch_reads() is active
_KEYS_INDEX: ContextVar = ContextVar("scope_keys_index", default=None)


class Scope(Struct):
    """Scope main class.

    Attributes:
        validator (JsonValidator): Validator for the scope

    """

    permissions = ["create", "read", "update", "delete"]

    validator = None

    @classmethod
    def get_validator(cls):
        """Lazy-load validator only when actually needed.

        If a subclass defines its own validator, use that instead.
        """
        # Check if this specific class has its own validator
        if "validator" in cls.__dict__ and cls.__dict__["validator"] is not None:
            return cls.__dict__["validator"]

        # Otherwise, lazy-load the default validator
        if cls.validator is None:
            from dal.validation.validator import JsonValidator

            cls.validator = JsonValidator()
        return cls.validator

    def __init__(self, scope, name, version, new=False, db="global"):
        self.__dict__["name"] = name
        self.__dict__["scope"] = scope

        template_struct = DBSchema()[scope]

        # we then need to get this from database!!!!
        self.__dict__["struct"] = template_struct

        struct = dict()
        struct[name] = template_struct["$name"]
        super().__init__(scope, struct, {}, db)

        if new:
            if self.movaidb.exists_by_args(scope=scope, Name=name):
                raise AlreadyExist(
                    "%s %s already exists, to edit dont send the 'new' flag" % (scope, name)
                )
        else:
            index = Scope._scope_index(self.movaidb, db, scope)
            # not in the index may also mean created after its scope was indexed
            if (index is None or name not in index) and not self.movaidb.exists_by_args(
                scope=scope, Name=name
            ):
                raise DoesNotExist(
                    f"{name} does not exist yet. If you wish to create please use 'new=True'"
                )

    @staticmethod
    @contextmanager
    def batch_reads(index: Optional[dict] = None):
        """
        Read documents with fewer requests to Redis while this is active.

        While this is active, the keys of each scope are indexed
        with one KEYS when first needed: Scope then checks a document exists in that index,
        and get_dict() reads it with one MGET of its keys.

        Documents written while this is active may be read without their newest keys, so
        it should only wrap a short sequence of reads, like a validation.

        Args:
            index (dict): where to keep the index, to share it between reads that are not
                in the same block. A new one is used by default.
        """
        token = _KEYS_INDEX.set({} if index is None else index)
        try:
            yield
        finally:
            _KEYS_INDEX.reset(token)

    @staticmethod
    def names(scope: str, db: str = "global") -> Set[str]:
        """Return the names of all the documents of a scope."""
        movaidb = MovaiDB(db)
        index = Scope._scope_index(movaidb, db, scope)
        if index is not None:
            return set(index)

        return set(Scope._read_scope_keys(movaidb, scope))

    @staticmethod
    def _scope_index(movaidb: MovaiDB, db: str, scope: str) -> Optional[Dict[str, List[str]]]:
        """Return the keys of the documents of a scope while batch_reads() is active."""
        index = _KEYS_INDEX.get()
        if index is None:
            return None

        if (db, scope) not in index:
            index[(db, scope)] = Scope._read_scope_keys(movaidb, scope)
        return index[(db, scope)]

    @staticmethod
    def _read_scope_keys(movaidb: MovaiDB, scope: str) -> Dict[str, List[str]]:
        """Find the keys of the documents of a scope, by document name."""
        keys_by_name: Dict[str, Set[str]] = {}
        for key in movaidb.find_keys(f"{scope}:*"):
            # keys have the format <scope>:<name>,<attribute>...
            name = re.split("[:,]", key)[1]
            keys_by_name.setdefault(name, set()).add(key)

        # in the order MovaiDB.get reads them
        return {name: sorted(keys, key=str.lower) for name, keys in keys_by_name.items()}

    @cached_property
    def _movai_db_global(self):
        """Instantiates the global MovaiDB object, caching it."""
        return MovaiDB()

    def transform_before_update(self, source_data: dict):
        """
        Transforms data into internal format

        Args:
            source_data (dict): Data to transform.

        Default: do nothing.
        """
        return source_data

    def calc_scope_update(self, old_dict: dict, new_dict: dict):
        """Calc the objects differences and returns list with dict keys to delete/set.

        Args:
            old_dict (dict): Old scope dictionary.
            new_dict (dict): New scope dictionary.

        Raises:
            SchemaTypeNotKnown: If the scope is not known to the validator.
            ValueError: If the data does not conform to the schema.

        """
        self.validate_format(self.scope, new_dict)
        structure = self.__dict__.get("struct").get("$name")
        return self._movai_db_global.calc_scope_update(old_dict, new_dict, structure)

    def remove(self, force=True):
        """Removes Scope"""
        result = self.movaidb.unsafe_delete({self.scope: {self.name: "**"}})
        return result

    def remove_partial(self, dict_key):
        """Remove Scope key"""
        result = self.movaidb.unsafe_delete({self.scope: {self.name: dict_key}})
        return result

    def get_dict(self):
        """Returns the full dictionary of the scope from db"""
        index = Scope._scope_index(self.movaidb, self.db, self.scope)
        # the keys MovaiDB.get finds with the pattern <scope>:<name>,*
        prefix = f"{self.scope}:{self.name},"
        keys = [key for key in (index or {}).get(self.name, []) if key.startswith(prefix)]
        if keys:
            result = self.movaidb.get_from_keys(keys)
        else:
            result = self.movaidb.get({self.scope: {self.name: "**"}})
        attrs, lists, hashs = self.get_attributes(self.struct)
        for list_name in lists:
            if list_name not in result[self.scope][self.name]:
                result[self.scope][self.name][list_name] = []
        for hash_name in hashs:
            if hash_name not in result[self.scope][self.name]:
                result[self.scope][self.name][hash_name] = {}

        for attr in attrs:
            if attr not in result[self.scope][self.name]:
                result[self.scope][self.name][attr] = ""

        return result

    def has_scope_permission(self, user, permission) -> bool:
        if not user.has_permission(
            self.scope, "{prefix}.{permission}".format(prefix=self.name, permission=permission)
        ):
            if not user.has_permission(self.scope, permission):
                return False
        return True

    def get_value(self, key: str, default: any = False) -> any:
        try:
            value = self.__getattribute__(key)
        except AttributeError:
            value = default

        return value

    @classmethod
    def get_all(cls, db="global"):
        names_list = []
        try:
            for elem in MovaiDB(db).search_by_args(cls.scope, Name="*")[0][cls.scope]:
                names_list.append(elem)
        except KeyError:
            pass  # when does not exist
        return names_list

    @classmethod
    def _validate_content(cls, data: dict, name=""):
        """Validate scope data.

        Here we validate what cannot be validated by the JSON schema and requires custom logic.

        """

    @classmethod
    def validate_format(cls, scope, data: dict, name=""):
        """Check if the data is in a valid format for this scope.

        Raises:
            SchemaTypeNotKnown: If the scope is not known to the validator.
            ValueError: If the data does not conform to the schema.

        """
        if scope in SCOPES_TO_VALIDATE:
            cls.get_validator().validate(scope, data)
            cls._validate_content(data, name)
