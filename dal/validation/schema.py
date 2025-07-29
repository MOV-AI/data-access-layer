"""Copyright (C) Mov.ai  - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential

Developers:
- Moawiya Mograbi (moawiya@mov.ai) - 2022
"""

from pathlib import Path
from typing import TypedDict

from referencing import Registry, Resource
from jsonschema import Draft202012Validator
from jsonschema import ValidationError

from dal.classes.filesystem import FileSystem


class ValidationResult(TypedDict):
    status: bool
    message: str


class Schema:
    def __init__(self, schema_path: Path):
        self._path: Path = schema_path

        def retrieve_from_filesystem(uri: str):
            """Retrieve a referenced schema from the filesystem.

            Args:
                uri (str): The URI of the schema to retrieve.
                    Must be a relative path from main schema directory.

            Returns:
                Resource: A Resource object containing the schema contents.

            """
            path = self._path.parent / uri
            print(path)
            contents = FileSystem.read_json(path)
            return Resource.from_contents(contents)

        # registry with the ability to retrieve schemas from the filesystem
        registry = Registry(retrieve=retrieve_from_filesystem)

        # load main schema into the validator
        self.validator = Draft202012Validator(
            FileSystem.read_json(self._path),
            registry=registry,
        )

    def validate(self, data: dict) -> ValidationResult:
        """Validate data against the schema.

        Args:
            data (dict): The data to be validated.

        Returns:
            ValidationResult: Validation results.

        """
        status = True
        message = ""
        try:
            self.validator.validate(data)
        except ValidationError as e:
            status = False
            message = f"Data schema violation: {e.message}"
        except Exception as e:
            status = False
            message = str(e)

        return ValidationResult(status=status, message=message)
