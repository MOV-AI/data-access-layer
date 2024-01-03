"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2023
   - Erez Zomer (erez@mov.ai) - 2023
"""
from typing import Optional, Dict, List, Any, Union
from typing_extensions import Annotated

from pydantic import StringConstraints, BaseModel, Field, field_validator, ConfigDict

from movai_core_shared.consts import (
    MOVAI_NODE,
    MOVAI_SERVER,
    MOVAI_STATE,
    MOVAI_TRANSITIONFOR,
    MOVAI_TRANSITIONTO,
    ROS1_NODE,
    ROS1_NODELET,
    ROS1_PLUGIN,
)

from dal.new_models.base import MovaiBaseModel
from dal.new_models.base_model.common import Arg
from dal.new_models.ports import Ports

KEY_REGEX = Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_]+$")]
PORT_NAME = Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_]+$")]


class Parameter1(BaseModel):
    Child: Optional[str] = None
    Parent: Optional[str] = None


class Portfields(BaseModel):
    """A class that represent Portfields."""

    Message: Optional[str] = None
    Callback: Optional[str] = None
    Parameter: Optional[Parameter1] = Field(default_factory=Parameter1)


class ActionFields(BaseModel):
    """A class that represent ActionFields."""

    cancel: Optional[Portfields] = None
    feedback: Optional[Portfields] = None
    goal: Optional[Portfields] = None
    status: Optional[Portfields] = None
    result: Optional[Portfields] = None


class OutValue(ActionFields):
    """A class that represent OutValue field."""

    out: Optional[Portfields] = None


class InValue(ActionFields):
    """A class that represent InValue field."""

    in_: Optional[Portfields] = Field(default=None, alias="in")

    model_config = ConfigDict(populate_by_name=True)


class PortsInstValue(BaseModel):
    """A class that represent PortsInValue field."""

    Message: Optional[str] = ""
    Package: Optional[str] = ""
    Template: Optional[str] = ""
    Out: Optional[OutValue] = Field(default_factory=OutValue)
    In: Optional[InValue] = Field(default_factory=InValue)


class Node(MovaiBaseModel):
    """A class that implements the Message Model."""

    EnvVar: Optional[Dict[KEY_REGEX, Arg]] = Field(default_factory=dict)
    CmdLine: Optional[Dict[KEY_REGEX, Arg]] = Field(default_factory=dict)
    Parameter: Optional[
        Dict[Annotated[str, StringConstraints(pattern=r"^[@a-zA-Z0-9_/]+$")], Arg]
    ] = Field(default_factory=dict)
    Launch: Optional[Union[bool, str]] = None
    PackageDepends: Optional[Union[str, List[Any]]] = None
    Path: Optional[str] = None
    Persistent: Optional[bool] = False
    PortsInst: Dict[str, PortsInstValue] = Field(default_factory=dict)
    Remappable: Optional[bool] = False
    Type: Optional[str] = None

    @classmethod
    def _original_keys(cls) -> List[str]:
        """keys that are originally defined part of the model.

        Returns:
            List[str]: list including the original keys
        """
        return super()._original_keys() + [
            "EnvVar",
            "CmdLine",
            "Parameter",
            "Launch",
            "PackageDepends",
            "Path",
            "Persistent",
            "PortsInst",
            "Remappable",
            "Type",
        ]

    @field_validator("Parameter", mode="before")
    @classmethod
    def validate_parameter(cls, v):
        try:
            return v
        except ValueError as verr:
            field, error = verr.errors()[0]["loc"], verr.errors()[0]["msg"]
            raise ValueError(f"{field}: {v} - {error}")

    @field_validator("Remappable", "Persistent", mode="before")
    @classmethod
    def validate_remappable(cls, v):
        return False if v in [None, ""] else v

    @property
    def is_remappable(self) -> bool:
        """Returns True if the ports are allowed to remap"""
        # get the value from the attribute Remappable
        # possible values True, False, None, ""
        prop = True if self.Remappable in [None, ""] else self.Remappable

        # get the value from the parameter _remappable
        # parameter takes precedence over attribute
        param = None
        try:
            if self.Parameter:
                param = self.Parameter["_remappable"].Value
        except KeyError:
            pass

        return prop if param in [None, ""] else param

    @property
    def is_node_to_launch(self) -> bool:
        """Returns True if it should be launched"""
        # get the value from the attribute Launch
        # possible values True, False, None, ""
        prop = True if self.Launch in [None, ""] else self.Launch

        # get the value from the parameter _launch
        # parameter takes precedence over attribute
        param = None
        try:
            if self.Parameter:
                param = self.Parameter["_launch"].Value
        except KeyError:
            pass

        return prop if param in [None, ""] else param

    @property
    def is_persistent(self) -> bool:
        """Returns True if it persists on state transitions"""
        # get the value from the attribute Persistent
        # possible values True, False, None, ""
        prop = False if self.Persistent in [None, ""] else self.Persistent

        # get the value from the parameter _persistent
        # parameter takes precedence over attribute
        param = None
        try:
            if self.Parameter:
                param = self.Parameter["_persistent"].Value
        except KeyError:
            pass

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
        output = {}
        if self.Parameter:
            output = {key: val.Value for key, val in self.Parameter.items()}
        return output

    def get_port(self, port_inst: str) -> Ports:
        """Returns an instance (Ports) of the port instance template"""

        if port_inst not in self.PortsInst:
            # TODO: raise exception
            return None
        tpl = self.PortsInst[port_inst].Template

        return Ports(tpl)

    def set_type(self):
        type_to_set = MOVAI_NODE
        templs = []
        if self.PortsInst:
            for _, temp in self.PortsInst.items():
                templs.append(temp.Template)
        if self.Path:
            if any("ROS1" in templ for templ in templs):
                type_to_set = ROS1_NODE

            if any("ROS1/PluginClient" in templ for templ in templs):
                type_to_set = ROS1_PLUGIN

        if any("ROS1/Nodelet" in templ for templ in templs):
            type_to_set = ROS1_NODELET

        if any("Http" in templ for templ in templs):
            type_to_set = MOVAI_SERVER

        if any(templ in (MOVAI_TRANSITIONFOR, MOVAI_TRANSITIONTO) for templ in templs):
            type_to_set = MOVAI_STATE

        self.Type = type_to_set
        self.save()
