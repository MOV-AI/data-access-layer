from typing import Optional, Dict, List, Any, Union
from pydantic import constr
from redis_om import EmbeddedJsonModel, JsonModel, Migrator, get_redis_connection, Field
from common import LastUpdate, Arg
from re import search
import json


class Parameter1(EmbeddedJsonModel):
    Child: Optional[str] = None
    Parent: Optional[str] = None


class Portfields(EmbeddedJsonModel):
    Message: Optional[str] = None
    Callback: Optional[str] = None
    Parameter: Optional[Parameter1] = None


class ActionFields(EmbeddedJsonModel):
    cancel: Optional[Portfields] = None
    feedback: Optional[Portfields] = None
    goal: Optional[Portfields] = None
    status: Optional[Portfields] = None
    result: Optional[Portfields] = None


class OutValue(ActionFields):
    out: Optional[Portfields] = None


class InValue(ActionFields):
    in_: Optional[Portfields] = Field(None, alias="in")


class PortsInstValue(EmbeddedJsonModel):
    Message: str
    Package: str
    Template: str
    Out: Optional[OutValue] = None
    In: Optional[InValue] = None


class Node(JsonModel):
    id: str = Field(default="", index=True)
    Info: Optional[str] = None
    Label: constr(regex=r"^[a-zA-Z0-9._-]+$")
    Description: Optional[str] = None
    LastUpdate: LastUpdate
    Version: str = Field(default="__UNVERSIONED__", index=True)
    EnvVar: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), Arg]] = None
    CmdLine: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), Arg]] = None
    Parameter: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), Arg]] = None
    Launch: Optional[Union[bool, str]] = None
    PackageDepends: Optional[Union[str, List[Any]]] = None
    Path: Optional[str] = None
    Persistent: Optional[bool] = None
    PortsInst: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), PortsInstValue]] = None
    Remappable: Optional[bool] = None
    Type: Optional[str] = None

    class Meta:
        global_key_prefix = "Models"
        model_key_prefix = "Node"
        database = get_redis_connection(url="redis://172.17.0.2", db=0)

    class Config:
        # Force Validation in case field value change
        validate_assignment = True

    def __init__(self, *args, **kwargs):
        version = "__UNVERSIONED__"
        if "version_" in kwargs:
            version = kwargs["version_"]
        if list(kwargs.keys())[0] == "Node":
            if kwargs is None or not isinstance(kwargs, dict):
                return
            type, struct_ = list(kwargs.items())[0]
            # TODO validate types
            if type != "Node":
                # TODO
                raise ValueError("")

            name = list(struct_.keys())[0]
            # TODO change the id in future
            id = f"Node:{name}:{version}"
            if search(r"^[a-zA-Z0-9_]+$", name) is None:
                raise ValueError(f"Validation Error for {type} name:({name}), data:{kwargs}")

            super().__init__(**struct_[name], id=id)
        else:
            super().__init__(*args, **kwargs)

    def dict(self):
        dic = super().dict(exclude_unset=True)
        id = dic.pop("id")
        return {"Node": {id.split(":")[1]: dic}}

    def schema_json(self):
        schema = json.loads(super().schema_json())
        schema["properties"].pop("pk")
        schema["properties"].pop("id")
        schema["definitions"]["LastUpdate"]["properties"].pop("pk")
        return schema


