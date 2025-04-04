"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2022
"""

from jsonschema import RefResolver
from jsonschema import validate as json_validate
from jsonschema.exceptions import ValidationError
from json import loads as load_json
from os.path import abspath, dirname
from dal.classes.filesystem import FileSystem
from dal.exceptions import SchemaVersionError


class Schema:
    def __init__(self, schema_path: str):
        self._path = schema_path
        content = FileSystem.read(schema_path)
        self._schema = load_json(content)
        self._version = Schema._get_schema_version(self._schema)
        full_path = abspath(schema_path)
        self._resolver = RefResolver(
            base_uri=f"file://{dirname(full_path)}/", referrer=self._schema
        )

    @staticmethod
    def _get_schema_version(schema_obj) -> float:
        """will exctract the schema version from it.

        Args:
            schema_obj (dict): the schema dictionary object

        Raises:
            SchemaVersionError: in case there was a problem with the version

        Returns:
            float: the version in float
        """
        version = schema_obj["$version"]
        return float(version)

    @property
    def version(self):
        return self._version

    def validate(self, inst: dict) -> dict:
        """validate the schema class against given dictionary

        Args:
            inst (dict): the dictionary that need to be validated.

        Returns:
            dict: a dictionary including status/error and a message.
                    - status: True if succeeded otherwise False
                    - message: error or success message
                    - path: the path of the error in case there is one
        """
        status = True
        message = ""
        path = ""
        try:
            json_validate(instance=inst, schema=self._schema, resolver=self._resolver)
        except ValidationError as e:
            status = False
            path = "/" + "/".join(e.path)
            message = e.message
        except Exception as e:
            status = False
            message = str(e)

        return {"status": status, "message": message, "path": path}
