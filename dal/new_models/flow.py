from typing import Optional, Dict, List, Any, Union
from pydantic import constr, BaseModel, validator, ValidationError, Extra
from .base_model import Arg, MovaiBaseModel
import re


ValidName = constr(regex=r"^[a-zA-Z0-9_]+$")


class Layer(BaseModel):
    name: Optional[str] = None
    on: Optional[bool] = None


class CmdLineValue(BaseModel):
    Value: Any


class EnvVarValue(BaseModel):
    Value: Any


class Parameter(BaseModel):
    Child: Optional[str] = None
    Parent: Optional[str] = None


class Portfields(BaseModel):
    Message: Optional[str] = None
    Callback: Optional[str] = None
    Parameter: Optional[Parameter] = None


class X(BaseModel):
    Value: float


class Y(BaseModel):
    Value: float


class Visualization(BaseModel):
    x: X
    y: Y


class Visual(BaseModel):
    # __root__: Union[VisualItem, VisualItem1]
    Visualization: Union[List[float], Visualization]


class ContainerValue(BaseModel):
    ContainerFlow: Optional[str] = None
    ContainerLabel: Optional[str] = None
    # Parameter: Optional[ArgSchema] = None
    Parameter: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), Arg]] = None


LINK_REGEX = r"^~?[a-zA-Z_0-9]+(//?~?[a-zA-Z_0-9]+){0,}$"
class Link(BaseModel):
    From: str
    To: str

    @validator('From', 'To', pre=True, always=True)
    def validate_regex(cls, value, field):
        if not re.match(LINK_REGEX, value):
            raise ValueError(f"Field '{field.alias}' with value '{value}' does not match the required pattern '{LINK_REGEX}'.")
        return value
    
PARAMETER_REGEX = r"^(/?[a-zA-Z0-9_@]+)+$"
class NodeInstValue(BaseModel):
    NodeLabel: Optional[ValidName] = None
    Parameter: Optional[Dict[str, Arg]] = None
    Template: Optional[ValidName] = None
    CmdLine: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), CmdLineValue]] = None
    EnvVar: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), EnvVarValue]] = None
    NodeLayers: Optional[Any] = None
    
    @validator('Parameter', pre=True, always=True)
    def validate_regex(cls, value):
        if isinstance(value, dict):
            for key in value:
                if not re.match(PARAMETER_REGEX, key):
                    raise ValueError(f"Field '{Parameter}' with value '{key}' does not match the required pattern '{PARAMETER_REGEX}'.")
        return value


class Flow(MovaiBaseModel, extra=Extra.allow):
    Parameter: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), Arg]] = None
    Container: Optional[Dict[constr(regex=r"^[a-zA-Z_0-9]+$"), ContainerValue]] = None
    ExposedPorts: Optional[
        Dict[
            constr(regex=r"^(__)?[a-zA-Z0-9_]+$"),
            Dict[
                constr(regex=r"^[a-zA-Z_0-9]+$"),
                List[constr(regex=r"^~?[a-zA-Z_0-9]+(\/~?[a-zA-Z_0-9]+){0,}$")],
            ],
        ]
    ] = None
    Layers: Optional[Dict[constr(regex=r"^[0-9]+$"), Layer]] = None
    Links: Optional[Dict[constr(regex=r"^[0-9a-z-]+$"), Link]] = None
    NodeInst: Optional[Dict[constr(regex=r"^[a-zA-Z_0-9]+$"), NodeInstValue]] = None

    def _original_keys(self) -> List[str]:
        return super()._original_keys() + ["Parameter", "Container", "ExposedPorts", "Layers", "Links", "NodeInst"]

    class Meta:
        model_key_prefix = "Flow"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_calc_remaps = None
        self.cache_dict = None
        self.cache_node_insts = {}
        self.cache_node_template = {}
        self.cache_ports_templates = {}
        self.cache_node_params = {}
        self.cache_container_params = {}
        self.parent_parameters = {}

