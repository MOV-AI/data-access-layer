"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi  (moawiya@mov.ai) - 2022
"""
try:
    from movai_core_enterprise.scopes import (
        Layout,
        GraphicAsset,
        SharedDataEntry,
        SharedDataTemplate,
        TaskTemplate,
        Annotation
    )
    enterprise_modules = [
        "Annotation",
        "SharedDataEntry",
        "SharedDataTemplate",
        "Layout",
        "TaskTemplate",
        "GraphicAsset",
    ]
except ImportError:
    enterprise_modules = []

from dal.helpers import Helpers
from backend.endpoints.api.v1.models.user import User
from dal.scopes import (
    Widget,
    Form,
    System,
    Ports,
    List,
    Hash,
    Scope,
    Struct
)

modules = [
    "Application",
    "Form",
    "List",
    "Hash",
    "Helpers",
    "Scope",
    "Struct",
    "User",
    "Widget",
    "System",
    "Ports",
]
modules.extend(enterprise_modules)
__all__ = modules
