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
        if isinstance(data, ScopeInstanceVersionNode):
            pass
        if isinstance(data, dict):
            try:
                scope = kwargs["scope"]
                ref = kwargs["ref"]
                # remove_extra = kwargs.get('remove_extra', False)
                # schema_version = data.get("schema_version", kwargs.get("schema_version", "1.0"))
            except KeyError as e:
                raise ValueError("missing scope,ref or schema_version") from e

            # get the current schema for this object
            # schema = schemas(scope, schema_version)

            try:
                obj = data[scope][ref]
            except KeyError:
                obj = data

            # TODO check if we want to save it to redis
            """
            # save the object into the database
            redis_keys = self.fetch_keys(conn, scope, ref)
            self.save_keys(schema, f"{scope}:{ref}", redis_keys, conn, obj)

            # store the schema version of this data
            conn.set(f"{scope}:{ref},_schema_version:", schema_version)
            try:
                redis_keys.remove(f"{scope}:{ref},_schema_version:")
            except ValueError:
                pass

            # delete the old relations cache and update it
            conn.delete(f"{scope}:{ref},relations:")
            relations = self.get_related_objects(
                scope=scope, ref=ref, schema_version=schema_version)
            for relation in relations:
                conn.rpush(f"{scope}:{ref},relations:", relation)
            try:
                redis_keys.remove(f"{scope}:{ref},relations:")
            except ValueError:
                pass

            if remove_extra and len(redis_keys) > 0:
                conn.delete(*redis_keys)
            """

            return None

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
