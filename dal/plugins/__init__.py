"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi  (Moawiya@mov.ai) - 2022
"""
from .resources.file import FilePlugin

from .resource import (
    Resource, Plugin, PluginManager, ResourceException, ResourcePlugin
)

__all__ = [
    "Resource",
    "Plugin",
    "PluginManager",
    "ResourceException",
    "ResourcePlugin"
]
