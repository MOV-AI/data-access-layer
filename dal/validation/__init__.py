"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2022
"""
from typing import TYPE_CHECKING

from .constants import REDIS_SCHEMA_FOLDER_PATH, JSON_SCHEMA_FOLDER_PATH

# Import for type checking only - actual imports are lazy-loaded via __getattr__
if TYPE_CHECKING:
    from .schema import Schema
    from .template import Template
    from .validator import JsonValidator


def __getattr__(name):
    """Lazy-load validation classes to avoid loading jsonschema unless actually needed."""
    if name == "Schema":
        from .schema import Schema

        return Schema
    elif name == "JsonValidator":
        from .validator import JsonValidator

        return JsonValidator
    elif name == "Template":
        from .template import Template

        return Template
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Schema",
    "JsonValidator",
    "Template",
    "REDIS_SCHEMA_FOLDER_PATH",
    "JSON_SCHEMA_FOLDER_PATH",
]
