"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020
"""
from .scope import Scope


class Widget(Scope):
    """Layout model"""

    scope = "Widget"

    def __init__(self, name, version="latest", new=False, db="global"):
        """Initializes the object"""

        super().__init__(scope="Widget", name=name, version=version, new=new, db=db)
