"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2022
"""

from .schema import Schema
from .validator import JsonValidator
from .template import Template
from os.path import dirname, realpath, isdir


dir = dirname(realpath(__file__))
SCHEMA_FOLDER_PATH = f"file:/{dir}/schema"


def get_schema_folder(version):
    if isdir(f"{dir}/schema/{version}"):
        return f"file:/{dir}/schema/{version}"
    raise Exception(f"schema version {version} does not exist")


__all__ = [
    "Schema",
    "JsonValidator",
    "Template",
    "SCHEMA_FOLDER_PATH",
    "get_schema_folder"
]
