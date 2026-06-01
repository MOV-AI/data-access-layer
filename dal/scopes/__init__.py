"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi  (moawiya@mov.ai) - 2022
"""
import importlib
from typing import TYPE_CHECKING

# Import for type checking only - actual imports are lazy-loaded via __getattr__
if TYPE_CHECKING:
    from .alert import Alert
    from .application import Application
    from .callback import Callback
    from .configuration import Config, Configuration
    from .fleetrobot import FleetRobot
    from .flow import Flow
    from .form import Form
    from .message import Message
    from .node import Node
    from .package import Package
    from .ports import Ports
    from .robot import Robot
    from .role import Role
    from .scope import Scope
    from .statemachine import SMVars, StateMachine
    from .structures import Struct
    from .system import System
    from .translation_constants import DEFAULT_LANGUAGE
    from .user import User
    from .widget import Widget
    from dal.utils import (
        DirectFlowUsageItem,
        DirectNodeUsageItem,
        FlowFlowUsage,
        IndirectFlowUsageItem,
        IndirectNodeUsageItem,
        NodeFlowUsage,
        UsageSearchResult,
        get_usage_search_scope_map,
    )

# Mapping of attribute names to their module paths
_LAZY_IMPORTS = {
    "Application": ".application",
    "Alert": ".alert",
    "Callback": ".callback",
    "Config": ".configuration",
    "Configuration": ".configuration",
    "FleetRobot": ".fleetrobot",
    "Flow": ".flow",
    "Form": ".form",
    "Message": ".message",
    "Node": ".node",
    "Package": ".package",
    "Ports": ".ports",
    "Robot": ".robot",
    "Role": ".role",
    "Scope": ".scope",
    "StateMachine": ".statemachine",
    "SMVars": ".statemachine",
    "Struct": ".structures",
    "System": ".system",
    "User": ".user",
    "Widget": ".widget",
    "DEFAULT_LANGUAGE": ".translation_constants",
    "UsageSearchResult": "dal.utils",
    "DirectNodeUsageItem": "dal.utils",
    "IndirectNodeUsageItem": "dal.utils",
    "DirectFlowUsageItem": "dal.utils",
    "IndirectFlowUsageItem": "dal.utils",
    "NodeFlowUsage": "dal.utils",
    "FlowFlowUsage": "dal.utils",
    "get_usage_search_scope_map": "dal.utils",
}


def __getattr__(name):
    """Dynamically import classes on first access to reduce memory usage."""
    if name in _LAZY_IMPORTS:
        module_path = _LAZY_IMPORTS[name]
        if module_path.startswith("."):
            module = importlib.import_module(module_path, package=__name__)
        else:
            module = importlib.import_module(module_path)
        attr = getattr(module, name)
        # Cache it in globals for faster subsequent access
        globals()[name] = attr
        return attr
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Application",
    "Callback",
    "Config",
    "Configuration",
    "DirectFlowUsageItem",
    "DirectNodeUsageItem",
    "FleetRobot",
    "Flow",
    "FlowFlowUsage",
    "Form",
    "IndirectFlowUsageItem",
    "IndirectNodeUsageItem",
    "Message",
    "Node",
    "NodeFlowUsage",
    "Package",
    "Ports",
    "Robot",
    "Role",
    "Scope",
    "StateMachine",
    "SMVars",
    "Struct",
    "System",
    "UsageSearchResult",
    "User",
    "Widget",
    "Alert",
    "DEFAULT_LANGUAGE",
    "get_usage_search_scope_map",
]

try:
    from movai_core_enterprise.scopes import (
        Annotation,
        GraphicScene,
        Layout,
        SharedDataEntry,
        SharedDataTemplate,
        Task,
        TaskEntry,
        TaskTemplate,
    )

    enterprise_modules = [
        "Annotation",
        "GraphicScene",
        "Layout",
        "SharedDataEntry",
        "SharedDataTemplate",
        "Task",
        "TaskEntry",
        "TaskTemplate",
    ]
except ImportError:
    enterprise_modules = []

__all__.extend(enterprise_modules)
