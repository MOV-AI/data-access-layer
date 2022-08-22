"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi  (moawiya@mov.ai) - 2022
"""
from .aclobject import AclObject
from .application import Application
from .baseuser import BaseUser
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
from .system import System
from .user import User
from .var import Var
from .widget import Widget
from .acl import ACLManager

# scope part modules
from ..scopes.container import Container
from ..scopes.nodeinst import NodeInst

try:
    from movai_core_enterprise.scopes import (
        SharedDataEntry,
        SharedDataTemplate,
        TaskTemplate,
        TaskEntry,
        Annotation,
        GraphicAsset,
        Layout,
        GraphicScene
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

try:
    from backend.models.role import Role
    backend_moduels = ['Role']
except ImportError:
    backend_moduels = []

modules = [
    'ACLManager',
    'Application',
    'Callback',
    'Configuration',
    'Container',
    'Flow',
    'Form',
    'Lock',
    'Message',
    'Model',
    'Node',
    'NodeInst',
    'Package',
    'Ports',
    'System',
    'User',
    'Var',
    'Widget'
]
modules.extend(enterprise_modules)
modules.extend(backend_moduels)

__all__ = modules
