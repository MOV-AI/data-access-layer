"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
from io import BytesIO, StringIO
from json import JSONDecodeError, load
from os import listdir, path, getenv, getcwd
import yaml
from dal.plugins.classes import Plugin, Resource, ResourcePlugin, ResourceException

__DRIVER_NAME__ = "Filesystem Plugin"
__DRIVER_VERSION__ = "0.0.1"


class FilePlugin(ResourcePlugin):
    """
    Exposes a simple interface to implement a plugin
    to access physical resources
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

    def read_text(self, url: str):
        """
        read a text file, returns a StringIO
        """
        local_path = self._get_local_path(url)

        with open(local_path, "r", encoding="utf-8") as fd:
            try:
                return StringIO(fd.read())
            except (OSError, JSONDecodeError):
                raise ResourceException("Error opening text file {}".format(url))

    def read_json(self, url: str):
        """
        read a json file, returns a dict
        """
        local_path = self._get_local_path(url)

        with open(local_path, "r", encoding="utf-8") as fd:
            try:
                return load(fd)
            except (OSError, JSONDecodeError):
                raise ResourceException("Error opening json file {}".format(url))

    def read_yaml(self, url: str):
        """
        read a yaml file, returns a dict
        """
        local_path = self._get_local_path(url)

        with open(local_path, "r") as fd:
            try:
                return yaml.safe_load(fd)
            except (OSError, yaml.YAMLError):
                raise ResourceException("Error opening yaml file {}".format(url))

    def read_binary(self, url: str):
        """
        read a binary file, returns a IOBytes
        """
        local_path = self._get_local_path(url)

        with open(local_path, "rb") as fd:
            try:
                return BytesIO(fd.read())
            except (OSError, JSONDecodeError):
                raise ResourceException("Error opening binary file {}".format(url))

    def exists(self, url: str):
        """
        check if resources exists, returns True/False
        """
        try:
            _ = self._get_local_path(url)
            return True
        except ValueError:
            return False

    def list_resources(self, url: str, recursive: bool = False):
        """
        returns a list of available resources at location, returns a list
        """
        local_path = self._get_local_path(url)

        files = []
        for entry in listdir(local_path):
            if path.isfile(path.join(local_path, entry)):
                files.append(entry)

        return files

    def _get_local_path(self, url: str):
        """
        validates url and extracts the path part.

        will convert a relative path to a absolute path
        based on APP_PATH environment variable or the
        current working directory.
        """
        if not url.startswith("file://"):
            raise ValueError("Invalid URL")

        # TODO these checks should be more extensible (BP-45)

        # extract path from URL
        local_path = url[7:]

        if path.isabs(local_path) and path.exists(local_path):
            return local_path
        else:
            # check with CWD
            cwd_path = path.join(getcwd(), local_path)
            if path.exists(cwd_path):
                return cwd_path

            # check with APP_PATH
            app_path = getenv("APP_PATH")
            if app_path is not None:
                app_path_path = path.join(app_path, local_path)
                if path.exists(app_path_path):
                    return app_path_path

        # no paths existed
        raise ValueError("Can't open url: {}".format(url))


# Register this Plugin
Resource.register_plugin("file", FilePlugin)
