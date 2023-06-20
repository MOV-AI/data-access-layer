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

