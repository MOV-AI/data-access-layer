"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020
"""
from .scope import Scope
from movai_core_shared.consts import (
    TRANSITION_TYPE,
    ROS1_NODELETCLIENT,
    ROS1_NODELETSERVER,
)


class Ports(Scope):
    """Ports model"""

    scope = "Ports"

    def __init__(self, name, version="latest", new=False, db="global"):
        """Initializes the object"""

        super().__init__(scope="Ports", name=name, version=version, new=new, db=db)

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
