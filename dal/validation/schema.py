"""Copyright (C) Mov.ai  - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential

Developers:
- Moawiya Mograbi (moawiya@mov.ai) - 2022
"""

from json import loads as load_json
from os.path import dirname
from pathlib import Path

from referencing import Registry, Resource
from jsonschema import Draft202012Validator
from jsonschema import ValidationError

from dal.classes.filesystem import FileSystem


class Schema:
    def __init__(self, schema_path: str):
        self._path = schema_path
        content = FileSystem.read(schema_path)
        self._schema = load_json(content)
        self._version = Schema._get_schema_version(self._schema)

        # load base_schema manually
        # tried to use Registry(retrieve=retrieve_from_filesystem) but failed
        """
        def retrieve_from_filesystem(uri: str):
            path = Path(uri)
            contents = json.loads(path.read_text())
            return Resource.from_contents(contents)

        registry = Registry(retrieve=retrieve_from_filesystem).with_resource(
            f"file://{dirname(schema_path)}/",
            self._schema,
        )
        """
        common = "common/base.schema.json"
        registry = Registry().with_resource(
            "common/base.schema.json",
            Resource.from_contents(load_json(FileSystem.read(f"{dirname(schema_path)}/{common}"))),
        )
        self.validator = Draft202012Validator(
            self._schema,
            registry=registry,
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
            self.validator.validate(inst)
        except ValidationError as e:
            status = False
            path = "/" + "/".join(e.path)
            message = e.message
        except Exception as e:
            status = False
            message = str(e)

        return {"status": status, "message": message, "path": path}
