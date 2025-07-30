"""
Copyright (C) Mov.ai  - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential

Developers:
- Moawiya Mograbi (moawiya@mov.ai) - 2022
"""

from re import search
import urllib
from typing import Dict
from pathlib import Path

from .schema import Schema
from dal.exceptions import SchemaTypeNotKnown, SchemaVersionError
from .constants import SCHEMA_FOLDER_PATH
from dal.classes.common.singleton import Singleton


class JsonValidator(metaclass=Singleton):
    """Validator responsible to load schema json files and validate files according
    to it's type.

    """

    VERSION = "2.4"

    def __init__(self):
        self.schema_types: Dict[str, Schema] = {}
        self._init_schemas()

    def _init_schemas(self):
        """Initialize schemas objects in the schema folder for all of our configuration files."""
        schema_folder = Path(
            urllib.parse.urlparse(SCHEMA_FOLDER_PATH).path
        )  # remove 'file://' prefix
        version_folder = schema_folder / self.VERSION

        if not version_folder.exists():
            raise SchemaVersionError(f"Version folder {version_folder} does not exist")

        for schema_json in version_folder.iterdir():
            m = search(r"(\w+)\.schema\.json", schema_json.name)
            if m is not None:
                schema_type = m.group(1)
                self.schema_types[schema_type] = Schema(schema_json)

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
