"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
from dal.plugins.classes import Plugin
from dal.data import ObjectDeserializer, TreeNode, SchemaDeserializer


__DRIVER_NAME__ = "Movai Schema Version 2.0 Plugin"
__DRIVER_VERSION__ = "0.0.1"


class SchemaV2Deserializer(ObjectDeserializer, Plugin):
    """
    Deserializer through a dict and convert to a tree
    """

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

    def deserialize(self, root: TreeNode, data: dict):
        """
        Abstract method to run the data deserializer
        """
        raise NotImplementedError


SchemaDeserializer.register_plugin("version20", SchemaV2Deserializer)
