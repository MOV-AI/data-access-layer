"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
from ...plugin import Plugin
from DAL.dataaccesslayer.dal.data import (ObjectDeserializer, TreeNode, SchemaPropertyNode,
                                          SchemaObjectNode, SchemaDeserializer)

__DRIVER_NAME__ = "Movai Schema Version 1.0 Plugin"
__DRIVER_VERSION__ = "0.0.1"


class SchemaAttributeDeserializer():
    """
    Deserializer through a dict and convert to a tree
    """

    def __init__(self, schema: dict, relations: dict):
        self._schema = schema
        self._relations = relations

    def deserialize(self, root: TreeNode, data: dict):
        """
        Abstract method to run the data deserializer
        """
        for key, value in data.items():

            if key == "$name":
                root.attributes["is_hash"] = True
                root.attributes["is_id"] = True
                root.attributes["value_on_key"] = True
                SchemaAttributeDeserializer(
                    self._schema, self._relations).deserialize(root, value)
                continue

            if isinstance(value, dict):
                node = SchemaObjectNode(key)
                SchemaAttributeDeserializer(
                    self._schema, self._relations).deserialize(node, value)
            else:
                node = SchemaPropertyNode(
                    key, SchemaV1Deserializer.get_python_type(value))
                if str.startswith(value,"&"):
                    node.attributes["value_on_key"] = True

            root.add_child(node)


class SchemaV1Deserializer(ObjectDeserializer, Plugin):
    """
    Deserializer through a dict and convert to a tree
    """

    SCHEMA_TYPE_MAPPING = {
        "str": str,
        "bool": bool,
        "float": float,
        "hash": dict,
        "any": object
    }

    @Plugin.plugin_name.getter
    def plugin_name(self):
        """
        Get current plugin class
        """
        return __DRIVER_NAME__

    @Plugin.plugin_version.getter
    def plugin_version(self):
        """
        Get current plugin class
        """
        return __DRIVER_VERSION__

    @staticmethod
    def get_python_type(schema_type: str):
        """
        returns the related python type
        """
        try:
            return SchemaV1Deserializer.SCHEMA_TYPE_MAPPING[schema_type]
        except KeyError:
            return str

    def deserialize(self, root: TreeNode, data: dict):
        """
        Abstract method to run the data deserializer
        """
        try:
            if data["_version"] != "1.0":
                raise ValueError("Missing version")
        except KeyError as e:
            raise KeyError("Missing version definition") from e

        try:
            schema = data["schema"]
        except KeyError as e:
            raise KeyError("Missing schema definition") from e

        relations = data.get("relations", {})

        SchemaAttributeDeserializer(
            schema, relations).deserialize(root, schema)


SchemaDeserializer.register_plugin("version10", SchemaV1Deserializer)
