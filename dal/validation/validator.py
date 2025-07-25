"""
Copyright (C) Mov.ai  - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential

Developers:
- Moawiya Mograbi (moawiya@mov.ai) - 2022
"""

from os import listdir
from os.path import isdir
from re import search
import urllib
from typing import Dict

from .schema import Schema
from dal.exceptions import SchemaTypeNotKnown, SchemaVersionError
from .constants import SCHEMA_FOLDER_PATH


class JsonValidator:
    """Validator responsible to load schema json files and validate files according
    to it's type.

    """

    def __init__(self, version: str):
        self.schema_types: Dict[str, Schema] = {}
        self._version = version
        self._init_schemas()

    def _init_schemas(self):
        """Initialize schemas objects in the schema folder for all of our configuration files."""
        schema_folder = urllib.parse.urlparse(SCHEMA_FOLDER_PATH).path
        schema_version_folder = f"{schema_folder}/{self._version}"

        if not isdir(schema_version_folder):
            raise SchemaVersionError(f"Version folder {schema_version_folder} does not exist")

        for schema_json in listdir(schema_version_folder):
            m = search(r"(\w+)\.schema\.json", schema_json)
            if m is not None:
                schema_type = m.group(1)
                schema_path = f"{schema_version_folder}/{schema_json}"
                self.schema_types[schema_type] = Schema(schema_path)

    def validate(self, scope: str, data: dict):
        """Validate the content against the schema of the given scope.

        Args:
            scope (str): The type of the schema to validate against.
            data (dict): The data to validate.

        Raises:
            SchemaTypeNotKnown: If the scope is not known to the validator.
            ValueError: If the data does not conform to the schema.

        """
        if scope not in self.schema_types:
            raise SchemaTypeNotKnown(
                f"Type {scope} is not known to the validator: {self.schema_types}"
            )

        result = self.schema_types[scope].validate(data)
        if not result["status"]:
            raise ValueError(f"Invalid data for scope {scope}: {result['message']} for data {data}")
