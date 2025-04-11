"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Tiago Teixeira  (tiago.teixeira@mov.ai) - 2020

   Ports Model
"""

from movai_core_shared.consts import TRANSITION_TYPE, ROS1_NODELETCLIENT, ROS1_NODELETSERVER
from .model import Model


class Ports(Model):
    """
    Provides the configuration of a port
    """

    def is_transition(self, port_type: str, port_name: str) -> bool:
        """Check if a port is of type transition"""

        port = self[port_type][port_name]

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

    # default __init__


Model.register_model_class("Ports", Ports)
