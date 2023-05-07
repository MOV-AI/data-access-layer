from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, constr
from pydantic.config import BaseConfig
from base import MovaiBaseModel


class Graph(BaseModel):
    keyValueMap: Optional[Dict[str, Any]] = None


class KeyValMap(BaseModel):
    behaviour: Optional[str] = None


class Annotation1(BaseModel):
    Value: Optional[str] = None


class Position(BaseModel):
    orientation: Optional[Dict[constr(regex=r"^[xyzw]$"), float]] = None
    position: Optional[Dict[constr(regex=r"^[xyz]$"), float]] = None


class RobotTreeValue(Position):
    child: Optional[List] = None
    name: Optional[str] = None


class Value2(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    robotTree: Optional[RobotTreeValue] = None
    type: Optional[str] = None
    image: Optional[str] = None
    origin: Optional[List[float]] = None
    resolution: Optional[float] = None
    size: Optional[List[float]] = None


class Assets(BaseModel):
    # Value: Optional[
    #     Union[
    #         Dict[constr(regex=r'^[a-zA-Z0-9_]+[.]png$'), Value2],
    #         Dict[constr(regex=r'^[a-zA-Z0-9_]+$'), Value2],
    #     ]
    # ] = None
    Value: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+[.]png$|^[a-zA-Z0-9_]+$"), Value2]] = None


class Value3(BaseModel):
    keypoints: Optional[List[float]] = None
    trajectory: Optional[List[float]] = None


class Coordinate(BaseModel):
    __root__: List[float] = Field(..., max_items=2, min_items=2)


class Val(BaseModel):
    polygon: Optional[List[Coordinate]] = None


class BehaviourValue(BaseModel):
    Value: str


class AnnotationValue(BaseModel):
    behaviour: BehaviourValue


class AssetNameValue(BaseModel):
    Value: Val
    # Annotation: Optional[Annotation1] = None
    Annotation: Optional[Dict[constr(regex=r"^[0-9]+$"), Annotation1]] = None


class AssetName6(BaseModel):
    Value: Value3
    # Annotation: Optional[AnnotationValue] = None https://movai.atlassian.net/browse/BP-732
    Annotation: Union[
        Optional[Dict[constr(regex=r"^[0-9]+$"), Annotation1]], Optional[AnnotationValue]
    ] = None


class Path1(BaseModel):
    AssetName: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), AssetName6]] = None


class BelongsObj(BaseModel):
    index: Optional[int] = None
    name: Optional[str] = None


class Field3arrayPoint(BaseModel):
    __root__: List[float] = Field(..., max_items=3, min_items=3)


class VerticesValue(BaseModel):
    id: Optional[Any] = None
    position: Optional[Field3arrayPoint] = None


class Edge(BaseModel):
    belongsSrc: Optional[BelongsObj] = None
    belongsTrg: Optional[BelongsObj] = None
    ids: Optional[List[str]] = None
    keyValueMap: Optional[Any] = None
    weight: Optional[int] = None


class Item(BaseModel):
    class Config(BaseConfig):
        exclude = ["old_name"]

    color: Optional[List] = None
    weight: Optional[int] = None
    keyValueMap: Optional[Dict[str, Any]] = None
    localPath: Optional[List[List[float]]] = None
    name: Optional[str] = None
    position: Optional[List[float]] = None
    quaternion: Optional[List[float]] = None
    splinePath: Optional[List[List[float]]] = None
    type: Optional[str] = None
    isVisible: Optional[bool] = None
    annotationPropOverrides: Optional[Any] = None
    assetName: Optional[str] = None
    size: Optional[List[float]] = None
    vertices: Optional[Dict[constr(regex=r"^[0-9]+$"), VerticesValue]] = None
    edges: Optional[Dict[constr(regex=r"^[0-9]+(_[0-9]+)?$"), Edge]] = None
    corners: Optional[List[Field3arrayPoint]] = None
    # fields that are missing in the schema added for determine item type
    # or to prevent failures in comparison after update
    localPolygon: Optional[List[List[float]]] = None
    isSubscribedToLogs: Optional[bool] = None  # is related to determine Robot type?!
    navigationAllowed: Optional[bool] = None
    old_name: Optional[str] = None


class MemoryValueObj(BaseModel):
    children: Optional[List["MemoryValueObj"]] = None
    item: Optional[Item] = None
    name: Optional[str] = None


class BoxRegionValue(BaseModel):
    AssetName: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), AssetNameValue]] = None


class GlobalrefValue(BaseModel):
    Value: Optional[Position] = None


class AssetName1(BaseModel):
    Globalref: Optional[GlobalrefValue] = None


class GlobalRefValue(BaseModel):
    AssetName: Optional[AssetName1] = None


class Link(BaseModel):
    belongsSrc: Optional[BelongsObj] = None
    belongsTrg: Optional[BelongsObj] = None
    keyValueMap: Optional[KeyValMap] = None
    source: Optional[str] = None
    target: Optional[str] = None
    weight: Optional[int] = None


class Value1(BaseModel):
    directed: Optional[bool] = None
    graph: Optional[Graph] = None
    links: Optional[List[Link]] = None


class LogicGraphValue(BaseModel):
    Value: Optional[Value1] = None


class AssetName2(BaseModel):
    LogicGraph: Optional[LogicGraphValue] = None


class GraphItemValue(BaseModel):
    AssetName: Optional[AssetName2] = None


class AssetName3(BaseModel):
    Value: Optional[Position] = None
    Annotation: Optional[Dict[constr(regex=r"^[0-9]+$"), Annotation1]] = None


class KeyPointValue(BaseModel):
    # AssetName: Optional[Dict[constr(regex=r'^[a-zA-Z0-9]+$'), AssetName3]] = None  https://movai.atlassian.net/browse/BP-696
    AssetName: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_-]+$"), AssetName3]] = None


class AssetName4(BaseModel):
    Value: Optional[Position] = None


class MapValue(BaseModel):
    # AssetName: Optional[
    #     Dict[constr(regex=r'^[a-zA-Z0-9_]+([.][a-zA-Z0-9]+)?$'), AssetName4]
    # ] = None  https://movai.atlassian.net/browse/BP-708
    AssetName: Optional[
        Dict[constr(regex=r"^[a-zA-Z0-9_-]+([.][a-zA-Z0-9]+)?$"), AssetName4]
    ] = None


class RobotTree(Position):
    child: Optional[List] = None
    name: Optional[str] = None


class Tree(BaseModel):
    Value: Optional[List[MemoryValueObj]] = None


class AssetName5(BaseModel):
    assets: Optional[Assets] = None
    tree: Optional[Tree] = None


class MemoryValue(BaseModel):
    AssetName: Optional[AssetName5] = None


class AssetName6(BaseModel):
    Value: Optional[Value3] = None
    Annotation: Optional[AnnotationValue] = None


class Path(BaseModel):
    AssetName: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), AssetName6]] = None


class AssetName7(BaseModel):
    Value: Optional[Position] = None


class PointCloudValue(BaseModel):
    AssetName: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_.-]+$"), AssetName7]] = None


class Value4(BaseModel):
    polygon: Optional[List[Coordinate]] = None
    navigationAllowed: Optional[bool] = None


class AssetName8(BaseModel):
    Value: Optional[Value4] = None


class PolygonRegionValue(BaseModel):
    AssetName: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), AssetName8]] = None


class AssetName9(BaseModel):
    Value: Optional[Position] = None


class RobotValue(BaseModel):
    AssetName: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), AssetName9]] = None


class AssetType(BaseModel):
    BoxRegion: Optional[BoxRegionValue] = None
    GlobalRef: Optional[GlobalRefValue] = None
    GraphItem: Optional[GraphItemValue] = None
    KeyPoint: Optional[KeyPointValue] = None
    Map: Optional[MapValue] = None
    memory: Optional[MemoryValue] = None
    Path: Optional[Path1] = None
    PointCloud: Optional[PointCloudValue] = None
    PolygonRegion: Optional[PolygonRegionValue] = None
    Robot: Optional[RobotValue] = None


class GraphicScene(MovaiBaseModel):
    AssetType: AssetType


