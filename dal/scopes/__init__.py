"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi  (moawiya@mov.ai) - 2022
"""
from .application import Application
from .alert import Alert
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
from .statemachine import StateMachine, SMVars
from .structures import Struct
from .system import System
from .translation import Translation
from .user import User
from .widget import Widget
from dal.utils.usage_search import (
    FlowUsageInfo,
    NodeUsageInfo,
    PathElement,
    get_cached_usage_search_scope_map,
    get_usage_search_scope_map,
)

__all__ = [
    "Application",
    "Callback",
    "Config",
    "Configuration",
    "FleetRobot",
    "Flow",
    "FlowUsageInfo",
    "Form",
    "Message",
    "Node",
    "NodeUsageInfo",
    "Package",
    "PathElement",
    "Ports",
    "Robot",
    "Role",
    "Scope",
    "StateMachine",
    "SMVars",
    "Struct",
    "System",
    "Translation",
    "User",
    "Widget",
    "Alert",
    "get_usage_search_scope_map",
    "get_cached_usage_search_scope_map",
]

try:
    from movai_core_enterprise.scopes import (
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
        "Annotation",
        "GraphicAsset",
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
