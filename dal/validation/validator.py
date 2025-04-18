"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2022
"""

from os import listdir
from os.path import dirname, realpath, isdir
from pathlib import Path
from re import search

from .schema import Schema
from json import loads as load_json
from dal.exceptions import SchemaTypeNotKnown, ValidationError, SchemaVersionError


class JsonValidator:
    """JsonValidator class
    responsible to load schema json files and validate files according
    to it's type.
    types: node/flow/callback/annotation/layout/graphicscene
    """

    def __init__(self, version: str):
        self.schema_types = []
        self._version = version
        self._init_schemas()

    def load_schema(self, schema_type: str, schema_path: str) -> bool:
        """load single schema in Validator class, check versions if bigger
           than existing one then replace it.

        Args:
            schema_type (str): schema type, node/flow/callback...
            schema_path (str): path of the schema file to be loaded

        Returns:
            bool: True if loaded successfully, otherwise False.
        """
        schema_type = schema_type.lower()
        schema_obj = Schema(schema_path)
        if schema_type in self.schema_types:
            # schema already loaded
            curr_schema: Schema = getattr(self, schema_type)
            if curr_schema.version > schema_obj.version:
                # TODO print or raise approperiate message
                return False
        else:
            self.schema_types.append(schema_type)
        setattr(self, schema_type, schema_obj)

        return True

    def _init_schemas(self):
        """will initialize schemas objects in the schema folder
        for all of our configuration files
        """
        # validator is in the root of validation module
        validation_path = dirname(realpath(__file__))

        schema_version_folder = f"{validation_path}/schema/{self._version}"
        if not isdir(schema_version_folder):
            raise SchemaVersionError(f"version {self._version} does not exist in schema folder")
        for schema_json in listdir(schema_version_folder):
            m = search(r"(\w+)\.schema\.json", schema_json)
            if m is not None:
                schema_type = m.group(1).lower()
                schema_path = f"{schema_version_folder}/{schema_json}"
                if not self.load_schema(schema_type, schema_path):
                    # loading failed
                    # TODO print approperiate message
                    pass

    def validate(self, file_path: Path, content=None) -> dict:
        """validate a local file path against it's matching schema

        Args:
            file_path (str): the local file path to be checked

        Returns:
            dict: a dictionary including a status about the validation
                  same as Schema.validate return value
                        - status: True if succeeded otherwise False
                        - message: error or success message
                        - path: the path of the error in case there is one
        """
        if file_path is not None:
            with file_path.open() as f:
                content = load_json(f.read())
        type = (list(content.keys())[0]).lower()
        if type not in self.schema_types:
            raise SchemaTypeNotKnown(f"type: {type}")
        schema_obj: Schema = getattr(self, type)

        """
        validation_res = schema_obj.validate(content)
        if validation_res["status"] is False:
            # validation Failed
            raise ValidationError(f"message:{validation_res['message']},\
                                path:{validation_res['path']}")
        """
        return schema_obj.validate(content)
