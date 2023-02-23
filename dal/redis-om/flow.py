from redis_om import JsonModel, Field, get_redis_connection, EmbeddedJsonModel, Migrator
from typing import Optional, Dict, List, Any, Union
from pydantic import constr
from common import LastUpdate, Arg
from re import search
import json



ValidName = constr(regex=r"^[a-zA-Z0-9_]+$")


class Layer(EmbeddedJsonModel):
    name: Optional[str] = None
    on: Optional[bool] = None


class CmdLineValue(EmbeddedJsonModel):
    Value: Any


class EnvVarValue(EmbeddedJsonModel):
    Value: Any


class Parameter(EmbeddedJsonModel):
    Child: Optional[str] = None
    Parent: Optional[str] = None


class Portfields(EmbeddedJsonModel):
    Message: Optional[str] = None
    Callback: Optional[str] = None
    Parameter: Optional[Parameter] = None


class X(EmbeddedJsonModel):
    Value: float


class Y(EmbeddedJsonModel):
    Value: float


class Visualization(EmbeddedJsonModel):
    x: X
    y: Y


class Visual(EmbeddedJsonModel):
    # __root__: Union[VisualItem, VisualItem1]
    Visualization: Union[List[float], Visualization]


class ContainerValue(EmbeddedJsonModel):
    ContainerFlow: Optional[str] = None
    ContainerLabel: Optional[str] = None
    # Parameter: Optional[ArgSchema] = None
    Parameter: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), Arg]] = None


class Link(EmbeddedJsonModel):
    From: constr(regex=r"^~?[a-zA-Z_0-9]+(\/~?[a-zA-Z_0-9]+){0,}$")
    To: constr(regex=r"^~?[a-zA-Z_0-9]+(\/~?[a-zA-Z_0-9]+){0,}$")


class NodeInstValue(EmbeddedJsonModel):
    NodeLabel: Optional[ValidName] = None
    Parameter: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_@]+$"), Arg]] = None
    Template: Optional[ValidName] = None
    CmdLine: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), CmdLineValue]] = None
    EnvVar: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), EnvVarValue]] = None
    NodeLayers: Optional[Any] = None


class Flow(JsonModel):
    id: str = Field(default="", index=True)
    Info: Optional[str] = None
    Label: constr(regex=r"^[a-zA-Z0-9._-]+$") = Field(index=True)
    Description: Optional[str] = None
    LastUpdate: LastUpdate
    Version: str = Field(default="__UNVERSIONED__", index=True)
    Parameter: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), Arg]] = None
    Container: Optional[Dict[constr(regex=r"^[a-zA-Z_0-9]+$"), ContainerValue]] = None
    ExposedPorts: Optional[
        Dict[
            constr(regex=r"^(__)?[a-zA-Z0-9_]+$"),
            Dict[constr(regex=r"^[a-zA-Z_0-9]+$"), List[constr(regex=r"^~?[a-zA-Z_0-9]+(\/~?[a-zA-Z_0-9]+){0,}$")]],
        ]
    ] = None
    Layers: Optional[Dict[constr(regex=r"^[0-9]+$"), Layer]] = None
    Links: Optional[Dict[constr(regex=r"^[0-9a-z-]+$"), Link]] = None
    NodeInst: Optional[Dict[constr(regex=r"^[a-zA-Z_0-9]+$"), NodeInstValue]] = None

    class Meta:
        global_key_prefix = "Models"
        model_key_prefix = "Flow"
        database = get_redis_connection(url="redis://172.17.0.2", db=0)

    class Config:
        # Force Validation in case field value change
        validate_assignment = True

    def __init__(self, *args, **kwargs):
        version = "__UNVERSIONED__"
        if "version_" in kwargs:
            version = kwargs["version_"]
        if list(kwargs.keys())[0] == "Flow":
            if kwargs is None or not isinstance(kwargs, dict):
                return
            type, struct_ = list(kwargs.items())[0]
            # TODO validate types
            if type != "Flow":
                # TODO
                raise ValueError("")

            name = list(struct_.keys())[0]
            # TODO change the id in future
            id = f"Flow:{name}:{version}"
            if search(r"^[a-zA-Z0-9_]+$", name) is None:
                raise ValueError(f"Validation Error for {type} name:({name}), data:{kwargs}")

            super().__init__(**struct_[name], id=id)
        else:
            super().__init__(*args, **kwargs)

    def dict(self):
        dic = super().dict(exclude_unset=True)
        id = dic.pop("id")
        return {"Flow": {id.split(":")[1]: dic}}

    def schema_json(self):
        schema = json.loads(super().schema_json())
        schema["properties"].pop("pk")
        schema["properties"].pop("id")
        schema["definitions"]["LastUpdate"]["properties"].pop("pk")
        return schema


