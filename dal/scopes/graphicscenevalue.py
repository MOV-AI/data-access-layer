"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
from geometry_msgs.msg import Pose  # pylint: disable=import-error
from dal.scopes import ScopeNode, ScopePropertyNode


class GraphicSceneValue(ScopePropertyNode):
    """
    A implementation of a GraphicScene Value
    """

    @property
    def to_pose(self):
        """
        try to return the object as a pose, this was created
        to make sure we can still use the database object
        as a pose message
        """
        try:
            p = Pose()
            _value = self.value
            p.position.x = _value["position"]["x"]
            p.position.y = _value["position"]["y"]
            p.position.z = _value["position"]["z"]
            p.orientation.x = _value["orientation"]["x"]
            p.orientation.y = _value["orientation"]["y"]
            p.orientation.z = _value["orientation"]["z"]
            p.orientation.w = _value["orientation"]["w"]
            return p
        except KeyError:
            return None

    @property
    def value(self):
        """
        This is overriden the get value so we can convert a 
        object stored as Pose into a dict, not doing so will
        break the serialization process
        """
        if isinstance(self._value, Pose):
            return {
                "position": {
                    "x": self._value.position.x,
                    "y": self._value.position.y,
                    "z": self._value.position.z,
                },
                "orientation": {
                    "x": self._value.orientation.x,
                    "y": self._value.orientation.y,
                    "z": self._value.orientation.z,
                    "w": self._value.orientation.w,
                }
            }

        return self._value


class GraphicSceneAnnotationValue(ScopePropertyNode):
    """
    A implementation of a GraphicScene Annotation Value
    """

    @property
    def to_pose(self):
        """
        try to return the object as a pose, this was created
        to make sure we can still use the database object
        as a pose message
        """
        try:
            p = Pose()
            p.position.x = self._value["position"]["x"]
            p.position.y = self._value["position"]["y"]
            p.position.z = self._value["position"]["z"]
            p.orientation.x = self._value["orientation"]["x"]
            p.orientation.y = self._value["orientation"]["y"]
            p.orientation.z = self._value["orientation"]["z"]
            p.orientation.w = self._value["orientation"]["w"]
            return p
        except KeyError:
            return None

    @property
    def value(self):
        """
        This is overriden the get value so we can convert a 
        object stored as Pose into a dict, not doing so will
        break the serialization process
        """
        if isinstance(self._value, Pose):
            return {
                "position": {
                    "x": self._value.position.x,
                    "y": self._value.position.y,
                    "z": self._value.position.z,
                },
                "orientation": {
                    "x": self._value.orientation.x,
                    "y": self._value.orientation.y,
                    "z": self._value.orientation.z,
                    "w": self._value.orientation.w,
                }
            }

        return self._value


# Register this Property objects so they can be
# properly used when we are deseralizing
ScopeNode.register_scope_property(
    "schemas/1.0/GraphicScene/AssetType/AssetName/Value", GraphicSceneValue)
ScopeNode.register_scope_property(
    "schemas/1.0/GraphicScene/AssetType/AssetName/Annotation/Value", GraphicSceneAnnotationValue)
