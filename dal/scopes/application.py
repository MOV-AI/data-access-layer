"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020
"""
from deprecated.api.core.scope import Scope


class Application(Scope):
    """Application model"""

    scope = "Application"
    
    permissions = [*Scope.permissions, 'execute']

    def __init__(self, name, version='latest', new=False, db='global'):
        super().__init__(scope="Application", name=name, version=version, new=new, db=db)

