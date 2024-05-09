"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2023
   - Erez Zomer (erez@mov.ai) - 2023
"""
from typing import Dict, List, Union

from pydantic import Field

from .base import MovaiBaseModel


class System(MovaiBaseModel):
    """A class that implements the System model."""

    Value: Dict[str, Dict[str, Union[bool, List[str], dict]]] = Field(default_factory=dict)
    Parameter: dict = Field(default_factory=dict)
    Package: dict = Field(default_factory=dict)

    @classmethod
    def _original_keys(cls) -> List[str]:
        """keys that are originally defined part of the model

        Returns:
            List[str]: list including the original keys
        """
        return super()._original_keys() + ["Value", "Parameter", "Package"]
