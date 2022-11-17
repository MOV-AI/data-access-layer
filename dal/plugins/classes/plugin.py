"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
from abc import abstractmethod
from importlib import import_module


class Plugin:
    """
    A abstract class for plugins
    """
    @property
    @abstractmethod
    def plugin_name(self):
        """
        Get current plugin class
        """

    @property
    @abstractmethod
    def plugin_version(self):
        """
        Get current plugin class
        """


class PluginManager:
    """
    A abstract class for plugin managers
    """
    _plugins = {}

    @classmethod
    def plugin_class(cls):
        """
        Get current class plugin
        """
        return ""

    @classmethod
    def get_plugin(cls, key: str):
        """
        Get the plugin implementation
        """
        if key not in cls._plugins:
            try:
                # Try to load plugin from our library
                import_module(
                    "dal.plugins.{}.{}".format(cls.plugin_class(), key))
            except ModuleNotFoundError as e:
                raise ValueError(f"No plugin found for key:{key}") from e

        return cls._plugins[key]

    @classmethod
    def get_plugin_class(cls, key: str):
        """
        Get the plugin implementation
        """
        if key not in cls._plugins:
            try:
                # Try to load plugin from our library
                import_module(
                    "dal.plugins.{}.{}".format(cls.plugin_class(), key))
            except ModuleNotFoundError as e:
                raise ValueError(f"No plugin found for key:{key}") from e

        return type(cls._plugins[key])

    @classmethod
    def register_plugin(cls, key: str, drv: type(Plugin)):
        """
        Register a new plugin
        """
        if not issubclass(drv, Plugin):
            raise ValueError("Plugin not valid")

        cls._plugins[key] = drv()
