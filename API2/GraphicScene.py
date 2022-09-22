"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
try:
   from movai_core_enterprise.scopes.graphicscene import GraphicScene
   __all__ = ["GraphicScene"]
   enterprise = True
except ImportError:
   __all__ = []
   enterprise = False


