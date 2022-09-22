import json
import os
from ..filesystem import FilesystemPlugin
from movai_core_shared.logger import Log
from dal.data import Persistence
from dal.plugins import Plugin
from dal.archive import Archive


class GitPlugin(FilesystemPlugin):
    logger = Log.get_logger("git.mov.ai")
    _ROOT_PATH = os.path.join(os.getenv('MOVAI_USERSPACE', ""), "database")
    archive = Archive()

    def validate_data(self, schema, data: dict, out: dict):
        pass

    @Plugin.plugin_name.getter
    def plugin_name(self):
        """
        Get current plugin class
        """
        return "git.mov.ai"

    @Plugin.plugin_version.getter
    def plugin_version(self):
        """
        Get current plugin class
        """
        return "3.1.0"

    def read(self, **kwargs) -> dict:
        """
        load an object from the persistent layer, you must provide the
        following args
        - scope
        - ref
        The following argument is optional:
        - schema_version

        If the schema_version is not specified we will try to load it
        from redis, if it is missing the default will be 1.0
        """
        try:
            # scope = github.com:remote/owner/project
            scope = kwargs["scope"]
            # ref = path
            ref = kwargs["ref"]
            version = kwargs["version"]
        except KeyError as e:
            raise ValueError("missing scope or name") from e

        
        remote = f"git@{scope}"
        # ref = path
        # scope = owner/project
        path = GitPlugin.archive.get(ref, remote, version)
        data = {}
        with path.open("r") as f:
            data = json.loads(f.read())

        return data

Persistence.register_plugin("git", GitPlugin)
