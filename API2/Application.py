"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi  (moawiya@mov.ai) - 2022
"""

try:
    from movai_core_enterprise.models import Application

    __all__ = ["Application"]
except ImportError:
    __all__ = []