if __name__ == "__main__":
    # small test
    g = GraphicScene(
        **{
            "GraphicScene": {
                "movai_lab_loop": {
                    "AssetType": {
                        "GlobalRef": {
                            "AssetName": {
                                "Globalref": {
                                    "Value": {
                                        "orientation": {"w": 1.0, "x": 0, "y": 0, "z": 0.0},
                                        "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                                    }
                                }
                            }
                        },
                        "GraphItem": {
                            "AssetName": {
                                "LogicGraph": {
                                    "Value": {
                                        "directed": True,
                                        "graph": {"annotationPropOverrides": {}, "keyValueMap": {}},
                                        "links": [
                                            {
                                                "annotationPropOverrides": {},
                                                "belongsSrc": {"index": 0, "name": "Path337"},
                                                "belongsTrg": {"index": -1, "name": "Path337"},
                                                "keyValueMap": {},
                                                "source": "53",
                                                "target": "54",
                                                "weight": 1,
                                            },
                                            {
                                                "annotationPropOverrides": {},
                                                "belongsSrc": {"index": 0, "name": "Path85"},
                                                "belongsTrg": {"index": -1, "name": "Path85"},
                                                "keyValueMap": {},
                                                "source": "103",
                                                "target": "104",
                                                "weight": 1,
                                            },
                                            {
                                                "annotationPropOverrides": {},
                                                "belongsSrc": {"index": 0, "name": "Path187"},
                                                "belongsTrg": {"index": -1, "name": "Path187"},
                                                "keyValueMap": {},
                                                "source": "105",
                                                "target": "106",
                                                "weight": 1,
                                            },
                                            {
                                                "annotationPropOverrides": {},
                                                "belongsSrc": {"index": 0, "name": "Path430"},
                                                "belongsTrg": {"index": -1, "name": "Path430"},
                                                "keyValueMap": {},
                                                "source": "107",
                                                "target": "108",
                                                "weight": 1,
                                            },
                                            {
                                                "annotationPropOverrides": {},
                                                "belongsSrc": {"index": 0, "name": "Path707"},
                                                "belongsTrg": {"index": -1, "name": "Path707"},
                                                "keyValueMap": {},
                                                "source": "109",
                                                "target": "110",
                                                "weight": 1,
                                            },
                                            {
                                                "annotationPropOverrides": {},
                                                "belongsSrc": {"index": 0, "name": "Path319"},
                                                "belongsTrg": {"index": -1, "name": "Path319"},
                                                "keyValueMap": {},
                                                "source": "111",
                                                "target": "112",
                                                "weight": 1,
                                            },
                                            {
                                                "annotationPropOverrides": {},
                                                "belongsSrc": {"name": "KeyPoint346"},
                                                "belongsTrg": {"index": 0, "name": "Path85"},
                                                "keyValueMap": {},
                                                "source": "113",
                                                "target": "103",
                                                "weight": 1,
                                            },
                                            {
                                                "annotationPropOverrides": {},
                                                "belongsSrc": {"index": -1, "name": "Path319"},
                                                "belongsTrg": {"name": "KeyPoint346"},
                                                "keyValueMap": {},
                                                "source": "112",
                                                "target": "113",
                                                "weight": 1,
                                            },
                                            {
                                                "annotationPropOverrides": {},
                                                "belongsSrc": {"index": -1, "name": "Path85"},
                                                "belongsTrg": {"name": "KeyPoint849"},
                                                "keyValueMap": {},
                                                "source": "104",
                                                "target": "114",
                                                "weight": 1,
                                            },
                                            {
                                                "annotationPropOverrides": {},
                                                "belongsSrc": {"name": "KeyPoint849"},
                                                "belongsTrg": {"index": 0, "name": "Path187"},
                                                "keyValueMap": {},
                                                "source": "114",
                                                "target": "105",
                                                "weight": 1,
                                            },
                                            {
                                                "annotationPropOverrides": {},
                                                "belongsSrc": {"index": -1, "name": "Path187"},
                                                "belongsTrg": {"name": "KeyPoint766"},
                                                "keyValueMap": {},
                                                "source": "106",
                                                "target": "115",
                                                "weight": 1,
                                            },
                                            {
                                                "annotationPropOverrides": {},
                                                "belongsSrc": {"name": "KeyPoint766"},
                                                "belongsTrg": {"index": 0, "name": "Path430"},
                                                "keyValueMap": {},
                                                "source": "115",
                                                "target": "107",
                                                "weight": 1,
                                            },
                                            {
                                                "annotationPropOverrides": {},
                                                "belongsSrc": {"index": -1, "name": "Path430"},
                                                "belongsTrg": {"name": "KeyPoint969"},
                                                "keyValueMap": {},
                                                "source": "108",
                                                "target": "116",
                                                "weight": 1,
                                            },
                                            {
                                                "annotationPropOverrides": {},
                                                "belongsSrc": {"name": "KeyPoint969"},
                                                "belongsTrg": {"index": 0, "name": "Path707"},
                                                "keyValueMap": {},
                                                "source": "116",
                                                "target": "109",
                                                "weight": 1,
                                            },
                                            {
                                                "annotationPropOverrides": {},
                                                "belongsSrc": {"index": -1, "name": "Path707"},
                                                "belongsTrg": {"name": "KeyPoint570"},
                                                "keyValueMap": {},
                                                "source": "110",
                                                "target": "117",
                                                "weight": 1,
                                            },
                                            {
                                                "annotationPropOverrides": {},
                                                "belongsSrc": {"name": "KeyPoint570"},
                                                "belongsTrg": {"index": 0, "name": "Path319"},
                                                "keyValueMap": {},
                                                "source": "117",
                                                "target": "111",
                                                "weight": 1,
                                            },
                                        ],
                                        "multigraph": False,
                                        "nodes": [
                                            {
                                                "id": "53",
                                                "position": [
                                                    -10.224956671439001,
                                                    -4.740004003171121,
                                                    -0.009999999776485056,
                                                ],
                                            },
                                            {
                                                "id": "54",
                                                "position": [
                                                    -12.876467750733664,
                                                    -4.979085439136518,
                                                    -1.6531914726058972e-15,
                                                ],
                                            },
                                            {
                                                "id": "103",
                                                "position": [
                                                    -8.559836061091378,
                                                    0.48509471388777925,
                                                    1.0685896612017132e-15,
                                                ],
                                            },
                                            {
                                                "id": "104",
                                                "position": [
                                                    -6.163119022801997,
                                                    1.4123073273888096,
                                                    -5.0133508455729725e-16,
                                                ],
                                            },
                                            {
                                                "id": "105",
                                                "position": [
                                                    -4.849069311213661,
                                                    1.1598590643299715,
                                                    -9.228728892196614e-16,
                                                ],
                                            },
                                            {
                                                "id": "106",
                                                "position": [
                                                    -1.8130148390952243,
                                                    -1.4146148101732834,
                                                    2.8275992658421956e-16,
                                                ],
                                            },
                                            {
                                                "id": "107",
                                                "position": [
                                                    -0.6631162431236213,
                                                    -2.767322869509148,
                                                    3.930883396563445e-15,
                                                ],
                                            },
                                            {
                                                "id": "108",
                                                "position": [
                                                    -5.332850789979503,
                                                    -4.899330151822754,
                                                    -1.93421667571414e-15,
                                                ],
                                            },
                                            {
                                                "id": "109",
                                                "position": [
                                                    -6.827555157153515,
                                                    -4.8864951846926825,
                                                    -2.6385144069607236e-15,
                                                ],
                                            },
                                            {
                                                "id": "110",
                                                "position": [
                                                    -14.854018773223643,
                                                    -5.549911676284954,
                                                    -9.315465065995454e-16,
                                                ],
                                            },
                                            {
                                                "id": "111",
                                                "position": [
                                                    -14.647393954810356,
                                                    -4.785705160813116,
                                                    -4.0419056990259605e-16,
                                                ],
                                            },
                                            {
                                                "id": "112",
                                                "position": [
                                                    -9.51397993883185,
                                                    -0.3771342296378002,
                                                    4.909267437014364e-16,
                                                ],
                                            },
                                            {
                                                "id": "113",
                                                "position": [
                                                    -9.202796673443528,
                                                    0.0877331633437386,
                                                    0.23999999463558197,
                                                ],
                                            },
                                            {
                                                "id": "114",
                                                "position": [
                                                    -5.661125183105469,
                                                    1.4941043853759766,
                                                    0.23999999463558197,
                                                ],
                                            },
                                            {
                                                "id": "115",
                                                "position": [
                                                    -1.2502803802490234,
                                                    -1.9700736999511719,
                                                    0.23999999463558197,
                                                ],
                                            },
                                            {
                                                "id": "116",
                                                "position": [
                                                    -5.950048446655273,
                                                    -4.767441749572754,
                                                    0.23999999463558197,
                                                ],
                                            },
                                            {
                                                "id": "117",
                                                "position": [
                                                    -15.181180000305176,
                                                    -5.167583465576172,
                                                    0.23999999463558197,
                                                ],
                                            },
                                        ],
                                    }
                                }
                            }
                        },
                        "KeyPoint": {
                            "AssetName": {
                                "KeyPoint346": {
                                    "Value": {
                                        "orientation": {
                                            "w": 0.9669151281693759,
                                            "x": 0,
                                            "y": 0,
                                            "z": 0.2550982848182234,
                                        },
                                        "position": {
                                            "x": -9.202796673443528,
                                            "y": 0.0877331633437386,
                                            "z": 0.23999999463558197,
                                        },
                                    }
                                },
                                "KeyPoint570": {
                                    "Value": {
                                        "orientation": {
                                            "w": 0.9524135400750127,
                                            "x": 0,
                                            "y": 0,
                                            "z": 0.30480887238035265,
                                        },
                                        "position": {
                                            "x": -15.181180000305176,
                                            "y": -5.167583465576172,
                                            "z": 0.23999999463558197,
                                        },
                                    }
                                },
                                "KeyPoint766": {
                                    "Value": {
                                        "orientation": {
                                            "w": 0.8936553061931966,
                                            "x": 0,
                                            "y": 0,
                                            "z": -0.44875404590125323,
                                        },
                                        "position": {
                                            "x": -1.2502803802490234,
                                            "y": -1.9700736999511719,
                                            "z": 0.23999999463558197,
                                        },
                                    }
                                },
                                "KeyPoint849": {
                                    "Value": {
                                        "orientation": {
                                            "w": 0.9732407263340314,
                                            "x": 0,
                                            "y": 0,
                                            "z": -0.2297879209288579,
                                        },
                                        "position": {
                                            "x": -5.661125183105469,
                                            "y": 1.4941043853759766,
                                            "z": 0.23999999463558197,
                                        },
                                    }
                                },
                                "KeyPoint969": {
                                    "Value": {
                                        "orientation": {
                                            "w": 0.01907374668794539,
                                            "x": 0,
                                            "y": 0,
                                            "z": -0.9998180795461162,
                                        },
                                        "position": {
                                            "x": -5.950048446655273,
                                            "y": -4.767441749572754,
                                            "z": 0.23999999463558197,
                                        },
                                    }
                                },
                            }
                        },
                        "Map": {
                            "AssetName": {
                                "movai_lab": {
                                    "Value": {
                                        "orientation": {"w": 1.0, "x": 0, "y": 0, "z": 0.0},
                                        "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                                    }
                                }
                            }
                        },
                        "Path": {
                            "AssetName": {
                                "Path187": {
                                    "Value": {
                                        "isBidirectional": False,
                                        "keypoints": [
                                            -4.849069311213661,
                                            1.1598590643299715,
                                            -3.520321046806398,
                                            0.17854372126653573,
                                            -1.8130148390952243,
                                            -1.4146148101732834,
                                        ],
                                        "trajectory": [
                                            -4.849069311213661,
                                            1.1598590643299715,
                                            -0.6198221697242012,
                                            -4.7322893626226605,
                                            1.0765201545053729,
                                            -0.6072084191557733,
                                            -4.577311165823891,
                                            0.9688456877705925,
                                            -0.6084441261758403,
                                            -4.392445423334294,
                                            0.8400671990062757,
                                            -0.6176529902503994,
                                            -4.186002837670807,
                                            0.6934162230930668,
                                            -0.633258305104044,
                                            -3.9662941113503694,
                                            0.5321242949116108,
                                            -0.6553676856820654,
                                            -3.7416299468899203,
                                            0.35942294934255253,
                                            -0.6852104487886319,
                                            -3.520321046806398,
                                            0.17854372126653573,
                                            -0.7195959356965154,
                                            -3.281353467151848,
                                            -0.030876296937824885,
                                            -0.7403158995248384,
                                            -3.0103352688174505,
                                            -0.2784972165937875,
                                            -0.752239660116522,
                                            -2.7255101615788475,
                                            -0.5450333083735136,
                                            -0.7593813987484149,
                                            -2.4451218552116813,
                                            -0.8111988429491649,
                                            -0.7631920379965941,
                                            -2.1874140594915943,
                                            -1.0577080909929024,
                                            -0.7636828885820427,
                                            -1.9706304841942277,
                                            -1.265275323176888,
                                            -0.7584425837513429,
                                            -1.8130148390952245,
                                            -1.4146148101732834,
                                            -0.7584425837513429,
                                        ],
                                        "weight": 1,
                                    }
                                },
                                "Path319": {
                                    "Value": {
                                        "isBidirectional": False,
                                        "keypoints": [
                                            -14.647393954810353,
                                            -4.785705160813117,
                                            -13.325123606941307,
                                            -4.19217340565167,
                                            -10.853940029103242,
                                            -3.63469682484342,
                                            -10.02770637016462,
                                            -1.2311025568295502,
                                            -9.513979938831849,
                                            -0.3771342296378002,
                                        ],
                                        "trajectory": [
                                            -14.647393954810353,
                                            -4.785705160813117,
                                            0.45800269208020866,
                                            -14.537937275235912,
                                            -4.731746997742958,
                                            0.48751390941904305,
                                            -14.39947382916968,
                                            -4.658333820083327,
                                            0.4845600609816733,
                                            -14.233519859625366,
                                            -4.570972219054471,
                                            0.46297758513038373,
                                            -14.041591609616669,
                                            -4.475168785876631,
                                            0.4280868037605259,
                                            -13.825205322157291,
                                            -4.3764301117700555,
                                            0.3820762062322802,
                                            -13.585877240260935,
                                            -4.280262787954986,
                                            0.3257885774315126,
                                            -13.325123606941307,
                                            -4.19217340565167,
                                            0.20976439363739294,
                                            -13.018002887024918,
                                            -4.126788587761451,
                                            0.1170435543122925,
                                            -12.654853463886207,
                                            -4.0840891275001185,
                                            0.09214363730362526,
                                            -12.260111458360756,
                                            -4.047612871559576,
                                            0.11571705302620479,
                                            -11.85821299128415,
                                            -4.0008976666317295,
                                            0.18861182342524946,
                                            -11.473594183491974,
                                            -3.9274813594084845,
                                            0.3277189883504462,
                                            -11.13069115581981,
                                            -3.8109017965817467,
                                            0.566962240582852,
                                            -10.853940029103242,
                                            -3.63469682484342,
                                            0.8982731057174882,
                                            -10.64684944743852,
                                            -3.37465344704329,
                                            1.1327931659879715,
                                            -10.488867962559425,
                                            -3.037333689294033,
                                            1.267328152290316,
                                            -10.36834155675785,
                                            -2.652437933181898,
                                            1.3398100928495755,
                                            -10.27361621232569,
                                            -2.2496665602931336,
                                            1.367532004561411,
                                            -10.193037911554836,
                                            -1.8587199522139888,
                                            1.3509384711072783,
                                            -10.114952636737181,
                                            -1.5092984905307112,
                                            1.2668964751599066,
                                            -10.02770637016462,
                                            -1.2311025568295502,
                                            1.1501982362436152,
                                            -9.933423849680043,
                                            -1.0203164928389696,
                                            1.0852846827729135,
                                            -9.843172448082736,
                                            -0.8492680732806812,
                                            1.019619619715179,
                                            -9.758712100099174,
                                            -0.711872829230805,
                                            0.9598822722420051,
                                            -9.68180274045583,
                                            -0.6020462917654594,
                                            0.9176457703421342,
                                            -9.614204303879177,
                                            -0.5137039919607642,
                                            0.9115109501920138,
                                            -9.557676725095693,
                                            -0.44076146089283785,
                                            0.9690100571570237,
                                            -9.513979938831849,
                                            -0.3771342296378011,
                                            0.9690100571570237,
                                        ],
                                        "weight": 1,
                                    }
                                },
                                "Path337": {
                                    "Value": {
                                        "isBidirectional": False,
                                        "keypoints": [
                                            -10.224956671439001,
                                            -4.740004003171121,
                                            -10.873124832341011,
                                            -4.942379132367244,
                                            -11.649930635174414,
                                            -4.969301738626982,
                                            -12.876467750733664,
                                            -4.979085439136518,
                                        ],
                                        "trajectory": [
                                            -10.224956671439001,
                                            -4.740004003171121,
                                            -2.8093352067985715,
                                            -10.282412356751443,
                                            -4.759829036914238,
                                            -2.7875950172989654,
                                            -10.359154628659214,
                                            -4.7881903287124645,
                                            -2.789680757802432,
                                            -10.45063948845411,
                                            -4.8217832635325735,
                                            -2.8055246261151217,
                                            -10.552322937427935,
                                            -4.857303226341334,
                                            -2.8336298611388346,
                                            -10.659660976872493,
                                            -4.891445602105519,
                                            -2.8763426860316197,
                                            -10.768109608079584,
                                            -4.920905775791899,
                                            -2.939894566338532,
                                            -10.873124832341011,
                                            -4.942379132367244,
                                            -3.010690667604343,
                                            -10.973412916439829,
                                            -4.955582542970255,
                                            -3.063335763740067,
                                            -11.072581725933228,
                                            -4.963359066898923,
                                            -3.104584167748902,
                                            -11.173439660274223,
                                            -4.96709337135896,
                                            -3.1313728251760953,
                                            -11.278795118915827,
                                            -4.968170123556074,
                                            3.139851749494838,
                                            -11.391456501311051,
                                            -4.967973990695976,
                                            3.140905622732056,
                                            -11.51423220691291,
                                            -4.967889639984375,
                                            -3.1311868759187873,
                                            -11.649930635174414,
                                            -4.969301738626982,
                                            -3.1269172923961266,
                                            -11.812276892842098,
                                            -4.97168439964739,
                                            -3.131402582680658,
                                            -12.003349660428796,
                                            -4.973631512092828,
                                            -3.133910684264923,
                                            -12.208487698036967,
                                            -4.97520740720447,
                                            -3.1353885863704165,
                                            -12.413029765769078,
                                            -4.9764764162234885,
                                            -3.136169905477527,
                                            -12.602314623727588,
                                            -4.977502870391055,
                                            -3.1362701859716755,
                                            -12.761681032014963,
                                            -4.97835110094834,
                                            -3.1351953266293515,
                                            -12.876467750733664,
                                            -4.979085439136518,
                                            -3.1351953266293515,
                                        ],
                                        "weight": 1,
                                    }
                                },
                                "Path430": {
                                    "Value": {
                                        "isBidirectional": False,
                                        "keypoints": [
                                            -0.6631162431236213,
                                            -2.767322869509148,
                                            -0.7899201570517747,
                                            -4.350799311228098,
                                            -2.677399440837899,
                                            -5.009204209688438,
                                            -5.332850789979503,
                                            -4.899330151822754,
                                        ],
                                        "trajectory": [
                                            -0.6631162431236213,
                                            -2.767322869509148,
                                            -1.544750790362449,
                                            -0.6591771621387781,
                                            -2.9185269054364458,
                                            -1.4751882140868275,
                                            -0.638772021602267,
                                            -3.1313009910195544,
                                            -1.4815708379798056,
                                            -0.6161912424114329,
                                            -3.38370447332864,
                                            -1.5320659884939483,
                                            -0.6057252454636213,
                                            -3.6537966994338706,
                                            -1.6306824543084983,
                                            -0.6216644516561773,
                                            -3.919637016405412,
                                            -1.802863867139227,
                                            -0.6782992818864466,
                                            -4.159284771313432,
                                            -2.098496925680139,
                                            -0.7899201570517747,
                                            -4.350799311228098,
                                            -2.4223865472993786,
                                            -0.9604461397106965,
                                            -4.500122823391917,
                                            -2.608642050337509,
                                            -1.1784809876961946,
                                            -4.628738839490019,
                                            -2.7393465311762286,
                                            -1.435342164817286,
                                            -4.738018723256509,
                                            -2.8335545787514977,
                                            -1.7223471348829855,
                                            -4.829333838425493,
                                            -2.903934265910742,
                                            -2.03081336170231,
                                            -4.904055548731072,
                                            -2.9584521487198097,
                                            -2.3520583090842755,
                                            -4.963555217907352,
                                            -3.002191546084234,
                                            -2.677399440837899,
                                            -5.009204209688438,
                                            -3.076374061345082,
                                            -3.039673414537505,
                                            -5.032864764221537,
                                            3.1361856218908297,
                                            -3.4575435926554094,
                                            -5.030605304903181,
                                            3.0954074150363544,
                                            -3.9010674963476166,
                                            -5.010106470341461,
                                            3.0710018396637175,
                                            -4.340302646770127,
                                            -4.979048899144468,
                                            3.057996963161233,
                                            -4.745306565078943,
                                            -4.945113229920292,
                                            3.0563229634318834,
                                            -5.086136772430068,
                                            -4.9159801012770235,
                                            3.074207990089317,
                                            -5.332850789979502,
                                            -4.899330151822754,
                                            3.074207990089317,
                                        ],
                                        "weight": 1,
                                    }
                                },
                                "Path707": {
                                    "Value": {
                                        "isBidirectional": False,
                                        "keypoints": [
                                            -6.8275551571535225,
                                            -4.886495184692683,
                                            -9.767196300802157,
                                            -5.49415183717812,
                                            -13.50206236260263,
                                            -5.981313470677949,
                                            -14.854018773223643,
                                            -5.549911676284954,
                                        ],
                                        "trajectory": [
                                            -6.8275551571535225,
                                            -4.886495184692683,
                                            -2.9285345742337388,
                                            -7.086281689802655,
                                            -4.94246848289678,
                                            -2.9215871371239377,
                                            -7.430008668246327,
                                            -5.019334501955928,
                                            -2.922260728602914,
                                            -7.8399802654393795,
                                            -5.110724568358718,
                                            -2.9273284019589076,
                                            -8.29744065433665,
                                            -5.2102700085937395,
                                            -2.9361147526378204,
                                            -8.783634007892978,
                                            -5.311602149149587,
                                            -2.9490153532039147,
                                            -9.2798044990632,
                                            -5.40835231651485,
                                            -2.9673399241943397,
                                            -9.767196300802157,
                                            -5.49415183717812,
                                            -2.97927644678934,
                                            -10.279858450816818,
                                            -5.578103792475237,
                                            -2.982511625091331,
                                            -10.845812474605204,
                                            -5.668903585972731,
                                            -2.9894796369195573,
                                            -11.437261276808734,
                                            -5.759571027505235,
                                            -3.0007085773929743,
                                            -12.026407762068823,
                                            -5.843125926907377,
                                            -3.0179751875382554,
                                            -12.58545483502689,
                                            -5.91258809401379,
                                            -3.0453347541420985,
                                            -13.086605400324354,
                                            -5.960977338659104,
                                            -3.0926828615678557,
                                            -13.50206236260263,
                                            -5.981313470677949,
                                            3.0895279232881854,
                                            -13.832074336577916,
                                            -5.96411594412878,
                                            2.9520087223776637,
                                            -14.101432723029907,
                                            -5.912429190511411,
                                            2.8124415783969665,
                                            -14.319154605695267,
                                            -5.838060485822508,
                                            2.6885445352214505,
                                            -14.494257068310658,
                                            -5.752817106058742,
                                            2.60424101495102,
                                            -14.635757194612742,
                                            -5.6685063272167815,
                                            2.5922781002754065,
                                            -14.752672068338184,
                                            -5.596935425293296,
                                            2.7071666214611425,
                                            -14.854018773223643,
                                            -5.549911676284954,
                                            2.7071666214611425,
                                        ],
                                        "weight": 1,
                                    }
                                },
                                "Path85": {
                                    "Value": {
                                        "isBidirectional": False,
                                        "keypoints": [
                                            -8.559836061091378,
                                            0.48509471388777925,
                                            -6.957495394201835,
                                            1.09289028586943,
                                            -6.163119022801997,
                                            1.4123073273888096,
                                        ],
                                        "trajectory": [
                                            -8.559836061091378,
                                            0.48509471388777925,
                                            0.36163901454114294,
                                            -8.407951356834687,
                                            0.5425489364032836,
                                            0.3610315128856129,
                                            -8.195257309960668,
                                            0.6228581601247566,
                                            0.36108776144403903,
                                            -7.9428353049799245,
                                            0.7181841275964205,
                                            0.3615290329868338,
                                            -7.671766726403065,
                                            0.8206885813624976,
                                            0.3623786325896307,
                                            -7.403132958740692,
                                            0.9225332639672099,
                                            0.3638668396117322,
                                            -7.158015386503415,
                                            1.01587991795478,
                                            0.36668410430717785,
                                            -6.957495394201835,
                                            1.09289028586943,
                                            0.37214568745958243,
                                            -6.794664698482866,
                                            1.1564485940540616,
                                            0.37791914784961034,
                                            -6.64848152977494,
                                            1.2144835912503331,
                                            0.38301993082440505,
                                            -6.518827043260942,
                                            1.2667238036006023,
                                            0.387157754629015,
                                            -6.405582394123762,
                                            1.3128977572472271,
                                            0.38984949956973797,
                                            -6.308628737546286,
                                            1.3527339783325647,
                                            0.3902263711174415,
                                            -6.2278472287114015,
                                            1.385960992998973,
                                            0.38655216152929217,
                                            -6.163119022801997,
                                            1.4123073273888096,
                                            0.38655216152929217,
                                        ],
                                        "weight": 1,
                                    }
                                },
                            }
                        },
                        "PointCloud": {
                            "AssetName": {
                                "movai_lab_edges.pcd93": {
                                    "Value": {
                                        "orientation": {"w": 1.0, "x": 0, "y": 0, "z": 0.0},
                                        "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                                    }
                                },
                                "movai_lab_planes.pcd89": {
                                    "Value": {
                                        "orientation": {"w": 1.0, "x": 0, "y": 0, "z": 0.0},
                                        "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                                    }
                                },
                            }
                        },
                        "PolygonRegion": {
                            "AssetName": {
                                "PolygonRegion945_copy0": {
                                    "Annotation": {"0": {"Value": "global/Annotation/mutex"}},
                                    "Value": {
                                        "navigationAllowed": True,
                                        "polygon": [
                                            [-9.974115043535894, -5.680013586835816],
                                            [-9.942705462595178, -4.776202892845146],
                                            [-9.947303875716106, -3.9857735145363065],
                                            [-10.892618029210952, -3.6999350384507466],
                                            [-11.666982322512393, -3.555760926076892],
                                            [-12.438171390467906, -3.4562102821522376],
                                            [-13.523346089231111, -3.2436169413341513],
                                            [-13.367742860839735, -4.151704274368076],
                                            [-13.343077573144102, -4.632667135235599],
                                            [-13.394809272250022, -5.157027016946742],
                                            [-13.858212383365274, -5.691167044558667],
                                            [-13.913943232026334, -6.527901579720876],
                                            [-11.83266605336183, -6.155901259553491],
                                        ],
                                    },
                                },
                                "vis_area2": {
                                    "Value": {
                                        "navigationAllowed": True,
                                        "polygon": [
                                            [-12.459620047211102, -5.383127886796256],
                                            [-12.436945857882353, -3.6340795395161756],
                                            [-11.06637535663629, -3.8679462014936337],
                                            [-11.054748984857714, -4.671783548140258],
                                            [-11.323122663484057, -5.250910695996095],
                                            [-11.57877284072143, -5.4823870306743645],
                                            [-12.239331986286812, -5.353101779611854],
                                        ],
                                    }
                                },
                            }
                        },
                        "memory": {
                            "AssetName": {
                                "tree": {
                                    "Value": [
                                        {
                                            "children": [
                                                {
                                                    "children": [],
                                                    "item": {
                                                        "annotationPropOverrides": {},
                                                        "color": [0.5, 0.5, 0.5, 1],
                                                        "isBidirectional": False,
                                                        "isVisible": False,
                                                        "keyValueMap": {},
                                                        "localPath": [
                                                            [
                                                                1.1811633009830218,
                                                                0.16768857515434543,
                                                                -0.002499999944121714,
                                                            ],
                                                            [
                                                                0.5329951400810107,
                                                                -0.03468655404177784,
                                                                -0.0024999999441217627,
                                                            ],
                                                            [
                                                                -0.24381066275239183,
                                                                -0.06160916030151614,
                                                                -0.0024999999441182134,
                                                            ],
                                                            [
                                                                -1.4703477783116408,
                                                                -0.07139286081105145,
                                                                0.007499999832361689,
                                                            ],
                                                        ],
                                                        "name": "Path337",
                                                        "position": [
                                                            -11.406119972422022,
                                                            -4.907692578325467,
                                                            -0.0074999998323633426,
                                                        ],
                                                        "quaternion": [1, 0, 0, 0],
                                                        "splinePath": [
                                                            [
                                                                1.1811633009830218,
                                                                0.16768857515434543,
                                                                -2.8093352067985715,
                                                            ],
                                                            [
                                                                1.123707615670578,
                                                                0.14786354141122887,
                                                                -2.7875950172989654,
                                                            ],
                                                            [
                                                                1.0469653437628093,
                                                                0.11950224961300186,
                                                                -2.789680757802432,
                                                            ],
                                                            [
                                                                0.955480483967913,
                                                                0.08590931479289328,
                                                                -2.8055246261151217,
                                                            ],
                                                            [
                                                                0.8537970349940872,
                                                                0.050389351984132094,
                                                                -2.8336298611388346,
                                                            ],
                                                            [
                                                                0.7464589955495298,
                                                                0.01624697621994725,
                                                                -2.8763426860316197,
                                                            ],
                                                            [
                                                                0.6380103643424384,
                                                                -0.013213197466432361,
                                                                -2.939894566338532,
                                                            ],
                                                            [
                                                                0.5329951400810107,
                                                                -0.03468655404177784,
                                                                -3.010690667604343,
                                                            ],
                                                            [
                                                                0.43270705598219394,
                                                                -0.04788996464478867,
                                                                -3.063335763740067,
                                                            ],
                                                            [
                                                                0.3335382464887944,
                                                                -0.05566648857345717,
                                                                -3.104584167748902,
                                                            ],
                                                            [
                                                                0.23268031214779922,
                                                                -0.059400793033493375,
                                                                -3.1313728251760953,
                                                            ],
                                                            [
                                                                0.12732485350619577,
                                                                -0.06047754523060732,
                                                                3.139851749494838,
                                                            ],
                                                            [
                                                                0.014663471110971327,
                                                                -0.06028141237050906,
                                                                3.140905622732056,
                                                            ],
                                                            [
                                                                -0.10811223449088682,
                                                                -0.06019706165890867,
                                                                -3.1311868759187873,
                                                            ],
                                                            [
                                                                -0.24381066275239183,
                                                                -0.06160916030151614,
                                                                -3.1269172923961266,
                                                            ],
                                                            [
                                                                -0.4061569204200761,
                                                                -0.06399182132192281,
                                                                -3.131402582680658,
                                                            ],
                                                            [
                                                                -0.5972296880067729,
                                                                -0.06593893376736129,
                                                                -3.133910684264923,
                                                            ],
                                                            [
                                                                -0.8023677256149451,
                                                                -0.0675148288790036,
                                                                -3.1353885863704165,
                                                            ],
                                                            [
                                                                -1.0069097933470554,
                                                                -0.06878383789802175,
                                                                -3.136169905477527,
                                                            ],
                                                            [
                                                                -1.1961946513055661,
                                                                -0.06981029206558775,
                                                                -3.1362701859716755,
                                                            ],
                                                            [
                                                                -1.3555610595929406,
                                                                -0.07065852262287364,
                                                                -3.1351953266293515,
                                                            ],
                                                            [
                                                                -1.4703477783116408,
                                                                -0.07139286081105145,
                                                                -3.1351953266293515,
                                                            ],
                                                        ],
                                                        "type": "Path",
                                                        "weight": 1,
                                                    },
                                                    "name": "Path337",
                                                },
                                                {
                                                    "children": [],
                                                    "item": {
                                                        "annotationPropOverrides": {},
                                                        "color": [0.796078431372549, 0, 1, 0.5],
                                                        "height": 1,
                                                        "isVisible": False,
                                                        "keyValueMap": {
                                                            "0": "global/Annotation/mutex"
                                                        },
                                                        "localPolygon": [
                                                            [
                                                                2.2007831945657403,
                                                                -0.9795150993337731,
                                                                1.0442368124043462e-15,
                                                            ],
                                                            [
                                                                2.2197492870978883,
                                                                -0.07535769064829934,
                                                                1.086737537565778e-15,
                                                            ],
                                                            [
                                                                2.2042714352377977,
                                                                0.7149335111240135,
                                                                1.3625585702460903e-15,
                                                            ],
                                                            [
                                                                1.2551124094074597,
                                                                0.987733120532455,
                                                                -2.0860716999958018e-15,
                                                            ],
                                                            [
                                                                0.47883698955303894,
                                                                1.1212348281952083,
                                                                1.5290920239398638e-15,
                                                            ],
                                                            [
                                                                -0.2936492855111214,
                                                                1.2101610002561027,
                                                                1.4753155961845828e-15,
                                                            ],
                                                            [
                                                                -1.3816474233519112,
                                                                1.4077973012004927,
                                                                1.387712060647754e-15,
                                                            ],
                                                            [
                                                                -1.2135595574332243,
                                                                0.50193779861006,
                                                                1.3001085251109253e-15,
                                                            ],
                                                            [
                                                                -1.1822763875202325,
                                                                0.021360007580162932,
                                                                -5.855358932758632e-16,
                                                            ],
                                                            [
                                                                -1.2267856281132266,
                                                                -0.5036622602736343,
                                                                -2.471180311662653e-15,
                                                            ],
                                                            [
                                                                -1.6827926619368718,
                                                                -1.0441302034413331,
                                                                -2.505874781182189e-15,
                                                            ],
                                                            [
                                                                -1.7270009886732705,
                                                                -1.881552578156009,
                                                                -2.5388345272257484e-15,
                                                            ],
                                                            [
                                                                0.3489586166779331,
                                                                -1.4809397356454463,
                                                                1.0017360872429145e-15,
                                                            ],
                                                        ],
                                                        "name": "PolygonRegion945_copy0",
                                                        "navigationAllowed": True,
                                                        "position": [
                                                            -12.16120719909668,
                                                            -4.6702985763549805,
                                                            -0.009999999776482582,
                                                        ],
                                                        "quaternion": [
                                                            0.9999763158751257,
                                                            1.436683697747356e-09,
                                                            1.7347645418886767e-17,
                                                            -0.0068824188197882975,
                                                        ],
                                                        "type": "PolygonRegion",
                                                    },
                                                    "name": "PolygonRegion945_copy0",
                                                },
                                                {
                                                    "children": [],
                                                    "item": {
                                                        "annotationPropOverrides": {},
                                                        "color": [0, 0.9921568627450981, 1, 0.5],
                                                        "height": 1,
                                                        "isVisible": False,
                                                        "keyValueMap": {},
                                                        "localPolygon": [
                                                            [
                                                                -0.722631799056851,
                                                                -0.576936932192165,
                                                                1.094734422161078e-15,
                                                            ],
                                                            [
                                                                -0.6999576097281027,
                                                                1.1721114150879155,
                                                                -5.636612208727497e-16,
                                                            ],
                                                            [
                                                                0.6706128915179618,
                                                                0.9382447531104572,
                                                                -5.480487095889584e-16,
                                                            ],
                                                            [
                                                                0.6822392632965383,
                                                                0.134407406463833,
                                                                2.889553675698509e-16,
                                                            ],
                                                            [
                                                                0.41386558467019396,
                                                                -0.44471974139200415,
                                                                1.1259594447286606e-15,
                                                            ],
                                                            [
                                                                0.15821540743282123,
                                                                -0.6761960760702735,
                                                                -6.885613111430798e-16,
                                                            ],
                                                            [
                                                                -0.5023437381325614,
                                                                -0.5469108250077631,
                                                                -7.093779928548015e-16,
                                                            ],
                                                        ],
                                                        "name": "vis_area2",
                                                        "navigationAllowed": True,
                                                        "position": [
                                                            -11.736988248154251,
                                                            -4.806190954604091,
                                                            -0.009999999776484851,
                                                        ],
                                                        "quaternion": [1, 0, 0, 0],
                                                        "type": "PolygonRegion",
                                                    },
                                                    "name": "vis_area2",
                                                },
                                                {
                                                    "children": [],
                                                    "item": {
                                                        "annotationPropOverrides": {},
                                                        "assetName": "movai_lab_edges.pcd",
                                                        "color": [1, 1, 1, 1],
                                                        "isVisible": False,
                                                        "keyValueMap": {},
                                                        "name": "movai_lab_edges.pcd93",
                                                        "position": [0, 0, 0],
                                                        "quaternion": [1, 0, 0, 0],
                                                        "type": "PointCloud",
                                                    },
                                                    "name": "movai_lab_edges.pcd93",
                                                },
                                                {
                                                    "children": [],
                                                    "item": {
                                                        "annotationPropOverrides": {},
                                                        "assetName": "movai_lab_planes.pcd",
                                                        "color": [1, 1, 1, 1],
                                                        "isVisible": False,
                                                        "keyValueMap": {},
                                                        "name": "movai_lab_planes.pcd89",
                                                        "position": [0, 0, 0],
                                                        "quaternion": [1, 0, 0, 0],
                                                        "type": "PointCloud",
                                                    },
                                                    "name": "movai_lab_planes.pcd89",
                                                },
                                                {
                                                    "children": [],
                                                    "item": {
                                                        "annotationPropOverrides": {},
                                                        "color": [0.5, 0.5, 0.5, 0],
                                                        "edges": {
                                                            "103_104": {
                                                                "annotationPropOverrides": {},
                                                                "belongsSrc": {
                                                                    "index": 0,
                                                                    "name": "Path85",
                                                                },
                                                                "belongsTrg": {
                                                                    "index": -1,
                                                                    "name": "Path85",
                                                                },
                                                                "ids": ["103", "104"],
                                                                "keyValueMap": {},
                                                                "visibility": True,
                                                                "weight": 1,
                                                            },
                                                            "104_114": {
                                                                "annotationPropOverrides": {},
                                                                "belongsSrc": {
                                                                    "index": -1,
                                                                    "name": "Path85",
                                                                },
                                                                "belongsTrg": {
                                                                    "name": "KeyPoint849"
                                                                },
                                                                "ids": ["104", "114"],
                                                                "keyValueMap": {},
                                                                "visibility": True,
                                                                "weight": 1,
                                                            },
                                                            "105_106": {
                                                                "annotationPropOverrides": {},
                                                                "belongsSrc": {
                                                                    "index": 0,
                                                                    "name": "Path187",
                                                                },
                                                                "belongsTrg": {
                                                                    "index": -1,
                                                                    "name": "Path187",
                                                                },
                                                                "ids": ["105", "106"],
                                                                "keyValueMap": {},
                                                                "visibility": True,
                                                                "weight": 1,
                                                            },
                                                            "106_115": {
                                                                "annotationPropOverrides": {},
                                                                "belongsSrc": {
                                                                    "index": -1,
                                                                    "name": "Path187",
                                                                },
                                                                "belongsTrg": {
                                                                    "name": "KeyPoint766"
                                                                },
                                                                "ids": ["106", "115"],
                                                                "keyValueMap": {},
                                                                "visibility": True,
                                                                "weight": 1,
                                                            },
                                                            "107_108": {
                                                                "annotationPropOverrides": {},
                                                                "belongsSrc": {
                                                                    "index": 0,
                                                                    "name": "Path430",
                                                                },
                                                                "belongsTrg": {
                                                                    "index": -1,
                                                                    "name": "Path430",
                                                                },
                                                                "ids": ["107", "108"],
                                                                "keyValueMap": {},
                                                                "visibility": True,
                                                                "weight": 1,
                                                            },
                                                            "108_116": {
                                                                "annotationPropOverrides": {},
                                                                "belongsSrc": {
                                                                    "index": -1,
                                                                    "name": "Path430",
                                                                },
                                                                "belongsTrg": {
                                                                    "name": "KeyPoint969"
                                                                },
                                                                "ids": ["108", "116"],
                                                                "keyValueMap": {},
                                                                "visibility": True,
                                                                "weight": 1,
                                                            },
                                                            "109_110": {
                                                                "annotationPropOverrides": {},
                                                                "belongsSrc": {
                                                                    "index": 0,
                                                                    "name": "Path707",
                                                                },
                                                                "belongsTrg": {
                                                                    "index": -1,
                                                                    "name": "Path707",
                                                                },
                                                                "ids": ["109", "110"],
                                                                "keyValueMap": {},
                                                                "visibility": True,
                                                                "weight": 1,
                                                            },
                                                            "110_117": {
                                                                "annotationPropOverrides": {},
                                                                "belongsSrc": {
                                                                    "index": -1,
                                                                    "name": "Path707",
                                                                },
                                                                "belongsTrg": {
                                                                    "name": "KeyPoint570"
                                                                },
                                                                "ids": ["110", "117"],
                                                                "keyValueMap": {},
                                                                "visibility": True,
                                                                "weight": 1,
                                                            },
                                                            "111_112": {
                                                                "annotationPropOverrides": {},
                                                                "belongsSrc": {
                                                                    "index": 0,
                                                                    "name": "Path319",
                                                                },
                                                                "belongsTrg": {
                                                                    "index": -1,
                                                                    "name": "Path319",
                                                                },
                                                                "ids": ["111", "112"],
                                                                "keyValueMap": {},
                                                                "visibility": True,
                                                                "weight": 1,
                                                            },
                                                            "112_113": {
                                                                "annotationPropOverrides": {},
                                                                "belongsSrc": {
                                                                    "index": -1,
                                                                    "name": "Path319",
                                                                },
                                                                "belongsTrg": {
                                                                    "name": "KeyPoint346"
                                                                },
                                                                "ids": ["112", "113"],
                                                                "keyValueMap": {},
                                                                "visibility": True,
                                                                "weight": 1,
                                                            },
                                                            "113_103": {
                                                                "annotationPropOverrides": {},
                                                                "belongsSrc": {
                                                                    "name": "KeyPoint346"
                                                                },
                                                                "belongsTrg": {
                                                                    "index": 0,
                                                                    "name": "Path85",
                                                                },
                                                                "ids": ["113", "103"],
                                                                "keyValueMap": {},
                                                                "visibility": True,
                                                                "weight": 1,
                                                            },
                                                            "114_105": {
                                                                "annotationPropOverrides": {},
                                                                "belongsSrc": {
                                                                    "name": "KeyPoint849"
                                                                },
                                                                "belongsTrg": {
                                                                    "index": 0,
                                                                    "name": "Path187",
                                                                },
                                                                "ids": ["114", "105"],
                                                                "keyValueMap": {},
                                                                "visibility": True,
                                                                "weight": 1,
                                                            },
                                                            "115_107": {
                                                                "annotationPropOverrides": {},
                                                                "belongsSrc": {
                                                                    "name": "KeyPoint766"
                                                                },
                                                                "belongsTrg": {
                                                                    "index": 0,
                                                                    "name": "Path430",
                                                                },
                                                                "ids": ["115", "107"],
                                                                "keyValueMap": {},
                                                                "visibility": True,
                                                                "weight": 1,
                                                            },
                                                            "116_109": {
                                                                "annotationPropOverrides": {},
                                                                "belongsSrc": {
                                                                    "name": "KeyPoint969"
                                                                },
                                                                "belongsTrg": {
                                                                    "index": 0,
                                                                    "name": "Path707",
                                                                },
                                                                "ids": ["116", "109"],
                                                                "keyValueMap": {},
                                                                "visibility": True,
                                                                "weight": 1,
                                                            },
                                                            "117_111": {
                                                                "annotationPropOverrides": {},
                                                                "belongsSrc": {
                                                                    "name": "KeyPoint570"
                                                                },
                                                                "belongsTrg": {
                                                                    "index": 0,
                                                                    "name": "Path319",
                                                                },
                                                                "ids": ["117", "111"],
                                                                "keyValueMap": {},
                                                                "visibility": True,
                                                                "weight": 1,
                                                            },
                                                            "53_54": {
                                                                "annotationPropOverrides": {},
                                                                "belongsSrc": {
                                                                    "index": 0,
                                                                    "name": "Path337",
                                                                },
                                                                "belongsTrg": {
                                                                    "index": -1,
                                                                    "name": "Path337",
                                                                },
                                                                "ids": ["53", "54"],
                                                                "keyValueMap": {},
                                                                "visibility": True,
                                                                "weight": 1,
                                                            },
                                                        },
                                                        "isVisible": True,
                                                        "keyValueMap": {},
                                                        "name": "LogicGraph",
                                                        "position": [0, 0, 0],
                                                        "quaternion": [1, 0, 0, 0],
                                                        "type": "GraphItem",
                                                        "vertices": {
                                                            "103": {
                                                                "id": "103",
                                                                "position": [
                                                                    -8.559836061091378,
                                                                    0.48509471388777925,
                                                                    1.0685896612017132e-15,
                                                                ],
                                                            },
                                                            "104": {
                                                                "id": "104",
                                                                "position": [
                                                                    -6.163119022801997,
                                                                    1.4123073273888096,
                                                                    -5.0133508455729725e-16,
                                                                ],
                                                            },
                                                            "105": {
                                                                "id": "105",
                                                                "position": [
                                                                    -4.849069311213661,
                                                                    1.1598590643299715,
                                                                    -9.228728892196614e-16,
                                                                ],
                                                            },
                                                            "106": {
                                                                "id": "106",
                                                                "position": [
                                                                    -1.8130148390952243,
                                                                    -1.4146148101732834,
                                                                    2.8275992658421956e-16,
                                                                ],
                                                            },
                                                            "107": {
                                                                "id": "107",
                                                                "position": [
                                                                    -0.6631162431236213,
                                                                    -2.767322869509148,
                                                                    3.930883396563445e-15,
                                                                ],
                                                            },
                                                            "108": {
                                                                "id": "108",
                                                                "position": [
                                                                    -5.332850789979503,
                                                                    -4.899330151822754,
                                                                    -1.93421667571414e-15,
                                                                ],
                                                            },
                                                            "109": {
                                                                "id": "109",
                                                                "position": [
                                                                    -6.827555157153515,
                                                                    -4.8864951846926825,
                                                                    -2.6385144069607236e-15,
                                                                ],
                                                            },
                                                            "110": {
                                                                "id": "110",
                                                                "position": [
                                                                    -14.854018773223643,
                                                                    -5.549911676284954,
                                                                    -9.315465065995454e-16,
                                                                ],
                                                            },
                                                            "111": {
                                                                "id": "111",
                                                                "position": [
                                                                    -14.647393954810356,
                                                                    -4.785705160813116,
                                                                    -4.0419056990259605e-16,
                                                                ],
                                                            },
                                                            "112": {
                                                                "id": "112",
                                                                "position": [
                                                                    -9.51397993883185,
                                                                    -0.3771342296378002,
                                                                    4.909267437014364e-16,
                                                                ],
                                                            },
                                                            "113": {
                                                                "id": "113",
                                                                "position": [
                                                                    -9.202796673443528,
                                                                    0.0877331633437386,
                                                                    0.23999999463558197,
                                                                ],
                                                            },
                                                            "114": {
                                                                "id": "114",
                                                                "position": [
                                                                    -5.661125183105469,
                                                                    1.4941043853759766,
                                                                    0.23999999463558197,
                                                                ],
                                                            },
                                                            "115": {
                                                                "id": "115",
                                                                "position": [
                                                                    -1.2502803802490234,
                                                                    -1.9700736999511719,
                                                                    0.23999999463558197,
                                                                ],
                                                            },
                                                            "116": {
                                                                "id": "116",
                                                                "position": [
                                                                    -5.950048446655273,
                                                                    -4.767441749572754,
                                                                    0.23999999463558197,
                                                                ],
                                                            },
                                                            "117": {
                                                                "id": "117",
                                                                "position": [
                                                                    -15.181180000305176,
                                                                    -5.167583465576172,
                                                                    0.23999999463558197,
                                                                ],
                                                            },
                                                            "53": {
                                                                "id": "53",
                                                                "position": [
                                                                    -10.224956671439001,
                                                                    -4.740004003171121,
                                                                    -0.009999999776485056,
                                                                ],
                                                            },
                                                            "54": {
                                                                "id": "54",
                                                                "position": [
                                                                    -12.876467750733664,
                                                                    -4.979085439136518,
                                                                    -1.6531914726058972e-15,
                                                                ],
                                                            },
                                                        },
                                                    },
                                                    "name": "LogicGraph",
                                                },
                                                {
                                                    "children": [],
                                                    "item": {
                                                        "annotationPropOverrides": {},
                                                        "color": [
                                                            0.7049121658107482,
                                                            0.2750627535222614,
                                                            0.11975906759954291,
                                                            1,
                                                        ],
                                                        "isVisible": True,
                                                        "keyValueMap": {},
                                                        "name": "KeyPoint346",
                                                        "position": [
                                                            -9.202796673443528,
                                                            0.0877331633437386,
                                                            0.23999999463558197,
                                                        ],
                                                        "quaternion": [
                                                            0.9669151281693742,
                                                            -4.6770139316981384e-08,
                                                            -3.353897429388256e-08,
                                                            0.25509828481822294,
                                                        ],
                                                        "type": "KeyPoint",
                                                    },
                                                    "name": "KeyPoint346",
                                                },
                                                {
                                                    "children": [],
                                                    "item": {
                                                        "annotationPropOverrides": {},
                                                        "color": [
                                                            0.8341020972351947,
                                                            0.9884479497194849,
                                                            0.6302809044684243,
                                                            1,
                                                        ],
                                                        "isVisible": True,
                                                        "keyValueMap": {},
                                                        "name": "KeyPoint849",
                                                        "position": [
                                                            -5.661125183105469,
                                                            1.4941043853759766,
                                                            0.23999999463558197,
                                                        ],
                                                        "quaternion": [
                                                            0.9732407263340312,
                                                            -1.5120372114224608e-08,
                                                            -2.5879555073980933e-09,
                                                            -0.22978792092885789,
                                                        ],
                                                        "type": "KeyPoint",
                                                    },
                                                    "name": "KeyPoint849",
                                                },
                                                {
                                                    "children": [],
                                                    "item": {
                                                        "annotationPropOverrides": {},
                                                        "color": [
                                                            0.49454963615190317,
                                                            0.7307952467780885,
                                                            0.2121529796176047,
                                                            1,
                                                        ],
                                                        "isVisible": True,
                                                        "keyValueMap": {},
                                                        "name": "KeyPoint766",
                                                        "position": [
                                                            -1.2502803802490234,
                                                            -1.9700736999511719,
                                                            0.23999999463558197,
                                                        ],
                                                        "quaternion": [
                                                            0.8936553061931939,
                                                            -7.00468035695557e-08,
                                                            -3.421183574726676e-08,
                                                            -0.44875404590125184,
                                                        ],
                                                        "type": "KeyPoint",
                                                    },
                                                    "name": "KeyPoint766",
                                                },
                                                {
                                                    "children": [],
                                                    "item": {
                                                        "annotationPropOverrides": {},
                                                        "color": [
                                                            0.688835128266984,
                                                            0.5710184585021761,
                                                            0.7671041130713278,
                                                            1,
                                                        ],
                                                        "isVisible": True,
                                                        "keyValueMap": {},
                                                        "name": "KeyPoint969",
                                                        "position": [
                                                            -5.950048446655273,
                                                            -4.767441749572754,
                                                            0.23999999463558197,
                                                        ],
                                                        "quaternion": [
                                                            0.019073746687945294,
                                                            4.0377601523360225e-08,
                                                            -1.0018320389887516e-07,
                                                            -0.9998180795461106,
                                                        ],
                                                        "type": "KeyPoint",
                                                    },
                                                    "name": "KeyPoint969",
                                                },
                                                {
                                                    "children": [],
                                                    "item": {
                                                        "annotationPropOverrides": {},
                                                        "color": [
                                                            0.15717826839741678,
                                                            0.5439020569013864,
                                                            0.27416151596428284,
                                                            1,
                                                        ],
                                                        "isVisible": True,
                                                        "keyValueMap": {},
                                                        "name": "KeyPoint570",
                                                        "position": [
                                                            -15.181180000305176,
                                                            -5.167583465576172,
                                                            0.23999999463558197,
                                                        ],
                                                        "quaternion": [
                                                            0.9524135357492682,
                                                            7.308143753352862e-08,
                                                            -8.210341338833702e-08,
                                                            0.3048088709959484,
                                                        ],
                                                        "type": "KeyPoint",
                                                    },
                                                    "name": "KeyPoint570",
                                                },
                                                {
                                                    "children": [],
                                                    "item": {
                                                        "annotationPropOverrides": {},
                                                        "color": [0.5, 0.5, 0.5, 1],
                                                        "isBidirectional": False,
                                                        "isVisible": True,
                                                        "keyValueMap": {},
                                                        "localPath": [
                                                            [
                                                                -1.3330192350596413,
                                                                -0.5116693951608937,
                                                                1.0685896612017132e-15,
                                                            ],
                                                            [
                                                                0.2693214318299013,
                                                                0.09612617682075708,
                                                                -5.724587470723463e-16,
                                                            ],
                                                            [
                                                                1.06369780322974,
                                                                0.41554321834013663,
                                                                -5.0133508455729725e-16,
                                                            ],
                                                        ],
                                                        "name": "Path85",
                                                        "position": [
                                                            -7.226816826031737,
                                                            0.996764109048673,
                                                            0,
                                                        ],
                                                        "quaternion": [1, 0, 0, 0],
                                                        "splinePath": [
                                                            [
                                                                -1.3330192350596413,
                                                                -0.5116693951608937,
                                                                0.36163901454114294,
                                                            ],
                                                            [
                                                                -1.1811345308029506,
                                                                -0.45421517264538935,
                                                                0.3610315128856129,
                                                            ],
                                                            [
                                                                -0.968440483928931,
                                                                -0.3739059489239164,
                                                                0.36108776144403903,
                                                            ],
                                                            [
                                                                -0.7160184789481883,
                                                                -0.27857998145225255,
                                                                0.3615290329868338,
                                                            ],
                                                            [
                                                                -0.444949900371328,
                                                                -0.17607552768617546,
                                                                0.3623786325896307,
                                                            ],
                                                            [
                                                                -0.17631613270895596,
                                                                -0.07423084508146308,
                                                                0.3638668396117322,
                                                            ],
                                                            [
                                                                0.0688014395283223,
                                                                0.01911580890610698,
                                                                0.36668410430717785,
                                                            ],
                                                            [
                                                                0.2693214318299013,
                                                                0.09612617682075708,
                                                                0.37214568745958243,
                                                            ],
                                                            [
                                                                0.43215212754887006,
                                                                0.15968448500538865,
                                                                0.37791914784961034,
                                                            ],
                                                            [
                                                                0.5783352962567968,
                                                                0.2177194822016602,
                                                                0.38301993082440505,
                                                            ],
                                                            [
                                                                0.7079897827707942,
                                                                0.2699596945519295,
                                                                0.387157754629015,
                                                            ],
                                                            [
                                                                0.8212344319079746,
                                                                0.3161336481985541,
                                                                0.38984949956973797,
                                                            ],
                                                            [
                                                                0.9181880884854506,
                                                                0.35596986928389174,
                                                                0.3902263711174415,
                                                            ],
                                                            [
                                                                0.998969597320335,
                                                                0.3891968839503,
                                                                0.38655216152929217,
                                                            ],
                                                            [
                                                                1.06369780322974,
                                                                0.4155432183401366,
                                                                0.38655216152929217,
                                                            ],
                                                        ],
                                                        "type": "Path",
                                                        "weight": 1,
                                                    },
                                                    "name": "Path85",
                                                },
                                                {
                                                    "children": [],
                                                    "item": {
                                                        "annotationPropOverrides": {},
                                                        "color": [0.5, 0.5, 0.5, 1],
                                                        "isBidirectional": False,
                                                        "isVisible": True,
                                                        "keyValueMap": {},
                                                        "localPath": [
                                                            [
                                                                -1.454934245508567,
                                                                1.1852630725222302,
                                                                -9.228728892196614e-16,
                                                            ],
                                                            [
                                                                -0.12618598110130375,
                                                                0.20394772945879444,
                                                                6.366435156834882e-16,
                                                            ],
                                                            [
                                                                1.5811202266098698,
                                                                -1.3892108019810248,
                                                                2.8275992658421956e-16,
                                                            ],
                                                        ],
                                                        "name": "Path187",
                                                        "position": [
                                                            -3.394135065705094,
                                                            -0.025404008192258704,
                                                            0,
                                                        ],
                                                        "quaternion": [1, 0, 0, 0],
                                                        "splinePath": [
                                                            [
                                                                -1.454934245508567,
                                                                1.1852630725222302,
                                                                -0.6198221697242012,
                                                            ],
                                                            [
                                                                -1.338154296917566,
                                                                1.1019241626976315,
                                                                -0.6072084191557733,
                                                            ],
                                                            [
                                                                -1.183176100118797,
                                                                0.9942496959628513,
                                                                -0.6084441261758403,
                                                            ],
                                                            [
                                                                -0.9983103576291998,
                                                                0.8654712071985344,
                                                                -0.6176529902503994,
                                                            ],
                                                            [
                                                                -0.7918677719657127,
                                                                0.7188202312853256,
                                                                -0.633258305104044,
                                                            ],
                                                            [
                                                                -0.5721590456452752,
                                                                0.5575283031038696,
                                                                -0.6553676856820654,
                                                            ],
                                                            [
                                                                -0.34749488118482613,
                                                                0.3848269575348112,
                                                                -0.6852104487886319,
                                                            ],
                                                            [
                                                                -0.12618598110130375,
                                                                0.20394772945879444,
                                                                -0.7195959356965154,
                                                            ],
                                                            [
                                                                0.11278159855324622,
                                                                -0.0054722887455661805,
                                                                -0.7403158995248384,
                                                            ],
                                                            [
                                                                0.3837997968876437,
                                                                -0.2530932084015288,
                                                                -0.752239660116522,
                                                            ],
                                                            [
                                                                0.6686249041262468,
                                                                -0.5196293001812549,
                                                                -0.7593813987484149,
                                                            ],
                                                            [
                                                                0.9490132104934129,
                                                                -0.7857948347569061,
                                                                -0.7631920379965941,
                                                            ],
                                                            [
                                                                1.2067210062134999,
                                                                -1.0323040828006438,
                                                                -0.7636828885820427,
                                                            ],
                                                            [
                                                                1.4235045815108665,
                                                                -1.2398713149846294,
                                                                -0.7584425837513429,
                                                            ],
                                                            [
                                                                1.5811202266098696,
                                                                -1.3892108019810248,
                                                                -0.7584425837513429,
                                                            ],
                                                        ],
                                                        "type": "Path",
                                                        "weight": 1,
                                                    },
                                                    "name": "Path187",
                                                },
                                                {
                                                    "children": [],
                                                    "item": {
                                                        "annotationPropOverrides": {},
                                                        "color": [0.5, 0.5, 0.5, 1],
                                                        "isBidirectional": False,
                                                        "isVisible": True,
                                                        "keyValueMap": {},
                                                        "localPath": [
                                                            [
                                                                1.7027054146245781,
                                                                1.489341266052962,
                                                                3.930449715694451e-15,
                                                            ],
                                                            [
                                                                1.5759015006964248,
                                                                -0.0941351756659885,
                                                                -1.8132197132647576e-15,
                                                            ],
                                                            [
                                                                -0.3115777830896995,
                                                                -0.7525400741263284,
                                                                -1.8257964584655895e-16,
                                                            ],
                                                            [
                                                                -2.9670291322313034,
                                                                -0.642666016260645,
                                                                -1.934650356583134e-15,
                                                            ],
                                                        ],
                                                        "name": "Path430",
                                                        "position": [
                                                            -2.3658216577481994,
                                                            -4.25666413556211,
                                                            4.336808689942018e-19,
                                                        ],
                                                        "quaternion": [1, 0, 0, 0],
                                                        "splinePath": [
                                                            [
                                                                1.7027054146245781,
                                                                1.489341266052962,
                                                                -1.544750790362449,
                                                            ],
                                                            [
                                                                1.7066444956094213,
                                                                1.3381372301256638,
                                                                -1.4751882140868275,
                                                            ],
                                                            [
                                                                1.7270496361459324,
                                                                1.1253631445425554,
                                                                -1.4815708379798056,
                                                            ],
                                                            [
                                                                1.7496304153367666,
                                                                0.8729596622334695,
                                                                -1.5320659884939483,
                                                            ],
                                                            [
                                                                1.7600964122845781,
                                                                0.6028674361282393,
                                                                -1.6306824543084983,
                                                            ],
                                                            [
                                                                1.744157206092022,
                                                                0.33702711915669775,
                                                                -1.802863867139227,
                                                            ],
                                                            [
                                                                1.6875223758617528,
                                                                0.09737936424867755,
                                                                -2.098496925680139,
                                                            ],
                                                            [
                                                                1.5759015006964248,
                                                                -0.0941351756659885,
                                                                -2.4223865472993786,
                                                            ],
                                                            [
                                                                1.405375518037503,
                                                                -0.2434586878298069,
                                                                -2.608642050337509,
                                                            ],
                                                            [
                                                                1.1873406700520048,
                                                                -0.3720747039279092,
                                                                -2.7393465311762286,
                                                            ],
                                                            [
                                                                0.9304794929309136,
                                                                -0.48135458769439976,
                                                                -2.8335545787514977,
                                                            ],
                                                            [
                                                                0.6434745228652139,
                                                                -0.5726697028633826,
                                                                -2.903934265910742,
                                                            ],
                                                            [
                                                                0.3350082960458892,
                                                                -0.6473914131689621,
                                                                -2.9584521487198097,
                                                            ],
                                                            [
                                                                0.013763348663923869,
                                                                -0.7068910823452426,
                                                                -3.002191546084234,
                                                            ],
                                                            [
                                                                -0.3115777830896995,
                                                                -0.7525400741263284,
                                                                -3.076374061345082,
                                                            ],
                                                            [
                                                                -0.6738517567893053,
                                                                -0.7762006286594272,
                                                                3.1361856218908297,
                                                            ],
                                                            [
                                                                -1.0917219349072103,
                                                                -0.7739411693410712,
                                                                3.0954074150363544,
                                                            ],
                                                            [
                                                                -1.535245838599417,
                                                                -0.7534423347793512,
                                                                3.0710018396637175,
                                                            ],
                                                            [
                                                                -1.9744809890219275,
                                                                -0.7223847635823578,
                                                                3.057996963161233,
                                                            ],
                                                            [
                                                                -2.3794849073307436,
                                                                -0.6884490943581818,
                                                                3.0563229634318834,
                                                            ],
                                                            [
                                                                -2.7203151146818683,
                                                                -0.6593159657149139,
                                                                3.074207990089317,
                                                            ],
                                                            [
                                                                -2.9670291322313025,
                                                                -0.642666016260645,
                                                                3.074207990089317,
                                                            ],
                                                        ],
                                                        "type": "Path",
                                                        "weight": 1,
                                                    },
                                                    "name": "Path430",
                                                },
                                                {
                                                    "children": [],
                                                    "item": {
                                                        "annotationPropOverrides": {},
                                                        "color": [0.5, 0.5, 0.5, 1],
                                                        "isBidirectional": False,
                                                        "isVisible": True,
                                                        "keyValueMap": {},
                                                        "localPath": [
                                                            [
                                                                4.410152991291966,
                                                                0.5914728575157433,
                                                                -2.6389480878297178e-15,
                                                            ],
                                                            [
                                                                1.4705118476433319,
                                                                -0.016183794969693466,
                                                                9.050919735908991e-16,
                                                            ],
                                                            [
                                                                -2.2643542141571418,
                                                                -0.5033454284695225,
                                                                2.6658363017073583e-15,
                                                            ],
                                                            [
                                                                -3.616310624778156,
                                                                -0.07194363407652737,
                                                                -9.319801874685396e-16,
                                                            ],
                                                        ],
                                                        "name": "Path707",
                                                        "position": [
                                                            -11.237708148445488,
                                                            -5.477968042208427,
                                                            4.336808689942018e-19,
                                                        ],
                                                        "quaternion": [1, 0, 0, 0],
                                                        "splinePath": [
                                                            [
                                                                4.410152991291966,
                                                                0.5914728575157433,
                                                                -2.9285345742337388,
                                                            ],
                                                            [
                                                                4.151426458642834,
                                                                0.5354995593116461,
                                                                -2.9215871371239377,
                                                            ],
                                                            [
                                                                3.8076994801991617,
                                                                0.4586335402524985,
                                                                -2.922260728602914,
                                                            ],
                                                            [
                                                                3.3977278830061093,
                                                                0.3672434738497093,
                                                                -2.9273284019589076,
                                                            ],
                                                            [
                                                                2.9402674941088383,
                                                                0.267698033614687,
                                                                -2.9361147526378204,
                                                            ],
                                                            [
                                                                2.4540741405525113,
                                                                0.16636589305884003,
                                                                -2.9490153532039147,
                                                            ],
                                                            [
                                                                1.9579036493822888,
                                                                0.06961572569357716,
                                                                -2.9673399241943397,
                                                            ],
                                                            [
                                                                1.4705118476433319,
                                                                -0.016183794969693466,
                                                                -2.97927644678934,
                                                            ],
                                                            [
                                                                0.9578496976286717,
                                                                -0.10013575026681018,
                                                                -2.982511625091331,
                                                            ],
                                                            [
                                                                0.39189567384028523,
                                                                -0.19093554376430474,
                                                                -2.9894796369195573,
                                                            ],
                                                            [
                                                                -0.19955312836324451,
                                                                -0.28160298529680794,
                                                                -3.0007085773929743,
                                                            ],
                                                            [
                                                                -0.7886996136233346,
                                                                -0.3651578846989506,
                                                                -3.0179751875382554,
                                                            ],
                                                            [
                                                                -1.3477466865814027,
                                                                -0.43462005180536334,
                                                                -3.0453347541420985,
                                                            ],
                                                            [
                                                                -1.8488972518788656,
                                                                -0.48300929645067714,
                                                                -3.0926828615678557,
                                                            ],
                                                            [
                                                                -2.2643542141571418,
                                                                -0.5033454284695225,
                                                                3.0895279232881854,
                                                            ],
                                                            [
                                                                -2.5943661881324274,
                                                                -0.48614790192035356,
                                                                2.9520087223776637,
                                                            ],
                                                            [
                                                                -2.863724574584418,
                                                                -0.4344611483029835,
                                                                2.8124415783969665,
                                                            ],
                                                            [
                                                                -3.0814464572497786,
                                                                -0.360092443614081,
                                                                2.6885445352214505,
                                                            ],
                                                            [
                                                                -3.256548919865169,
                                                                -0.27484906385031527,
                                                                2.60424101495102,
                                                            ],
                                                            [
                                                                -3.398049046167254,
                                                                -0.19053828500835512,
                                                                2.5922781002754065,
                                                            ],
                                                            [
                                                                -3.5149639198926947,
                                                                -0.11896738308486948,
                                                                2.7071666214611425,
                                                            ],
                                                            [
                                                                -3.616310624778156,
                                                                -0.07194363407652737,
                                                                2.7071666214611425,
                                                            ],
                                                        ],
                                                        "type": "Path",
                                                        "weight": 1,
                                                    },
                                                    "name": "Path707",
                                                },
                                                {
                                                    "children": [],
                                                    "item": {
                                                        "annotationPropOverrides": {},
                                                        "color": [0.5, 0.5, 0.5, 1],
                                                        "isBidirectional": False,
                                                        "isVisible": True,
                                                        "keyValueMap": {},
                                                        "localPath": [
                                                            [
                                                                -2.973765174840078,
                                                                -1.941542725258005,
                                                                -4.0419056990259605e-16,
                                                            ],
                                                            [
                                                                -1.6514948269710332,
                                                                -1.3480109700965583,
                                                                1.5040052536718918e-15,
                                                            ],
                                                            [
                                                                0.8196887508670314,
                                                                -0.790534389288309,
                                                                -1.474514954580286e-16,
                                                            ],
                                                            [
                                                                1.645922409805655,
                                                                1.6130598787255612,
                                                                -1.4432899320127035e-15,
                                                            ],
                                                            [
                                                                2.1596488411384254,
                                                                2.467028205917311,
                                                                4.909267437014364e-16,
                                                            ],
                                                        ],
                                                        "name": "Path319",
                                                        "position": [
                                                            -11.673628779970274,
                                                            -2.8441624355551114,
                                                            0,
                                                        ],
                                                        "quaternion": [1, 0, 0, 0],
                                                        "splinePath": [
                                                            [
                                                                -2.973765174840078,
                                                                -1.941542725258005,
                                                                0.45800269208020866,
                                                            ],
                                                            [
                                                                -2.8643084952656372,
                                                                -1.8875845621878464,
                                                                0.48751390941904305,
                                                            ],
                                                            [
                                                                -2.7258450491994073,
                                                                -1.8141713845282161,
                                                                0.4845600609816733,
                                                            ],
                                                            [
                                                                -2.559891079655092,
                                                                -1.7268097834993594,
                                                                0.46297758513038373,
                                                            ],
                                                            [
                                                                -2.3679628296463946,
                                                                -1.6310063503215202,
                                                                0.4280868037605259,
                                                            ],
                                                            [
                                                                -2.1515765421870165,
                                                                -1.5322676762149439,
                                                                0.3820762062322802,
                                                            ],
                                                            [
                                                                -1.9122484602906615,
                                                                -1.4361003523998748,
                                                                0.3257885774315126,
                                                            ],
                                                            [
                                                                -1.6514948269710332,
                                                                -1.3480109700965583,
                                                                0.20976439363739294,
                                                            ],
                                                            [
                                                                -1.344374107054645,
                                                                -1.28262615220634,
                                                                0.1170435543122925,
                                                            ],
                                                            [
                                                                -0.9812246839159333,
                                                                -1.239926691945007,
                                                                0.09214363730362526,
                                                            ],
                                                            [
                                                                -0.5864826783904824,
                                                                -1.2034504360044644,
                                                                0.11571705302620479,
                                                            ],
                                                            [
                                                                -0.18458421131387626,
                                                                -1.1567352310766181,
                                                                0.18861182342524946,
                                                            ],
                                                            [
                                                                0.2000345964783008,
                                                                -1.0833189238533734,
                                                                0.3277189883504462,
                                                            ],
                                                            [
                                                                0.5429376241504644,
                                                                -0.9667393610266353,
                                                                0.566962240582852,
                                                            ],
                                                            [
                                                                0.8196887508670314,
                                                                -0.790534389288309,
                                                                0.8982731057174882,
                                                            ],
                                                            [
                                                                1.0267793325317545,
                                                                -0.5304910114881783,
                                                                1.1327931659879715,
                                                            ],
                                                            [
                                                                1.1847608174108497,
                                                                -0.1931712537389213,
                                                                1.267328152290316,
                                                            ],
                                                            [
                                                                1.3052872232124237,
                                                                0.19172450237321348,
                                                                1.3398100928495755,
                                                            ],
                                                            [
                                                                1.400012567644584,
                                                                0.5944958752619778,
                                                                1.367532004561411,
                                                            ],
                                                            [
                                                                1.480590868415438,
                                                                0.9854424833411226,
                                                                1.3509384711072783,
                                                            ],
                                                            [
                                                                1.5586761432330924,
                                                                1.3348639450244002,
                                                                1.2668964751599066,
                                                            ],
                                                            [
                                                                1.645922409805655,
                                                                1.6130598787255612,
                                                                1.1501982362436152,
                                                            ],
                                                            [
                                                                1.7402049302902307,
                                                                1.8238459427161418,
                                                                1.0852846827729135,
                                                            ],
                                                            [
                                                                1.830456331887537,
                                                                1.9948943622744302,
                                                                1.019619619715179,
                                                            ],
                                                            [
                                                                1.9149166798711,
                                                                2.1322896063243064,
                                                                0.9598822722420051,
                                                            ],
                                                            [
                                                                1.9918260395144443,
                                                                2.242116143789652,
                                                                0.9176457703421342,
                                                            ],
                                                            [
                                                                2.0594244760910967,
                                                                2.330458443594347,
                                                                0.9115109501920138,
                                                            ],
                                                            [
                                                                2.115952054874582,
                                                                2.4034009746622735,
                                                                0.9690100571570237,
                                                            ],
                                                            [
                                                                2.1596488411384254,
                                                                2.4670282059173103,
                                                                0.9690100571570237,
                                                            ],
                                                        ],
                                                        "type": "Path",
                                                        "weight": 1,
                                                    },
                                                    "name": "Path319",
                                                },
                                            ],
                                            "item": {
                                                "annotationPropOverrides": {},
                                                "color": [0, 0, 0, 1],
                                                "isVisible": True,
                                                "keyValueMap": {},
                                                "name": "Global ref",
                                                "position": [0, 0, 0],
                                                "quaternion": [1, 0, 0, 0],
                                                "type": "GlobalRef",
                                            },
                                            "name": "Global ref",
                                        },
                                        {
                                            "children": [],
                                            "item": {
                                                "annotationPropOverrides": {},
                                                "assetName": "movai_lab",
                                                "color": [1, 1, 1, 1],
                                                "isVisible": True,
                                                "keyValueMap": {},
                                                "name": "movai_lab",
                                                "position": [0, -0.1, 0],
                                                "quaternion": [1, 0, 0, 0],
                                                "size": [51.5, 36.9],
                                                "type": "Map",
                                            },
                                            "name": "movai_lab",
                                        },
                                    ]
                                }
                            }
                        },
                    },
                    "Label": "movai_lab_loop",
                    "LastUpdate": {"date": "25/03/2022 at 15:54:58", "user": "movai"},
                    "User": "",
                }
            }
        }
    )

    print(g.save())