if __name__ == "__main__":
    f = Flow(
        **{
            "Flow": {
                "ignition_camera_rgbD": {
                    "Description": 'This Subflow is to use with the Ignition Sensor "rgbd_camera" in the robot SDF file.',
                    "ExposedPorts": {
                        "dependency": {"dependency": ["entry/in"]},
                        "remap_sim_depthcam": {
                            "output": [
                                "image_raw/out",
                                "camera_info/out",
                                "points/out",
                                "depth_image/points/out",
                                "depth_image/out",
                                "image/out",
                            ]
                        },
                    },
                    "Info": "",
                    "Label": "ignition_camera_rgbD_Moawiya",
                    "LastUpdate": {"date": "17/12/2021 at 14:10:17", "user": "movai"},
                    "Layers": {},
                    "Links": {
                        "07302d37-a1bf-4852-9ab4-7d149f6d9b38": {
                            "From": "dependency/depends/out",
                            "To": "output/depend/in",
                        },
                        "1cce13ce-101a-4713-9de6-65fe5df54a91": {
                            "From": "dependency/depends/out",
                            "To": "ign_bridge_camera_info/dependency/in",
                        },
                        "3a956471-d262-4798-b333-d7443191245b": {
                            "From": "dependency/depends/out",
                            "To": "ign_bridge_image/dependency/in",
                        },
                        "9d531a8c-0be8-44d2-8e3e-de0824db7b14": {
                            "From": "tf_camera_front/tf_static/out",
                            "To": "ign_bridge_image/empty/in",
                        }, "ab2b122c-16c7-42f4-bfd8-ebf8a430bbf0": {
                            "From": "dependency/depends/out",
                            "To": "ign_bridge_point_cloud/dependency/in",
                        },
                        "fccf2ca6-9657-45b3-bcd9-16308c47bafd": {
                            "From": "dependency/depends/out",
                            "To": "ign_bridge_depth_image/dependency/in",
                        },
                    },
                    "NodeInst": {
                        "dependency": {
                            "NodeLabel": "dependency",
                            "Template": "dependency",
                            "Visualization": {
                                "x": {"Value": 0.016466666666666668},
                                "y": {"Value": 0.0178},
                            },
                        },
                        "ign_bridge_camera_info": {
                            "CmdLine": {
                                "arg": {
                                    "Value": "/world/$(config ignition_simulator.world_scene_name)/model/$(flow robot_name)/link/$(flow frame_name)/sensor/$(flow sensor_name)/camera_info@sensor_msgs/CameraInfo[ignition.msgs.CameraInfo"
                                },
                                "remap": {
                                    "Value": "/world/$(config ignition_simulator.world_scene_name)/model/$(flow robot_name)/link/$(flow frame_name)/sensor/$(flow sensor_name)/camera_info:=/$(flow remap_topic)/camera_info"
                                },
                            },
                            "NodeLabel": "ign_bridge_camera_info",
                            "Template": "ignition_parameter_bridge",
                            "Visualization": {
                                "x": {"Value": 0.029811458333333336},
                                "y": {"Value": 0.024733333333333333},
                            },
                        },
                        "ign_bridge_depth_image": {
                            "CmdLine": {
                                "arg": {
                                    "Value": "/world/$(config ignition_simulator.world_scene_name)/model/$(flow robot_name)/link/$(flow frame_name)/sensor/$(flow sensor_name)/depth_image@sensor_msgs/Image[ignition.msgs.Image"
                                },
                                "remap": {
                                    "Value": "/world/$(config ignition_simulator.world_scene_name)/model/$(flow robot_name)/link/$(flow frame_name)/sensor/$(flow sensor_name)/depth_image:=/$(flow remap_topic)/depth_image"
                                },
                            },
                            "NodeLabel": "ign_bridge_depth_image",
                            "Template": "ignition_parameter_bridge",
                            "Visualization": {
                                "x": {"Value": 0.029678125000000003},
                                "y": {"Value": 0.012933333333333333},
                            },
                        },
                        "ign_bridge_image": {
                            "CmdLine": {
                                "arg": {
                                    "Value": "/world/$(config ignition_simulator.world_scene_name)/model/$(flow robot_name)/link/$(flow frame_name)/sensor/$(flow sensor_name)/image@sensor_msgs/Image[ignition.msgs.Image"
                                },
                                "remap": {
                                    "Value": "/world/$(config ignition_simulator.world_scene_name)/model/$(flow robot_name)/link/$(flow frame_name)/sensor/$(flow sensor_name)/image:=/$(flow remap_topic)/image_raw"
                                },
                            },
                            "NodeLabel": "ign_bridge_image",
                            "Template": "ignition_parameter_bridge",
                            "Visualization": {
                                "x": {"Value": 0.029678125000000003},
                                "y": {"Value": 0.004533333333333334},
                            },
                        },
                        "ign_bridge_point_cloud": {
                            "CmdLine": {
                                "arg": {
                                    "Value": "/world/$(config ignition_simulator.world_scene_name)/model/$(flow robot_name)/link/$(flow frame_name)/sensor/$(flow sensor_name)/points@sensor_msgs/PointCloud2[ignition.msgs.PointCloudPacked"
                                },
                                "remap": {
                                    "Value": "/world/$(config ignition_simulator.world_scene_name)/model/$(flow robot_name)/link/$(flow frame_name)/sensor/$(flow sensor_name)/points:=/$(flow remap_topic)/points"
                                },
                            },
                            "NodeLabel": "ign_bridge_point_cloud",
                            "Template": "ignition_parameter_bridge",
                            "Visualization": {
                                "x": {"Value": 0.029678125000000003},
                                "y": {"Value": 0.03306666666666667},
                            },
                        },
                        "output": {
                            "NodeLabel": "output",
                            "Parameter": {
                                "_namespace": {"Value": "$(flow remap_topic)"},
                                "_ns": {"Value": "$(flow remap_topic)"},
                            },
                            "Template": "remap_sim_depthcam",
                            "Visualization": {
                                "x": {"Value": 0.03561016438802084},
                                "y": {"Value": 0.017820330810546875},
                            },
                        },
                        "tf_camera_front": {
                            "CmdLine": {
                                "cmdline": {
                                    "Value": "$(flow lens_pose) $(flow frame_name) $(flow robot_name)/$(flow frame_name)/$(flow sensor_name)"
                                }
                            },
                            "NodeLabel": "tf_camera_front",
                            "Template": "static_transform_publisher",
                            "Visualization": {
                                "x": {"Value": 0.018662766520182294},
                                "y": {"Value": 0.007687588500976564},
                            },
                        }
                    },
                    "Parameter": {
                        "frame_name": {
                            "Description": "link that is attached the sensor in SDF model file",
                            "Value": "depth_link",
                        },
                        "lens_pose": {
                            "Description": "TF of Lens position from frame_name",
                            "Value": "0 0 0 0 0 0",
                        },
                        "remap_topic": {
                            "Description": "topic to be used in Mov.Ai",
                            "Value": "depth_image",
                        },
                        "robot_name": {
                            "Description": "Robot model name in Ignition Simulator",
                            "Value": "$(config ignition_simulator.sim_robot_name)",
                        },
                        "sensor_name": {
                            "Description": "Name of the sensor in SDF file.",
                            "Value": "depth",
                        },
                    },
                    "User": "",
                    "Version": "",
                    "VersionDelta": {},
                }
            }
        },
        version_="__UNVERSIONED__",
    )
    """
    f.save()
    print(f.select())
    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$44")
    print(Flow.select(ids=[f.pk]))
    # print(NodeInstValue.find(NodeInstValue.Template == ""))
    """
    print(f.schema_json())

