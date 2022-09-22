"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
from abc import abstractmethod
from urllib.parse import urlparse
from dal.plugins.classes.plugin import Plugin, PluginManager


class ResourceException(Exception):
    """
    A resources handling exception
    """


class ResourcePlugin(Plugin):
    """
    Exposes a simple interface to implement a plugin
    to access physical resources
    """

    @abstractmethod
    def read_text(self, url: str):
        """
        read a text file, returns a StringIO
        """

    @abstractmethod
    def read_json(self, url: str):
        """
        read a json file, returns a dict
        """

    @abstractmethod
    def read_binary(self, url: str):
        """
        read a binary file, returns a IOBytes
        """

    @abstractmethod
    def exists(self, url: str):
        """
        check if resources exists, returns True/False
        """

    @abstractmethod
    def list_resources(self, url: str, recursive: bool = False):
        """
        returns a list of available resources at location, returns a list
        """


class Resource(PluginManager):
    """
    This class represents a resources, a resources can be a image file, a
    python script, a map, or any other kind of file that needs to be
    accessed

    A resources might be located on the local filesystem, or a external
    filesystem.

    We provide one interface to implement a plugin to access the physical
    resources
    """

    @classmethod
    def plugin_class(cls):
        """
        Get current class plugin
        """
        return "resources"

    @classmethod
    def get_plugin(cls, key: str):
        result = urlparse(key)

        if result.scheme == "":
            raise ValueError("Invalid URL")

        return super().get_plugin(result.scheme)

    @staticmethod
    def read_text(url: str):
        """
        load a text file, returns a StringIO
        """
        return Resource.get_plugin(url).read_text(url)

    @staticmethod
    def read_json(url: str):
        """
        load a json file, returns a dict
        """
        return Resource.get_plugin(url).read_json(url)

    @staticmethod
    def read_yaml(url: str):
        """
        load a yaml file, returns a dict
        """
        return Resource.get_plugin(url).read_yaml(url)

    @staticmethod
    def read_binary(url: str):
        """
        load a binary file, returns a BytesIO
        """
        return Resource.get_plugin(url).read_binary(url)

    @staticmethod
    def validate_url(url: str):
        """
        validate an url (schema)://(net location), ie: file://node.json
        """
        result = urlparse(url)
        return result.scheme != "" and result.netloc != ""

    @staticmethod
    def exists(url: str):
        """
        check if resources exists, returns True/False
        """
        return Resource.get_plugin(url).exists(url)

    @staticmethod
    def list_resources(url: str, recursive: bool = False):
        """
        returns a list of available resources at location, returns a list
        """
        return Resource.get_plugin(url).list_resources(url, recursive)
