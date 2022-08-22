"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi  (moawiya@mov.ai) - 2022
"""
from .configuration import Configuration
from .application import Application
from .callback import Callback
from .form import Form
from .model import Model
from .node import Node
from .system import System
from .var import Var
from .widget import Widget
from .flow import Flow
from .acl import ACLManager
from .user import User
from .lock import Lock
from .package import Package
from .ports import Ports
from .message import Message

# scope part modules
from ..scopes.container import Container
from ..scopes.nodeinst import NodeInst

try:
    from movai_core_enterprise.models import (
        SharedDataEntry, SharedDataTemplate, TaskTemplate,
        TaskEntry, Annotation, GraphicAsset, Layout, GraphicScene
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
