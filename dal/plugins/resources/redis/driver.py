"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
from io import BytesIO, StringIO
from json import JSONDecodeError, load
from os import path
from dal.plugins import Resource, ResourcePlugin, ResourceException


class RedisPlugin(ResourcePlugin):
    """
    Exposes a simple interface to implement a plugin
    to access physical resources
    """

    def read_text(self, url: str):
        """
        Read a text file, returns all text in the file
        """
        raise ResourceException(
            "Error opening text file {}".format(url))

    def read_json(self, url: str):
        """
        Read a text file, returns all text in the file
        """
        raise ResourceException(
            "Error opening text file {}".format(url))

    def read_binary(self, url: str):
        """
        Read a text file, returns all text in the file
        """
        raise ResourceException(
            "Error opening text file {}".format(url))


# Register this Plugin
Resource.register_plugin("redis", RedisPlugin)
