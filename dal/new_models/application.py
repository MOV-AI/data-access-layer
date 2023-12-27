"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2023
   - Erez Zomer (erez@mov.ai) - 2023
"""
from typing import List, Any

from pydantic import Field

from .base import MovaiBaseModel


class Application(MovaiBaseModel):
    User: str = ""
    Type: str = ""
    Package: str = ""
    EntryPoint: str = ""
    Icon: str = ""
    Configuration: str = ""
    CustomConfiguration: str = ""
    Callbacks: List[Any] = Field(default_factory=list)

    def _original_keys(self) -> List[str]:
        return super()._original_keys() + [
            "Type",
            "Package",
            "EntryPoint",
            "Icon",
            "Configuration",
            "CustomConfiguration",
            "Callbacks",
        ]
