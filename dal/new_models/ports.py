"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2023
   - Erez Zomer (erez@mov.ai) - 2023
"""
from typing import Optional, Dict, List
from typing_extensions import Annotated

from pydantic import StringConstraints, BaseModel, Field

from movai_core_shared.consts import (
    TRANSITION_TYPE,
    ROS1_NODELETCLIENT,
    ROS1_NODELETSERVER,
)

from .base import MovaiBaseModel

PORT_NAME_REGEX = Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_]+$")]


class OutPort(BaseModel):
    Transport: str
    Protocol: str
    Message: Optional[str] = None    
    Parameter: Optional[dict] = Field(default_factory=dict)
    LinkEnabled: bool


class InPort(OutPort):
    Callback: Optional[str] = None


class Ports(MovaiBaseModel):
    Data: dict = Field(default_factory=dict)
    In: Optional[Dict[PORT_NAME_REGEX, InPort]] = Field(default_factory=dict)
    Out: Optional[Dict[PORT_NAME_REGEX, OutPort]] = Field(default_factory=dict)

    def _original_keys(self) -> List[str]:
        return super()._original_keys() + ["Data", "In", "Out"]

    def is_transition(self, port_type: str, port_name: str) -> bool:
        """Check if a port is of type transition"""

        port = getattr(self, port_type)[port_name]

        if (
            port.Protocol == TRANSITION_TYPE["Protocol"]
            and port.Transport == TRANSITION_TYPE["Transport"]
        ):
            return True

        return False

    def is_nodelet_client(self) -> bool:
        """Returns True if the port is a nodelet client"""
        return self.Template == ROS1_NODELETCLIENT

    def is_nodelet_server(self) -> bool:
        """Returns True if the port is a nodelet server"""
        return self.Template == ROS1_NODELETSERVER
