"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
from dal.helpers import Helpers
from dal.scopes.application import (Application)
from dal.scopes.form import (Form)
from dal.scopes.ports import (Ports)
from dal.scopes.scope import (Scope)
from dal.scopes.structures import (List, Hash, Struct)
from dal.scopes.system import (System)
from dal.scopes.widget import (Widget)

try:
    from movai_core_enterprise.scopes.annotation import (Annotation)
    from movai_core_enterprise.scopes.graphicasset import (GraphicAsset)
    from movai_core_enterprise.scopes.layout import (Layout)
    from movai_core_enterprise.scopes.shareddataentry import (SharedDataEntry)
    from movai_core_enterprise.scopes.shareddatatemplate import (SharedDataTemplate)
    from movai_core_enterprise.scopes.tasktemplate import (TaskTemplate)
    enterprise_models = [
        "Annotation",
        "GraphicAsset",
        "Layout",
        "SharedDataEntry",
        "SharedDataTemplate",
        "TaskTemplate",
    ]
except ImportError:
    enterprise_models = []

__all__ = [
    "Application",
    "Form",
    "List",
    "Hash",
    "Helpers",
    "Scope",
    "Struct",
    "Widget",
    "System",
    "Ports",
]
__all__.extend(enterprise_models)
