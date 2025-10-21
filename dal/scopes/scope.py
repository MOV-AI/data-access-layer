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
from typing import List

from dal.validation.validator import Validator
from movai_core_shared.exceptions import DoesNotExist, AlreadyExist
from .structures import Struct
from dal.movaidb import MovaiDB
from dal.validation import JsonValidator


SCOPES_TO_VALIDATE: List[str] = ["Translation", "Alert"]


class Scope(Struct):
    """Scope main class.

    Attributes:
        validator (JsonValidator): Validator for the scope.

    """

    permissions = ["create", "read", "update", "delete"]

    validator: Validator = JsonValidator()

    def __init__(self, scope, name, version, new=False, db="global"):
        self.__dict__["name"] = name
        self.__dict__["scope"] = scope

        template_struct = MovaiDB.API()[scope]

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
            if not self.movaidb.exists_by_args(scope=scope, Name=name):
                raise DoesNotExist(
                    f"{name} does not exist yet. If you wish to create please use 'new=True'"
                )

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
        return MovaiDB().calc_scope_update(old_dict, new_dict, structure)

    def remove(self, force=True):
        """Removes Scope"""
        result = self.movaidb.unsafe_delete({self.scope: {self.name: "**"}})
        return result

    def remove_partial(self, dict_key):
        """Remove Scope key"""
        result = MovaiDB(self.db).unsafe_delete({self.scope: {self.name: dict_key}})
        return result

    def get_dict(self):
        """Returns the full dictionary of the scope from db"""
        result = MovaiDB(self.db).get({self.scope: {self.name: "**"}})
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
    def validate_format(cls, scope, data: dict):
        """Check if the data is in a valid format for this scope.

        Raises:
            SchemaTypeNotKnown: If the scope is not known to the validator.
            ValueError: If the data does not conform to the schema.

        """
        if scope in SCOPES_TO_VALIDATE:
            cls.validator.validate(scope, data)
