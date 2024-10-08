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
from os.path import dirname, realpath


dir = dirname(realpath(__file__))
SCHEMA_FOLDER_PATH = f"file://{dir}/schema"
default_version = "2.3"


__all__ = [
    "Schema",
    "JsonValidator",
    "Template",
    "SCHEMA_FOLDER_PATH",
    "default_version"
]
