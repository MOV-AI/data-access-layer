"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi  (moawiya@mov.ai) - 2022
"""
from .acl import ACLManager
from .aclobject import AclObject
from .application import Application
from .callback import Callback
from .configuration import Configuration
from .flow import Flow
from .form import Form
from .internaluser import InternalUser
from .ldapconfig import LdapConfig
from .lock import Lock
from .message import Message
from .model import Model
from .node import Node
from .package import Package
from .ports import Ports
from .remoteuser import RemoteUser
from .role import Role
from .system import System
from .var import Var
from .widget import Widget


# scope part modules
from ..scopes.container import Container
from ..scopes.nodeinst import NodeInst

try:
    from movai_core_enterprise.scopes import (
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
        'Annotation',
        'GraphicAsset',
        'GraphicScene',
        'Layout',
        'SharedDataEntry',
        'SharedDataTemplate',
        'TaskEntry',
        'TaskTemplate'
    ]
except ImportError:
    enterprise_modules = []


modules = [
    'ACLManager',
    'AclObject',
    'Application',
    'BaseUser',
    'Callback',
    'Configuration',
    'Container',
    'Flow',
    'Form',
    'InternalUser',
    'LdapConfig',
    'Lock',
    'Message',
    'Model',
    'Node',
    'NodeInst',
    'Package',
    'Ports',
    'RemoteUser',
    'Role',
    'System',
    'User',
    'Var',
    'Widget'
]
modules.extend(enterprise_modules)

__all__ = modules
