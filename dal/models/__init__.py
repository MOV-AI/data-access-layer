"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi  (moawiya@mov.ai) - 2022
"""
from .acl import ACLManager, NewACLManager
from .configuration import Configuration
from .aclobject import AclObject
from .application import Application
from .baseuser import BaseUser
from .callback import Callback
from .container import Container
from .flow import Flow
from .flowlinks import FlowLinks
from .form import Form
from .internaluser import InternalUser
from .ldapconfig import LdapConfig
from .lock import Lock
from .message import Message
from .model import Model
from .node import Node
from .nodeinst import NodeInst
from .package import Package
from .ports import Ports
from .remoteuser import RemoteUser
from .role import Role
from .scopestree import (
    scopes,
    ScopeInstanceVersionNode,
    ScopePropertyNode,
    ScopeNode,
    ScopeObjectNode,
    ScopesTree,
)
from .system import System
from .user import User
from .var import Var
from .widget import Widget


try:
    from movai_core_enterprise.models import (
        Annotation,
        GraphicAsset,
        GraphicScene,
        Layout,
        SharedDataEntry,
        SharedDataTemplate,
        TaskEntry,
        TaskTemplate,
    )

    enterprise_modules = [
        "Annotation",
        "GraphicAsset",
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
