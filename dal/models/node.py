"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
   - Manuel Silva  (manuel.silva@mov.ai) - 2020
"""
from movai_core_shared.consts import ROS1_NODELET, MOVAI_STATE, ROS1_PLUGIN

from dal.scopes.scopestree import scopes
from dal.models.model import Model


class Node(Model):
    """
    Provides the default configuration to launch a GD_Node
    """

    __RELATIONS__ = {
        # "schemas/1.0/Node/PortsInst/Template": {
        #     "schema_version": "1.0",
        #     "scope": "Ports",
        # },
        "schemas/1.0/Node/PortsInst/In/Callback": {
            "schema_version": "1.0",
            "scope": "Callback",
        }
    }

    @property
    def is_remappable(self) -> bool:
        """Returns True if the ports are allowed to remap"""
        # get the value from the attribute Remappable
        # possible values True, False, None, ""
        prop = True if self.Remappable in [None, ""] else self.Remappable

        # get the value from the parameter _remappable
        # parameter takes precedence over attribute
        try:
            param = self.Parameter["_remappable"].Value
        except KeyError:
            param = None

        return prop if param in [None, ""] else param

    @property
    def is_node_to_launch(self) -> bool:
        """Returns True if it should be launched"""
        # get the value from the attribute Launch
        # possible values True, False, None, ""
        prop = True if self.Launch in [None, ""] else self.Launch

        # get the value from the parameter _launch
        # parameter takes precedence over attribute
        try:
            param = self.Parameter["_launch"].Value
        except KeyError:
            param = None

        return prop if param in [None, ""] else param

    @property
    def is_persistent(self) -> bool:
        """Returns True if it persists on state transitions"""
        # get the value from the attribute Persistent
        # possible values True, False, None, ""
        prop = False if self.Persistent in [None, ""] else self.Persistent

        # get the value from the parameter _persistent
        # parameter takes precedence over attribute
        try:
            param = self.Parameter["_persistent"].Value
        except KeyError:
            param = None

        return prop if param in [None, ""] else param

    @property
    def is_nodelet(self) -> bool:
        """Returns True if the node is of type Nodelet"""
        return self.Type == ROS1_NODELET

    @property
    def is_state(self) -> bool:
        """Returns True if the node is of type State"""
        return self.Type == MOVAI_STATE

    @property
    def is_plugin(self) -> bool:
        """Returns True if the node is of type plugin"""
        return self.Type == ROS1_PLUGIN

    def get_params(self) -> dict:
        """
        Return a dict with all parameters in the format <parameter name>: <Parameter.Value>
        (Parameter format is {key:{Value: <value>, Description: <value>}})
        """
        params = self.Parameter.serialize()
        output = {key: value["Value"] for key, value in params.items()}
        return output

    def get_port(self, port_inst: str):
        """Returns an instance (Ports) of the port instance template"""

        tpl = self.PortsInst[port_inst].Template

        # return Ports(tpl)
        return scopes.from_path(tpl, scope="Ports")


# Register class as model of scope Flow
Model.register_model_class("Node", Node)
