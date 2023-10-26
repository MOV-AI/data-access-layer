from typing import Optional, Dict, List
from pydantic import StringConstraints, BaseModel, Field
from .base import MovaiBaseModel
from movai_core_shared.consts import (
    TRANSITION_TYPE,
    ROS1_NODELETCLIENT,
    ROS1_NODELETSERVER,
)
from typing_extensions import Annotated


PORT_NAME_REGEX = Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_]+$")]


class InOutValue(BaseModel):
    Transport: str
    Protocol: str
    Message: Optional[str] = None
    Callback: Optional[str] = None
    Parameter: Optional[dict] = Field(default_factory=dict)
    LinkEnabled: bool


class Ports(MovaiBaseModel):
    Data: dict = Field(default_factory=dict)
    In: Optional[Dict[PORT_NAME_REGEX, InOutValue]] = Field(default_factory=dict)
    Out: Optional[Dict[PORT_NAME_REGEX, InOutValue]] = Field(default_factory=dict)

    def is_transition(self, port_type: str, port_name: str) -> bool:
        """Check if a port is of type transition"""

        port = getattr(self, port_type)[port_name]

        if (
            port.Protocol == TRANSITION_TYPE["Protocol"]
            and port.Transport == TRANSITION_TYPE["Transport"]
        ):
            return True

        return False

    def _original_keys(self) -> List[str]:
        return super()._original_keys() + ["Data", "In", "Out"]
