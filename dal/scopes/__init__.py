"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi  (moawiya@mov.ai) - 2022
"""
from .application import Application
# from .callback import Callback
from dal.new_models import Callback
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
from .statemachine import StateMachine, SMVars
from .structures import Struct
from .system import System
from .user import User
from .widget import Widget

__all__ = [
   "Application",
   "Callback",
   "Config",
   "Configuration",
   "FleetRobot",
   "Flow",
   "Form",
   "Message",
   "Node",
   "Package",
   "Ports",
   "Robot",
   "Role",
   "Scope",
   "StateMachine",
   "SMVars",
   "Struct",
   "System",
   "User",
   "Widget",
]

try:
   from movai_core_enterprise.scopes import(
      Annotation,
      GraphicAsset,
      GraphicScene,
      Layout,
      SharedDataEntry, 
      SharedDataTemplate,
      Task,
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
        "Task",
        'TaskEntry',
        'TaskTemplate'
    ]
except ImportError:
   enterprise_modules = []

__all__.extend(enterprise_modules)