Migrator().run()

f = Flow(
    **{
    "Flow": {
        "autonomous_nav": {
            "Description": "Autonomous navigation flow",
            "ExposedPorts": {
                "auto_in_mux1": {
                    "in_mux1": [
                        "nav_goal/in"
                    ]
                },
                "autonomous_main": {
                    "auto_end": [
                        "response/out",
                        "cancel_mb/in"
                    ]
                },
                "free_nav": {
                    "free_nav": [
                        "annotation/out"
                    ]
                },
                "graph_nav_cpp": {
                    "graph_nav_cpp": [
                        "annotation/out",
                        "graph/in"
                    ]
                },
                "move_base": {
                    "move_base": [
                        "cmd_vel/out",
                        "map/in",
                        "~MovaiGlobalPlanner/planner_srv/in",
                        "scored_path/out",
                        "odom/in"
                    ]
                },
                "nav_smoother": {
                    "smoother": [
                        "start/in",
                        "cmd_vel_out/out",
                        "distance_to_obstacle/in"
                    ]
                },
                "scene_sub": {
                    "scene_sub": [
                        "start/in",
                        "has_cart_pub/out"
                    ]
                },
                "traj_nav": {
                    "traj_nav": [
                        "annotation/out"
                    ]
                }
            },
            "Info": "",
            "Label": "autonomous_nav",
            "LastUpdate": {
                "date": "16/02/2023 at 14:20:25",
                "user": "movai"
            },
            "Layers": {},
            "Links": {
                "057f24d7-0a7a-4bdd-bc6d-9c662e91c6df": {
                    "From": "auto_end/move_base/cancel",
                    "To": "move_base/move_base/cancel"
                },
                "0694e867-f4de-4622-8d9c-a6ff6cff4084": {
                    "From": "scene_sub/to_planner/out",
                    "To": "graph_nav_cpp/sceneSub/in"
                },
                "0cd92145-3abe-44d0-87ef-b65490ceeb9d": {
                    "From": "traj_nav/planner/out",
                    "To": "move_base/~MovaiGlobalPlanner/planner_srv/in"
                },
                "2b3200f5-014b-427b-9d6d-b27c7f5a2c9e": {
                    "From": "move_base/~TebLocalPlannerROS/local_plan/out",
                    "To": "smoother/local_plan/in"
                },
                "2b75b6b1-d2e5-44a4-88cf-f1c4b7c08c1e": {
                    "From": "global_costmap/plugin/out",
                    "To": "move_base/global_costmap/in"
                },
                "2e863168-74b3-4704-abbf-be5e4a141f1a": {
                    "From": "free_nav/cancel_goal/out",
                    "To": "auto_end/cancel_mb/in"
                },
                "3ddd4942-d00a-4eb8-b0e9-bba857dbb03b": {
                    "From": "local_costmap/plugin/out",
                    "To": "move_base/local_costmap/in"
                },
                "3f729ccd-62d2-4061-ba45-29b432cfd7f7": {
                    "From": "in_mux2/nav_goal/out",
                    "To": "graph_nav_cpp/navigationGoal/in"
                },
                "49f6a2ab-2e7f-44ef-81c8-ba2ab6f99d6e": {
                    "From": "move_base/~TebLocalPlannerROS/local_plan/out",
                    "To": "move_base/path/in"
                },
                "5bbdd27c-962d-44aa-a6ba-0ee81159b9ee": {
                    "From": "move_base/~MovaiGlobalPlanner/resend/out",
                    "To": "auto_end/resend/in"
                },
                "6871424c-3d7a-4e73-b589-f2f6fc331c71": {
                    "From": "scene_sub/to_planner/out",
                    "To": "move_base/~MovaiGlobalPlanner/scene_sub/in"
                },
                "9171f4dd-9cbb-43f9-a482-c3b29b3b19c2": {
                    "From": "scene_sub/to_graph/out",
                    "To": "graph_nav_cpp/graphSub/in"
                },
                "986ae6d7-0159-4ac3-a60e-cf75577624f8": {
                    "From": "in_mux2/nav_goal/out",
                    "To": "free_nav/start/in"
                },
                "a131c71e-eae1-4b0f-8305-087d882fd8c5": {
                    "From": "move_base/move_base/result",
                    "To": "auto_end/move_base/result"
                },
                "a67f0f2b-1f51-4a05-8eaf-c0477364fae5": {
                    "From": "move_base/cmd_vel/out",
                    "To": "smoother/cmd_vel_in/in"
                },
                "abf251a3-4f76-444d-ba79-8c2490440ffa": {
                    "From": "teb_planner/plugin/out",
                    "To": "move_base/base_local_planner/in"
                },
                "b3bdd4b9-5c81-4e01-8d6c-ccd8eeacae7f": {
                    "From": "graph_nav_cpp/cancelGraph/out",
                    "To": "auto_end/cancel_mb/in"
                },
                "b97e697c-64a7-4e55-86aa-57e036a18857": {
                    "From": "global_planner/plugin/out",
                    "To": "move_base/base_global_planner/in"
                },
                "bebf4327-dcd5-4d80-a11a-fb2117216106": {
                    "From": "traj_nav/cancel_goal/out",
                    "To": "auto_end/cancel_mb/in"
                },
                "c82f9f5e-ac23-49db-97eb-1405fe8053af": {
                    "From": "free_nav/planner/out",
                    "To": "move_base/~MovaiGlobalPlanner/planner_srv/in"
                },
                "d0b2e20e-dfdc-4366-b3d4-b3da00628f0c": {
                    "From": "in_mux2/nav_goal/out",
                    "To": "traj_nav/start/in"
                },
                "e7ef7312-5617-462b-86c6-5d021452806a": {
                    "From": "scene_sub/has_cart_pub/out",
                    "To": "graph_nav_cpp/hasCartSub/in"
                },
                "eb70dccd-d547-4442-b4f7-05567af654bb": {
                    "From": "graph_nav_cpp/planner/out",
                    "To": "move_base/~MovaiGlobalPlanner/planner_srv/in"
                },
                "ec6d33e1-d82a-4c3c-857e-802dd6059fc1": {
                    "From": "auto_end/clear_graph_nav/out",
                    "To": "graph_nav_cpp/moveBaseReturnSub/in"
                }
            },
            "NodeInst": {
                "auto_end": {
                    "NodeLabel": "auto_end",
                    "Template": "autonomous_main",
                    "Visualization": {
                        "x": {
                            "Value": 0.06387454020182291
                        },
                        "y": {
                            "Value": 0.012627059936523442
                        }
                    }
                },
                "free_nav": {
                    "NodeLabel": "free_nav",
                    "Template": "free_nav",
                    "Visualization": {
                        "x": {
                            "Value": 0.025211458333333336
                        },
                        "y": {
                            "Value": 0.014333333333333333
                        }
                    }
                },
                "global_costmap": {
                    "NodeLabel": "global_costmap",
                    "Parameter": {
                        "always_send_full_costmap": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_costmap.always_send_full_costmap)"
                        },
                        "footprint": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).footprint.vertices)"
                        },
                        "footprint_padding": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).footprint_padding)"
                        },
                        "global_frame": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_costmap.global_frame)"
                        },
                        "inflation_layer": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_costmap.inflation_layer)"
                        },
                        "map_type": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_costmap.map_type)"
                        },
                        "obstacle_detector_layer": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_costmap.obstacle_detector_layer)"
                        },
                        "obstacle_layer": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_costmap.obstacle_layer)"
                        },
                        "plugins": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_costmap.plugins)"
                        },
                        "publish_frequency": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_costmap.publish_frequency)"
                        },
                        "publish_voxel_map": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_costmap.publish_voxel_map)"
                        },
                        "resolution": {
                            "Type": "any",
                            "Value": "0.05"
                        },
                        "robot_base_frame": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_costmap.robot_base_frame)"
                        },
                        "robot_radius": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).footprint.radius)"
                        },
                        "rolling_window": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_costmap.rolling_window)"
                        },
                        "static_layer": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_costmap.static_layer)"
                        },
                        "static_map": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_costmap.static_map)"
                        },
                        "transform_tolerance": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_costmap.transform_tolerance)"
                        },
                        "update_frequency": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_costmap.update_frequency)"
                        }
                    },
                    "Template": "global_costmap",
                    "Visualization": {
                        "x": {
                            "Value": 0.04183251546223959
                        },
                        "y": {
                            "Value": 0.04024471842447915
                        }
                    }
                },
                "global_planner": {
                    "NodeLabel": "global_planner",
                    "Parameter": {
                        "cost_threshold": {
                            "Type": "any",
                            "Value": "0"
                        },
                        "dubins_merge_max_candidates": {
                            "Type": "any",
                            "Value": "10"
                        },
                        "dubins_merge_plan_time": {
                            "Type": "any",
                            "Value": "0.1"
                        },
                        "enable_smoothing": {
                            "Type": "any",
                            "Value": "True"
                        },
                        "footprint_type": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).footprint.type)"
                        },
                        "ompl_algorithm": {
                            "Type": "any",
                            "Value": "BIT*"
                        },
                        "ompl_planning_time": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_planner.ompl_planning_time)"
                        },
                        "ompl_state_space": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_planner.ompl_state_space)"
                        },
                        "run_with_loops_flag": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_planner.run_with_loops_flag)"
                        },
                        "spline_interval": {
                            "Type": "any",
                            "Value": "10"
                        },
                        "turning_radius": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_planner.turning_radius)"
                        },
                        "w_data": {
                            "Type": "any",
                            "Value": "0.5"
                        },
                        "w_smooth": {
                            "Type": "any",
                            "Value": "0.5"
                        }
                    },
                    "Template": "movai_navigation",
                    "Visualization": {
                        "x": {
                            "Value": 0.04153402506510417
                        },
                        "y": {
                            "Value": 0.003043608601888017
                        }
                    }
                },
                "graph_nav_cpp": {
                    "NodeLabel": "graph_nav_cpp",
                    "Parameter": {
                        "max_goal_distance": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).graph_nav.max_goal_distance)"
                        },
                        "max_start_distance": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).graph_nav.max_start_distance)"
                        },
                        "weight_free": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).graph_nav.weight_free)"
                        }
                    },
                    "Template": "graph_nav_cpp",
                    "Visualization": {
                        "x": {
                            "Value": 0.02541913513825698
                        },
                        "y": {
                            "Value": 0.029334644492356756
                        }
                    }
                },
                "in_mux1": {
                    "NodeLabel": "in_mux1",
                    "Remappable": False,
                    "Template": "auto_in_mux1",
                    "Visualization": {
                        "x": {
                            "Value": 0.005423072814941405
                        },
                        "y": {
                            "Value": 0.02132752685546875
                        }
                    }
                },
                "in_mux2": {
                    "NodeLabel": "in_mux2",
                    "Remappable": False,
                    "Template": "auto_in_mux2",
                    "Visualization": {
                        "x": {
                            "Value": 0.009744791666666667
                        },
                        "y": {
                            "Value": 0.021333333333333336
                        }
                    }
                },
                "local_costmap": {
                    "NodeLabel": "local_costmap",
                    "Parameter": {
                        "footprint": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).footprint.vertices)"
                        },
                        "footprint_padding": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).footprint_padding)"
                        },
                        "global_frame": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).local_costmap.global_frame)"
                        },
                        "height": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).local_costmap.height)"
                        },
                        "inflation_layer": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).local_costmap.inflation_layer)"
                        },
                        "map_type": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).local_costmap.map_type)"
                        },
                        "obstacle_detector_layer": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).local_costmap.obstacle_detector_layer)"
                        },
                        "obstacle_layer": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).local_costmap.obstacle_layer)"
                        },
                        "origin_x": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).local_costmap.origin_x)"
                        },
                        "origin_y": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).local_costmap.origin_y)"
                        },
                        "path_scorer_layer": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).local_costmap.path_scorer_layer)"
                        },
                        "plugins": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).local_costmap.plugins)"
                        },
                        "publish_frequency": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).local_costmap.publish_frequency)"
                        },
                        "publish_voxel_map": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).local_costmap.publish_voxel_map)"
                        },
                        "resolution": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).local_costmap.resolution)"
                        },
                        "robot_base_frame": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).local_costmap.robot_base_frame)"
                        },
                        "robot_radius": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).footprint.radius)"
                        },
                        "rolling_window": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).local_costmap.rolling_window)"
                        },
                        "static_layer": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).local_costmap.static_layer)"
                        },
                        "static_map": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).local_costmap.static_map)"
                        },
                        "transform_tolerance": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).local_costmap.transform_tolerance)"
                        },
                        "update_frequency": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).local_costmap.update_frequency)"
                        },
                        "width": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).local_costmap.width)"
                        }
                    },
                    "Template": "local_costmap",
                    "Visualization": {
                        "x": {
                            "Value": 0.04164154256184896
                        },
                        "y": {
                            "Value": 0.046592744954427084
                        }
                    }
                },
                "move_base": {
                    "NodeLabel": "move_base",
                    "Parameter": {
                        "base_global_planner": {
                            "Type": "string",
                            "Value": "movai_navigation/MovaiGlobalPlanner"
                        },
                        "base_local_planner": {
                            "Type": "string",
                            "Value": "teb_local_planner/TebLocalPlannerROS"
                        },
                        "max_planning_retries": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_planner.max_planning_retries)"
                        },
                        "planner_frequency": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_planner.planner_frequency)"
                        }
                    },
                    "Template": "move_base",
                    "Visualization": {
                        "x": {
                            "Value": 0.05742945556640625
                        },
                        "y": {
                            "Value": 0.026362556966145836
                        }
                    }
                },
                "scene_sub": {
                    "NodeLabel": "scene_sub",
                    "Parameter": {
                        "update": {
                            "Type": "boolean",
                            "Value": "True"
                        }
                    },
                    "Template": "scene_sub",
                    "Visualization": {
                        "x": {
                            "Value": 0.012478122965494805
                        },
                        "y": {
                            "Value": 0.03386666666666667
                        }
                    }
                },
                "smoother": {
                    "NodeLabel": "smoother",
                    "Parameter": {
                        "xy_goal_tolerance": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.xy_goal_tolerance)"
                        },
                        "yaw_goal_tolerance": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.yaw_goal_tolerance)"
                        }
                    },
                    "Template": "nav_smoother",
                    "Visualization": {
                        "x": {
                            "Value": 0.07126215820312501
                        },
                        "y": {
                            "Value": 0.02617583821614583
                        }
                    }
                },
                "teb_planner": {
                    "NodeLabel": "teb_planner",
                    "Parameter": {
                        "acc_lim_theta": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.acc_lim_theta)"
                        },
                        "acc_lim_x": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.acc_lim_x)"
                        },
                        "allow_init_with_backwards_motion": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.allow_init_with_backwards_motion)"
                        },
                        "cmd_angle_instead_rotvel": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.cmd_angle_instead_rotvel)"
                        },
                        "costmap_converter_plugin": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).default_teb.costmap_converter_plugin)"
                        },
                        "costmap_converter_rate": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).default_teb.costmap_converter_rate)"
                        },
                        "costmap_converter_spin_thread": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).default_teb.costmap_converter_spin_thread)"
                        },
                        "costmap_obstacles_behind_robot_dist": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.costmap_obstacles_behind_robot_dist)"
                        },
                        "dt_hysteresis": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.dt_hysteresis)"
                        },
                        "dt_ref": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.dt_ref)"
                        },
                        "enable_homotopy_class_planning": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).default_teb.enable_homotopy_class_planning)"
                        },
                        "enable_multithreading": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.enable_multithreading)"
                        },
                        "feasibility_check_no_poses": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.feasibility_check_no_poses)"
                        },
                        "footprint_model": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).footprint)"
                        },
                        "free_goal_vel": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.free_goal_vel)"
                        },
                        "global_plan_overwrite_orientation": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.global_plan_overwrite_orientation)"
                        },
                        "global_plan_viapoint_sep": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.global_plan_viapoint_sep)"
                        },
                        "h_signature_prescaler": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.h_signature_prescaler)"
                        },
                        "h_signature_threshold": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.h_signature_threshold)"
                        },
                        "include_costmap_obstacles": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.include_costmap_obstacles)"
                        },
                        "inflation_dist": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.inflation_dist)"
                        },
                        "map_frame": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).default_teb.map_frame)"
                        },
                        "max_global_plan_lookahead_dist": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.max_global_plan_lookahead_dist)"
                        },
                        "max_number_classes": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.max_number_classes)"
                        },
                        "max_vel_theta": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.max_vel_theta)"
                        },
                        "max_vel_x": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.max_vel_x)"
                        },
                        "max_vel_x_backwards": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.max_vel_x_backwards)"
                        },
                        "min_obstacle_dist": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.min_obstacle_dist)"
                        },
                        "min_turning_radius": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.min_turning_radius)"
                        },
                        "no_inner_iterations": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.no_inner_iterations)"
                        },
                        "no_outer_iterations": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.no_outer_iterations)"
                        },
                        "obstacle_heading_threshold": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.obstacle_heading_threshold)"
                        },
                        "obstacle_poses_affected": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.obstacle_poses_affected)"
                        },
                        "optimization_activate": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.optimization_activate)"
                        },
                        "optimization_verbose": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.optimization_verbose)"
                        },
                        "oscillation_recovery": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.oscillation_recovery)"
                        },
                        "penalty_epsilon": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.penalty_epsilon)"
                        },
                        "publish_feedback": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.publish_feedback)"
                        },
                        "roadmap_graph_area_length_scale": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.roadmap_graph_area_length_scale)"
                        },
                        "roadmap_graph_area_width": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.roadmap_graph_area_width)"
                        },
                        "roadmap_graph_no_samples": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.roadmap_graph_no_samples)"
                        },
                        "selection_alternative_time_cost": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.selection_alternative_time_cost)"
                        },
                        "selection_viapoint_cost_scale": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.selection_viapoint_cost_scale)"
                        },
                        "teb_autosize": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.teb_autosize)"
                        },
                        "viapoints_all_candidates": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.viapoints_all_candidates)"
                        },
                        "visualize_hc_graph": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.visualize_hc_graph)"
                        },
                        "weight_acc_lim_theta": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.weight_acc_lim_theta)"
                        },
                        "weight_acc_lim_x": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.weight_acc_lim_x)"
                        },
                        "weight_dynamic_obstacle": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.weight_dynamic_obstacle)"
                        },
                        "weight_inflation": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.weight_inflation)"
                        },
                        "weight_kinematics_forward_drive": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.weight_kinematics_forward_drive)"
                        },
                        "weight_kinematics_nh": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.weight_kinematics_nh)"
                        },
                        "weight_kinematics_turning_radius": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.weight_kinematics_turning_radius)"
                        },
                        "weight_max_vel_theta": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.weight_max_vel_theta)"
                        },
                        "weight_max_vel_x": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.weight_max_vel_x)"
                        },
                        "weight_obstacle": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.weight_obstacle)"
                        },
                        "weight_optimaltime": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.weight_optimaltime)"
                        },
                        "weight_shortest_path": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.weight_shortest_path)"
                        },
                        "weight_viapoint": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.weight_viapoint)"
                        },
                        "wheelbase": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.wheelbase)"
                        },
                        "xy_goal_tolerance": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.xy_goal_tolerance)"
                        },
                        "yaw_goal_tolerance": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).move_base.TebLocalPlannerROS.yaw_goal_tolerance)"
                        }
                    },
                    "Template": "TebLocalPlannerROS",
                    "Visualization": {
                        "x": {
                            "Value": 0.04171290283203125
                        },
                        "y": {
                            "Value": 0.010157687377929691
                        }
                    }
                },
                "traj_nav": {
                    "NodeLabel": "traj_nav",
                    "Parameter": {
                        "default_ompl_ss": {
                            "Type": "any",
                            "Value": "$(config $(flow navigation_configuration).global_planner.ompl_state_space)"
                        }
                    },
                    "Template": "traj_nav",
                    "Visualization": {
                        "x": {
                            "Value": 0.025408487955729166
                        },
                        "y": {
                            "Value": 0.02148745524088542
                        }
                    }
                }
            },
            "Parameter": {
                "navigation_configuration": {
                    "Description": "Navigation configuration file",
                    "Type": "any",
                    "Value": "\"\""
                }
            },
            "User": "",
            "Version": "",
            "VersionDelta": {}
        }
    }
}
)
f.save()
print(Flow.find(Flow.id == "Flow:autonomous_nav:__UNVERSIONED__").first())

print(f.NodeInst.keys())