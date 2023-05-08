from typing import Optional, Dict, List, Any, Union
from pydantic import constr, BaseModel, Field
from common import Arg
from base import MovaiBaseModel


KEY_REGEX = constr(regex=r"^[a-zA-Z0-9_]+$")
PORT_NAME = constr(regex=r"^[a-zA-Z0-9_]+")


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


class PortsInstValue(BaseModel):
    Message: Optional[str] = ""
    Package: Optional[str] = ""
    Template: str
    Out: Optional[OutValue] = None
    In: Optional[InValue] = None


class Node(MovaiBaseModel):
    EnvVar: Optional[Dict[KEY_REGEX, Arg]] = None
    CmdLine: Optional[Dict[KEY_REGEX, Arg]] = None
    Parameter: Optional[Dict[KEY_REGEX, Arg]] = None
    Launch: Optional[Union[bool, str]] = None
    PackageDepends: Optional[Union[str, List[Any]]] = None
    Path: Optional[str] = None
    Persistent: Optional[bool] = None
    PortsInst: Dict[str, PortsInstValue]
    Remappable: Optional[bool] = None
    Type: Optional[str] = None

    class Meta:
        model_key_prefix = "Node"


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
                            "in": {"Callback": "Counter_CB", "Message": "movai_msgs/Transition"}
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
#print(Node.select())
print("#########")
print(Node.select(ids=[pk]))

#print(Node.find(Node.id == "Node:Counter:__UNVERSIONED__").all())
