"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi  (moawiya@mov.ai) - 2022
"""
import importlib
from typing import TYPE_CHECKING

# Eagerly import critical base classes and singletons to avoid initialization issues
from .model import Model
from .node import Node
from .nodeinst import NodeInst
from .container import Container
from .flow import Flow
from .flowlinks import FlowLinks
from .scopestree import (
    scopes,
    ScopeInstanceVersionNode,
    ScopePropertyNode,
    ScopeNode,
    ScopeObjectNode,
    ScopesTree,
)

# Import for type checking only - actual imports are lazy-loaded via __getattr__
if TYPE_CHECKING:
    from .acl import ACLManager, NewACLManager
    from .aclobject import AclObject
    from .application import Application
    from .baseuser import BaseUser
    from .callback import Callback
    from .configuration import Configuration
    from .form import Form
    from .internaluser import InternalUser
    from .ldapconfig import LdapConfig
    from .lock import Lock
    from .message import Message
    from .package import Package
    from .ports import Ports
    from .remoteuser import RemoteUser
    from .role import Role
    from .system import System
    from .user import User
    from .var import Var
    from .widget import Widget

# Mapping of attribute names to their module paths (excluding eagerly loaded ones)
_LAZY_IMPORTS = {
    "ACLManager": ".acl",
    "NewACLManager": ".acl",
    "Configuration": ".configuration",
    "AclObject": ".aclobject",
    "Application": ".application",
    "BaseUser": ".baseuser",
    "Callback": ".callback",
    "Form": ".form",
    "InternalUser": ".internaluser",
    "LdapConfig": ".ldapconfig",
    "Lock": ".lock",
    "Message": ".message",
    "Package": ".package",
    "Ports": ".ports",
    "RemoteUser": ".remoteuser",
    "Role": ".role",
    "System": ".system",
    "User": ".user",
    "Var": ".var",
    "Widget": ".widget",
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


try:
    from movai_core_enterprise.models import (
        Annotation,
        GraphicScene,
        Layout,
        SharedDataEntry,
        SharedDataTemplate,
        TaskEntry,
        TaskTemplate,
    )

    enterprise_modules = [
        "Annotation",
        "GraphicScene",
        "Layout",
        "SharedDataEntry",
        "SharedDataTemplate",
        "TaskEntry",
        "TaskTemplate",
    ]
except ImportError:
    enterprise_modules = []


__all__ = [
    "ACLManager",
    "NewACLManager",
    "Configuration",
    "AclObject",
    "Application",
    "BaseUser",
    "Callback",
    "Configuration",
    "Container",
    "Flow",
    "FlowLinks",
    "Form",
    "InternalUser",
    "LdapConfig",
    "Lock",
    "Message",
    "Model",
    "Node",
    "NodeInst",
    "Package",
    "Ports",
    "RemoteUser",
    "Role",
    "scopes",
    "ScopeInstanceVersionNode",
    "ScopePropertyNode",
    "ScopeNode",
    "ScopeObjectNode",
    "ScopesTree",
    "System",
    "User",
    "Var",
    "Widget",
]

__all__.extend(enterprise_modules)
