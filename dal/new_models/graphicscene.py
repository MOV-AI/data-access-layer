from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, constr
from pydantic.config import BaseConfig
from base import MovaiBaseModel
from movai_core_shared.logger import Log
import numpy as np


logger = Log.get_logger(__name__)
KEYPOINT = "KeyPoint"
PATH = "Path"


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
    Value: Optional[
        Dict[constr(regex=r"^[a-zA-Z0-9_]+[.]png$|^[a-zA-Z0-9_]+$"), Value2]
    ] = None


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
        Optional[Dict[constr(regex=r"^[0-9]+$"), Annotation1]],
        Optional[AnnotationValue],
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

    def get_trajectories(self) -> List:
        """Get the names of all trajectories in the scene"""
        asset_type = getattr(self.AssetType, PATH, None)
        return [] if not asset_type else list(asset_type.AssetName)

    def get_trajectory_waypoints(self, trajectory_name: str) -> List:
        """Get an array of waypoints

        waypoint format:
            [x1, y1, x2, y2]
        """
        asset_type = getattr(self.AssetType, PATH, None)
        if not asset_type:
            return []
        else:
            trajectory_points = (
                asset_type.AssetName[trajectory_name].Value.value.keypoints
            )
            return [float(point) for point in trajectory_points]

    def get_trajectory_waypoints_list(self, trajectory_name: str) -> List:
        """Get an array of waypoints

        waypoint format:
            [[x1, y1], [x2, y2]]
        """
        points = self.get_trajectory_waypoints(trajectory_name)
        return list(zip(points[0::2], points[1::2]))

    def get_trajectory_distance(self, trajectory_name: str) -> float:
        """Returns the distance of a trajectory"""
        try:
            waypoints = (
                getattr(self.AssetType, PATH).AssetName[trajectory_name].Value.value.trajectory
            )
        except KeyError:
            return 0.0

        # Cant find the fix for this, went back to old version
        # return np.sum([
        #    np.linalg.norm(np.diff(pair, axis=0), ord=2)
        #    for pair in zip(waypoints[::3], waypoints[1::3])
        # ])

        waypoints = [pair for pair in zip(waypoints[::3], waypoints[1::3])]
        return np.sum(np.sqrt(np.sum(np.diff(waypoints, axis=0) ** 2, axis=1)))

    def get_trajectory_init_yaw(self, trajectory_name: str) -> Union[float, None]:
        """Get the initial yaw of a trajectory"""
        try:
            return float(
                getattr(self.AssetType, PATH)
                .AssetName[trajectory_name]
                .Value.value.trajectory[2]
            )
        except (KeyError, IndexError, ValueError):
            # dicts, lists of float conversion errors
            return None

    def get_trajectory_yaw(self, trajectory_name: str) -> float:
        """Get the final yaw of a trajectory"""
        try:
            return float(
                self.AssetType[PATH]
                .AssetName[trajectory_name]
                .Value.value.trajectory[-1]
            )
        except (KeyError, IndexError, ValueError):
            # dicts, lists of float conversion errors
            return None

    def get_keypoints(self) -> List:
        """Get the names of all keypoints in the scene"""
        try:
            return list(self.AssetType.KeyPoint.AssetName)
        except KeyError:
            # no 'KeyPoint' on dict
            return []

    def get_areas(self) -> List:
        """Get the name of all regions in the scene"""
        _area_types = ("BoxRegion", "PolygonRegion")
        ret = []
        for _atype in _area_types:
            try:
                ret.extend(list(getattr(self.AssetType, _atype).AssetName))
            except KeyError:
                pass
        return ret

    def get_area_points(self, area_name: str) -> List:
        """Get an array of area points"""
        partial = list()
        try:
            box_region = self.AssetType.BoxRegion.AssetName[area_name].Value
            if box_region:
                partial.extend(box_region.value["polygon"])
        except KeyError:
            pass

        try:
            polygon_region = self.AssetType["PolygonRegion"].AssetName[area_name].Value
            if polygon_region:
                partial.extend(polygon_region.value["polygon"])
        except KeyError:
            pass
        return partial

    def point_in_area(
        self, area_name: str, x: float, y: float
    ) -> Union[bool, None]:  # pylint: disable=invalid-name
        """Check if point (x,y) is inside area"""
        try:
            return Path(np.array(self.get_area_points(area_name))).contains_point(
                (x, y)
            )
        except ValueError:  # 'vertices' must be a 2D list or array with shape Nx2
            # when get_area_points() return empty list
            return None

    def get_goal(self, asset_name: str) -> Pose:
        """Get the goal Pose from trajectory or point name"""
        _valid_goals = (KEYPOINT, PATH)
        for goal in _valid_goals:
            try:
                asset = self.AssetType[goal].AssetName[asset_name].Value
            except KeyError:
                continue
            if not asset:
                continue
            if goal == KEYPOINT:
                return asset.to_pose
            # else
            path = asset.value
            angle = path["trajectory"][-1]  # in radians

            return Pose(
                Point(*path["keypoints"][-2:], 0.0),  # x,y,z
                # simple enough conversion:
                Quaternion(0.0, 0.0, np.sin(angle / 2), np.cos(angle / 2)),  # x,y,z,w
            )
        # else, not found
        return None

    def get_element_points(self, asset_name: str) -> list:
        """Returns the [x0,y0, ..., xn,yn] from a trajectory or point name"""
        _valid_goals = (KEYPOINT, PATH)
        for goal in _valid_goals:
            try:
                asset = self.AssetType[goal].AssetName[asset_name].Value
            except KeyError:
                continue
            if not asset:
                continue
            if goal == KEYPOINT:
                position = asset.value["position"]
                return [position["x"], position["y"]]
            if goal == PATH:
                tmp_array = np.array(asset.value["trajectory"])
                # remove the z coordinates of array
                tmp_array = np.delete(tmp_array, np.arange(2, tmp_array.size, 3))
                return list(tmp_array)
        # else, not found
        return []

    def get_annotation(
        self, asset_name: str, annotation_type: str = "all"
    ) -> Union[Dict, None]:
        """Get a dict with the annotation(s) of an asset

        pass `annotation_type` to filter
        """
        for atype in self.AssetType.values():
            if asset_name in atype.AssetName.keys():
                annotation = atype.AssetName[asset_name].Annotation
                break
        else:
            # not found
            return None
        if annotation_type == "all":
            return {key: value.Value.value for key, value in annotation.items()}
        # else
        try:
            return {annotation_type: annotation[annotation_type].Value.value}
        except KeyError:
            return {annotation_type: ""}

    def get_annotation_props_overrides(self, asset_name: str):
        """Get a dict with annotations properties overwritten of an asset"""
        overrides = {}
        for atype in self.AssetType.values():
            if asset_name in atype.AssetName.keys():
                overrides = atype.AssetName[asset_name].AnnotationOverride
                break
        if not overrides:
            # not found
            logger.error("asset_name not found: ", asset_name)

        return overrides

    def get_edge_annotations(self, edge_name: str):
        """Get a dict containing edge annotations and overrides
        edge_name in format: Edge-<source>,<target> (Edge-0,1)
        """
        default_value = {"annotation_names": {}, "annotation_overrides": {}}
        try:
            pattern = "([^-]*)-([^,]+),([^,]*)"
            edge_data = re.search(pattern, edge_name)
            if not edge_data:
                logger.error(
                    "received edge_name is not of the right pattern", edge_name
                )
                return default_value
            source, target = edge_data.group(2), edge_data.group(3)
            logic_graph = None
            for atype in self.AssetType.values():
                try:
                    logic_graph = atype.AssetName["LogicGraph"].Value.value
                    break
                except KeyError:
                    pass
            if not logic_graph:
                logger.error("LogicGraph not found")
                return default_value
        except IndexError:
            logger.error("invalid edge_name => ", edge_name)
            return default_value
        # get logic graph edges
        logic_graph_links = logic_graph["links"]
        filtered_edges = [
            ed for ed in logic_graph_links if find_edge(ed, source, target)
        ]
        if not filtered_edges:
            return default_value
        # return edge annotations and overrides
        edge = filtered_edges[0]
        try:
            edge_annotations = edge["keyValueMap"]
            edge_overrides = edge["annotationPropOverrides"]
        except KeyError:
            edge_overrides = default_value["annotation_overrides"]
        # Return data
        return {
            "annotation_names": edge_annotations,
            "annotation_overrides": overrides_dict_to_object(edge_overrides),
        }

    def get_computed_annotations(
        self, asset_name: str, is_logic_graph_edge: bool = False
    ) -> List:
        """Get computed annotation keys of an asset

        Parameters:
        asset_name (string): Scene object name (asset name eg: BoxRegion307)
        is_logic_graph_edge (boolean) : Flag to inform if asset_name is a logicGraph edge

        Returns:
        List: List of all annotations props with overrides (if any)
        """
        computed_annotations_dict = {}
        # get annotations
        annotations = self.get_annotation(asset_name)
        edge_annotation_dict = {}
        if is_logic_graph_edge:
            edge_annotation_dict = self.get_edge_annotations(asset_name)
            annotations = edge_annotation_dict["annotation_names"]
        # order annotations
        sorted_annotations = [x[1] for x in sorted(annotations.items()) if x[1]]
        # get annotation props
        for annotation_path in sorted_annotations:
            try:
                computed_annotations_dict.update(
                    Annotation(annotation_path).get_computed_annotation()
                )
            except KeyError:
                logger.error("Annotation not found: ", annotation_path)
        # get overrides
        if is_logic_graph_edge:
            prop_overrides = edge_annotation_dict["annotation_overrides"]
        else:
            prop_overrides = self.get_annotation_props_overrides(asset_name)
        # apply overrides
        for override_key in prop_overrides:
            override_path = override_key.split(".")
            override_value = prop_overrides[override_key]["Value"].value
            annotation_prop_key = override_path[0]
            try:
                computed_annotations_dict[annotation_prop_key]["overwritten"] = True
                if len(override_path) == 1:
                    computed_annotations_dict[annotation_prop_key][
                        "value"
                    ] = override_value
                    computed_annotations_dict[annotation_prop_key]["annotation"][
                        "name"
                    ] = "__overwritten__"
                    computed_annotations_dict[annotation_prop_key]["annotation"][
                        "type"
                    ] = get_data_type(override_value)
                # When config is not an object
                elif len(override_path) == 2 and override_path[1] == "":
                    computed_annotations_dict[annotation_prop_key][
                        "value"
                    ] = override_value
                else:
                    override_path.pop(0)
                    acc = computed_annotations_dict[annotation_prop_key]["value"]
                    for config_key in override_path:
                        if isinstance(acc[config_key], dict):
                            acc = acc[config_key]
                    acc[override_path[-1]] = override_value
            except Exception as e:  # pylint: disable=broad-except
                logger.error(e)

        # return computed annotations
        return list(computed_annotations_dict.values())

    def get_weight(self, asset_name: str):
        """Get weight of asset"""
        for atype in self.AssetType.values():
            if asset_name in atype.AssetName:
                return atype.AssetName[asset_name].Value.value.get("weight", None)
        return None

    def get_graph(self):
        """Get the graph"""
        return json_graph.node_link_graph(
            next(iter(self.AssetType["GraphItem"].AssetName.values())).Value.value
        )

    def get_trajectory_spline(self, trajectory_name: str) -> Union[List, int]:
        try:
            points = (
                self.AssetType[PATH].AssetName[trajectory_name].Value.value["keypoints"]
            )
            waypoints = [(x, y) for x, y in zip(points[::2], points[1::2])]
        except KeyError:
            return 0
        n = np.atleast_1d(waypoints)
        return si.splprep(n.T, s=0, k=1)[0]
