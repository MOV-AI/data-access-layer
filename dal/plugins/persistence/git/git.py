import json
import os
from movai_core_shared.logger import Log
from dal.archive import Archive
from dal.plugins.classes import PersistencePlugin, Persistence, Plugin
from abc import abstractmethod

class GitPlugin(PersistencePlugin):
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
        return "2.2.3"

    @PersistencePlugin.versioning.getter
    def versioning(self):
        """
        returns if this plugin supports versioning
        """
        return True

    def read(self, **kwargs) -> dict:
        """
        load an object from the persistent layer, you must provide the
        following args
        - scope
        - ref
        - version
        The following argument is optional:
        - schema_version

        If the schema_version is not specified the default version will be used
        """
        try:
            # example:
            #       scope = github.com:remote/owner/project

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

    @abstractmethod
    def write(self, data: object, **kwargs):
        """
        Stores the object on the persistent layer, for now we only support
        ScopeInstanceVersionNode, and python dict.

        if you pass a dict you must provide the following args:
            - scope
            - ref
            - schema_version

        Currently a dict must be in one of the following form:
        - { <scope> : { {ref} : { <data> } } }
        - { <data> }

        The data part must comply with the schema of the scope
        """



    @abstractmethod
    def create_workspace(self, ref:str, **kwargs):
        """
        creates a new workspace
        """

    @abstractmethod
    def delete_workspace(self, ref:str):
        """
        deletes a existing workspace
        """

    @abstractmethod
    def workspace_info(self, ref:str):
        """
        get information about a workspace
        """

    @abstractmethod
    def list_workspaces(self):
        """
        list available workspaces
        """

    @abstractmethod
    def list_scopes(self, **kwargs):
        """
        list all existing scopes
        """

    @abstractmethod
    def get_scope_info(self, **kwargs):
        """
        get the information of a scope
        """

    @abstractmethod
    def backup(self, **kwargs):
        """
        archive a scope/scopes into a zip file
        """

    @abstractmethod
    def restore(self, **kwargs):
        """
        restore a scope/scopes from a zip file
        """

    @abstractmethod
    def list_versions(self, **kwargs):
        """
        list all existing scopes
        """

    @abstractmethod
    def get_related_objects(self, **kwargs):
        """
        Get a list of all related objects
        """

    @abstractmethod
    def delete(self, data: object, **kwargs):
        """
        delete data in the persistent layer
        """

    @abstractmethod
    def rebuild_indexes(self,**kwargs):
        """
        force the database layer to rebuild
        all indexes
        """

Persistence.register_plugin("git", GitPlugin)
