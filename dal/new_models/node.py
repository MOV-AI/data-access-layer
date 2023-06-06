from typing import Optional, Dict, List, Any, Union
from pydantic import constr, BaseModel, Field, validator
from .base_model import Arg, MovaiBaseModel
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
from ..models.scopestree import scopes


KEY_REGEX = constr(regex=r"^[a-zA-Z0-9_]+$")
PORT_NAME = constr(regex=r"^[a-zA-Z0-9_]+$")


class Parameter1(BaseModel):
    Child: Optional[str] = None
    Parent: Optional[str] = None


class Portfields(BaseModel):
    Message: Optional[str] = None
    Callback: Optional[str] = None
    Parameter: Optional[Parameter1] = None


class ActionFields(BaseModel):
    cancel: Optional[Portfields] = None
    feedback: Optional[Portfields] = None
    goal: Optional[Portfields] = None
    status: Optional[Portfields] = None
    result: Optional[Portfields] = None


class OutValue(ActionFields):
    out: Optional[Portfields] = None


class InValue(ActionFields):
    in_: Optional[Portfields] = Field(default=None, alias="in")

    def dict(
        self,
        *,
        include=None,
        exclude=None,
        by_alias: bool = False,
        skip_defaults: Optional[bool] = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ):
        return super().dict(
            include=include,
            exclude=exclude,
            by_alias=True,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )


class PortsInstValue(BaseModel):
    Message: Optional[str] = ""
    Package: Optional[str] = ""
    Template: Optional[str] = ""
    Out: Optional[OutValue] = None
    In: Optional[InValue] = None


class Node(MovaiBaseModel):
    EnvVar: Optional[Dict[KEY_REGEX, Arg]] = Field(default_factory=dict)
    CmdLine: Optional[Dict[KEY_REGEX, Arg]] = Field(default_factory=dict)
    Parameter: Optional[Dict[constr(regex=r"^[@a-zA-Z0-9_/]+$"), Arg]] = None
    Launch: Optional[Union[bool, str]] = None
    PackageDepends: Optional[Union[str, List[Any]]] = None
    Path: Optional[str] = None
    Persistent: Optional[bool] = False
    PortsInst: Dict[str, PortsInstValue] = Field(default_factory=dict)
    Remappable: Optional[bool] = False
    Type: Optional[str] = None

    class Meta:
        model_key_prefix = "Node"

    @validator("Parameter", pre=True, always=True)
    def validate_parameter(cls, v):
        try:
            return v
        except ValueError as e:
            field, error = e.errors()[0]["loc"], e.errors()[0]["msg"]
            raise ValueError(f"{field}: {v} - {error}")

    @validator("Remappable", pre=True, always=True)
    def validate_remappable(cls, v):
        return v if v not in [None, ""] else False

    @validator("Persistent", pre=True, always=True)
    def validate_persistent(cls, v):
        return v if v not in [None, ""] else False

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

    def get_port(self, port_inst: str):
        """Returns an instance (Ports) of the port instance template"""

        if port_inst not in self.PortsInst:
            # TODO: raise exception
            return None
        tpl = self.PortsInst[port_inst].Template

        # return Ports(tpl)
        # TODO change this
        return scopes.from_path(tpl, scope="Ports")

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


if __name__ == "__main__":
    n = Node(
        **{
            "Node": {
                "Countto10": {
                    "Info": "A state that transitions to the done oport a set maximum number of counts (param: max_count) after which the state transitions to the max_count oport. The counter name can be set using the counter_name and the reset param can be used to reset the counter value to zero count, given counter name. ",
                    "Label": "CounterYYYY",
                    "LastUpdate": {"date": "02/07/2021 at 16:18:09", "user": "movai"},
                    "Launch": False,
                    "PackageDepends": "",
                    "Parameter": {
                        "counter_name": {
                            "Description": "[string] Name of the redis variable in which the node saves the current count or iterations. When using the reset functionality of this node, this redis variable is reset to zero",
                            "Value": '"count_cycles"',
                        },
                        "max_count": {
                            "Description": '[integer] Number of times this node will transition to the "done" oport, once exceeded the node will transition to the "max_count" out port',
                            "Value": "2",
                        },
                        "reset": {
                            "Description": "[bool] Reset the counter state, stored in the redis flow variable mentioned in the counter_name parameter, to zero.",
                            "Value": "False",
                        },
                    },
                    "Path": "",
                    "Persistent": False,
                    "PortsInst": {
                        "done": {
                            "Message": "Transition",
                            "Out": {"out": {"Message": "movai_msgs/Transition"}},
                            "Package": "movai_msgs",
                            "Template": "MovAI/TransitionFor",
                        },
                        "entry": {
                            "In": {
                                "in": {
                                    "Callback": "Counter_CB",
                                    "Message": "movai_msgs/Transition",
                                }
                            },
                            "Message": "Transition",
                            "Package": "movai_msgs",
                            "Template": "MovAI/TransitionTo",
                        },
                        "max_count": {
                            "Message": "Transition",
                            "Out": {"out": {"Message": "movai_msgs/Transition"}},
                            "Package": "movai_msgs",
                            "Template": "MovAI/TransitionFor",
                        },
                    },
                    "Remappable": True,
                    "Type": "MovAI/State",
                    "User": "",
                    "Version": "",
                    "VersionDelta": {},
                }
            }
        }
    )

    pk = n.save()

    print(pk)
    # print(Node.select())
    print("#########")
    print(Node.select(ids=[pk]))

    # print(Node.find(Node.id == "Node:Counter:__UNVERSIONED__").all())
