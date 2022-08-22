"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi  (moawiya@mov.ai) - 2022
"""
try:
    from movai_core_enterprise.scopes import (
        Task,
        TaskEntry,
        TaskTemplate,
        SharedDataTemplate,
        SharedDataEntry
    )

    __all__ = [
        "Task",
        "TaskTemplate",
        "SharedDataTemplate",
        "TaskEntry",
        "SharedDataEntry"
    ]
except ImportError:
    __all__ = []