n = Node(
    **{
        "Node": {
            "GoTo": {
                "Info": "Main node to perform robot navigation. The GoTo node sends to the main navigation stack via Redis, the information on the navigation type, the goal and annotations to use.",
                "Label": "GoTo",
                "LastUpdate": {"date": "03/01/2023 at 12:16:14", "user": "movai"},
                "Launch": True,
                "PackageDepends": "",
                "Parameter": {
                    "actuators": {
                        "Description": "(Dict) Actuators to be performed by robot before sending the command to navigation stack, alerting the environment that the robot is going to move. List of possible values are described in the Actuator Stack for the Robot.",
                        "Type": "any",
                        "Value": "{'leds' : 'fade_green', 'buzzer': False}",
                    },
                    "annotation": {
                        "Description": "(Str) Name of the annotation to include. Use None to not include any",
                        "Type": "any",
                        "Value": "None",
                    },
                    "error_log": {
                        "Description": "(Str) (Str) Log to be displayed when the node fails to achieve the given navigation command",
                        "Type": "any",
                        "Value": "",
                    },
                    "goal": {
                        "Description": "(Float/Str) This can be a distance (m) or, angle (deg) or, a trajectory or, a keypoint name from the Scene, depending on the nav_type parameter. If None, default value is from Var('Robot').goal_id. ",
                        "Type": "any",
                        "Value": "None",
                    },
                    "info_log": {
                        "Description": "(Str) Log to be displayed when the node successfully achieve the given navigation command",
                        "Type": "any",
                        "Value": "",
                    },
                    "localization": {
                        "Description": "(dict) Localization sources to use for the current movement",
                        "Type": "any",
                        "Value": "$(config localization.default)",
                    },
                    "nav_type": {
                        "Description": "(Str) Type of navigation to use. e.g: move_distance, rotate, dock, graph_nav, traj_nav, free_nav.\n The list of all possible values is described in https://movai.readme.io/docs/types",
                        "Type": "any",
                        "Value": "rotate",
                    },
                    "params": {
                        "Description": "(dict) Any parameters sent here will overwrite the ones in the annotation",
                        "Type": "any",
                        "Value": "{}",
                    },
                    "timeout_log": {
                        "Description": "(Str) Log to be displayed when the node timed out to achieve the given navigation command",
                        "Type": "any",
                        "Value": "",
                    },
                    "use_task_manager": {
                        "Description": "(Bool) Enable/Disable task manager features in the node ",
                        "Type": "any",
                        "Value": "$(config project.use_task_manager)",
                    },
                },
                "Path": "",
                "Persistent": False,
                "PortsInst": {
                    "actuators_stack": {
                        "In": {
                            "in": {
                                "Callback": "place_holder",
                                "Message": "movai_msgs/Context",
                                "Parameter": {"Namespace": "actuators"},
                            }
                        },
                        "Message": "Context",
                        "Out": {
                            "out": {
                                "Message": "movai_msgs/Context",
                                "Parameter": {"Namespace": "actuators"},
                            }
                        },
                        "Package": "movai_msgs",
                        "Template": "MovAI/ContextClient",
                    },
                    "end": {
                        "Message": "Transition",
                        "Out": {"out": {"Message": "movai_msgs/Transition"}},
                        "Package": "movai_msgs",
                        "Template": "MovAI/TransitionFor",
                    },
                    "failed": {
                        "Message": "Transition",
                        "Out": {"out": {"Message": "movai_msgs/Transition"}},
                        "Package": "movai_msgs",
                        "Template": "MovAI/TransitionFor",
                    },
                    "localization_stack": {
                        "In": {
                            "in": {
                                "Callback": "place_holder",
                                "Message": "movai_msgs/Context",
                                "Parameter": {"Namespace": "localization"},
                            }
                        },
                        "Message": "Context",
                        "Out": {
                            "out": {
                                "Message": "movai_msgs/Context",
                                "Parameter": {"Namespace": "localization"},
                            }
                        },
                        "Package": "movai_msgs",
                        "Template": "MovAI/ContextClient",
                    },
                    "navigation_stack": {
                        "In": {
                            "in": {
                                "Callback": "goto_navigation_stack",
                                "Message": "movai_msgs/Context",
                                "Parameter": {"Namespace": "navigation"},
                            }
                        },
                        "Message": "Context",
                        "Out": {
                            "out": {
                                "Message": "movai_msgs/Context",
                                "Parameter": {"Namespace": "navigation"},
                            }
                        },
                        "Package": "movai_msgs",
                        "Template": "MovAI/ContextClient",
                    },
                    "safety_stack": {
                        "In": {
                            "in": {
                                "Callback": "place_holder",
                                "Message": "movai_msgs/Context",
                                "Parameter": {"Namespace": "risk_prevention"},
                            }
                        },
                        "Message": "Context",
                        "Out": {
                            "out": {
                                "Message": "movai_msgs/Context",
                                "Parameter": {"Namespace": "risk_prevention"},
                            }
                        },
                        "Package": "movai_msgs",
                        "Template": "MovAI/ContextClient",
                    },
                    "start": {
                        "In": {
                            "in": {"Callback": "goto_start", "Message": "movai_msgs/Transition"}
                        },
                        "Message": "Transition",
                        "Package": "movai_msgs",
                        "Template": "MovAI/TransitionTo",
                    },
                    "timeout": {
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

print(n.save())