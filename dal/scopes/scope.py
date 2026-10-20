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
import json
import os
from typing import List
from functools import cached_property
from dal import scopes
from dal.utils.project_metadata import ProjectSource, from_path
from movai_core_shared.exceptions import DoesNotExist, AlreadyExist, ExportException
from .structures import Struct
from dal.movaidb import MovaiDB
from dal.movaidb.db_schema import DBSchema
from movai_core_shared.logger import Log

LOGGER = Log.get_logger(__name__)

SCOPES_TO_VALIDATE: List[str] = ["Translation", "Alert", "Node"]


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
            if not self.movaidb.exists_by_args(scope=scope, Name=name):
                raise DoesNotExist(
                    f"{name} does not exist yet. If you wish to create please use 'new=True'"
                )

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

    @staticmethod
    def get_class(scope):
        """Retrieve a scope class by its name.

        Args:
            scope (str): Name of the scope class to retrieve.

        Returns:
            type: The class associated with the specified scope.

        Raises:
            DoesNotExist: If the specified scope does not exist.
        """
        try:
            return getattr(scopes, scope)
        except AttributeError as exc:
            raise DoesNotExist(f"Scope does not exist: {scope}") from exc

    @classmethod
    def _import_dependencies(cls, data: dict, source: ProjectSource):
        """Import dependencies associated with the provided metadata.

        This is a default implementation that does not import any dependencies.
        Subclasses can override this method to handle scope-specific dependencies.

        Args:
            data (dict): Metadata of the object being imported.
            source (ProjectSource): Source from which dependencies are imported.

        Returns:
            list: Imported dependency results.
        """
        return []

    @classmethod
    def _get_metadata(cls, json_data: dict, scope_name: str, name: str) -> dict:
        """Retrieve metadata for a specific object from its JSON representation.

        Args:
            json_data (dict): Parsed JSON data containing scope metadata.
            scope_name (str): Name of the scope containing the object.
            name (str): Name of the object whose metadata is retrieved.

        Returns:
            dict: Metadata associated with the specified object.

        Raises:
            KeyError: If the scope or object name does not exist in the JSON data.
        """
        return json_data[scope_name][name]

    @classmethod
    def _update_metadata(cls, data: dict, file_path: str, source: ProjectSource) -> dict:
        """Update metadata before importing it.

        This is a default implementation that returns the metadata unchanged.
        Subclasses can override this method to perform scope-specific updates.

        Args:
            data (dict): Metadata to update.
            file_path (str): Path to the metadata file.
            source (ProjectSource): Source containing the metadata.

        Returns:
            dict: Updated metadata.
        """
        return data

    @classmethod
    def import_metadata(cls, names, source: ProjectSource, recursive=False):
        """Import metadata for the specified objects.

        Reads metadata files from the provided source, extracts the relevant
        object metadata, optionally imports dependencies, and applies
        scope-specific metadata updates.

        Args:
            names: Names of the objects to import.
            source (ProjectSource): Source from which metadata is imported.
            recursive (bool, optional): Whether to import object dependencies.
                Defaults to False.

        Returns:
            list: A list of tuples containing the object name, JSON metadata,
            and metadata file path.
        """
        ret = []
        scope_name = cls.__name__

        files = source.get_files(scope_name, names)
        for name, file_path in files:
            json_data = source._read_json(file_path)
            data = cls._get_metadata(json_data, scope_name, name)

            if recursive:
                ret += cls._import_dependencies(data, source)

            data = cls._update_metadata(data, file_path, source)

            ret.append((name, json_data, file_path, None))
        return ret

    @classmethod
    def _export_extra_files(cls, scope, name: str):
        """Collect additional files associated with an object for export.

        This is a default implementation that returns no additional files.
        Subclasses can override this method to include scope-specific files.

        Args:
            scope: Object whose additional files are being exported.
            name (str): Name of the object being exported.

        Returns:
            dict: A mapping of relative file paths to file contents.
        """
        return {}

    @classmethod
    def _export_dependencies(cls, scope):
        """Collect dependencies associated with an object for export.

        This is a default implementation that returns no dependencies.
        Subclasses can override this method to export scope-specific dependencies.

        Args:
            scope: Object whose dependencies are being exported.

        Returns:
            dict: A mapping of relative file paths to serialized file contents.
        """
        return {}

    @classmethod
    def clean_data(cls, data):
        """Remove internal fields and serialize metadata to formatted JSON.

        Removes fields that should not be included in exported JSON. Handles
        the deprecated Dummy field by setting Remappable and Launch to False
        when Dummy is True.

        Args:
            data (dict): Metadata dictionary to clean and serialize.

        Returns:
            str: JSON-formatted metadata with sorted keys and four-space indentation.

        Note:
            The input dictionary is modified in place.
        """
        b = data
        for _ in range(2):
            b = next(iter(b.values()))

        for key in (
            "_schema_version",
            "relations",
            "InstallPath",
            "Code",
            "Yaml",
            "Translations",
        ):
            b.pop(key, None)

        # Keep compatibility with the deprecated Dummy field.
        if b.pop("Dummy", None) is True:
            b["Remappable"] = False
            b["Launch"] = False

        return json.dumps(data, sort_keys=True, indent=4)

    @classmethod
    def export_metadata(cls, names, recursive=False):
        """Export metadata and associated files for the specified objects.

        Instantiates each object, collects its additional files, optionally
        exports its dependencies, and serializes its metadata to JSON.

        Args:
            names (iterable[str]): Names or paths of the objects to export.
            recursive (bool, optional): Whether to export object dependencies.
                Defaults to False.

        Returns:
            dict: A mapping of relative file paths to serialized file contents.

        Raises:
            ExportException: If an object cannot be found or instantiated.

        Note:
            Object names are normalized using from_path() before export.
            Duplicate JSON paths are skipped.
        """
        ret = {}
        scope_name = cls.__name__

        for name in names:
            name = from_path(name)

            json_path = os.path.join(scope_name, f"{name}.json")
            if json_path in ret:
                continue

            try:
                obj = cls(name)  # pylint: disable=no-value-for-parameter
            except Exception as e:
                raise ExportException(f"Can't find {scope_name}:{name} - (Exc: {e})")

            ret.update(cls._export_extra_files(obj, name))

            if recursive:
                ret.update(cls._export_dependencies(obj))

            data = cls.clean_data(obj.get_dict())

            ret[json_path] = data
        return ret
