"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2022
"""
import importlib
from typing import TYPE_CHECKING

from .constants import REDIS_SCHEMA_FOLDER_PATH, JSON_SCHEMA_FOLDER_PATH

# Import for type checking only - actual imports are lazy-loaded via __getattr__
if TYPE_CHECKING:
    from .schema import Schema
    from .template import Template
    from .validator import JsonValidator

_LAZY_IMPORTS = {
    "Schema": ".schema",
    "Template": ".template",
    "JsonValidator": ".validator",
}


def __getattr__(name):
    """Dynamically import classes on first access to reduce memory usage."""
    if name in _LAZY_IMPORTS:
        module = importlib.import_module(_LAZY_IMPORTS[name], package=__name__)
        attr = getattr(module, name)
        # Cache it in globals for faster subsequent access
        globals()[name] = attr
        return attr
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Schema",
    "JsonValidator",
    "Template",
    "REDIS_SCHEMA_FOLDER_PATH",
    "JSON_SCHEMA_FOLDER_PATH",
]
