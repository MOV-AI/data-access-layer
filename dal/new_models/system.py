"""
"""
from .base import MovaiBaseModel
from typing import Dict, List
from pydantic import Field


class System(MovaiBaseModel):
    Value: Dict[str, Dict[str, List[str]]] = Field(default_factory=dict)
    Parameter: dict = Field(default_factory=dict)
    Package: dict = Field(default_factory=dict)

    def _original_keys(self) -> List[str]:
        return super()._original_keys() + ["Value", "Parameter", "Package"]
