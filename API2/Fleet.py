"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
try:
    from movai_core_enterprise.scopes.task import Task
    from movai_core_enterprise.scopes.tasktemplate import TaskTemplate
    from movai_core_enterprise.scopes.shareddatatemplate import SharedDataTemplate
    from movai_core_enterprise.scopes.taskentry import TaskEntry
    from movai_core_enterprise.scopes.shareddataentry import SharedDataEntry

    __all__ = [
        "Task",
        "TaskTemplate",
        "SharedDataTemplate",
        "TaskEntry",
        "SharedDataEntry",
    ]
    enterprise = True
except ImportError:
    __all__ = []
    enterprise = False
