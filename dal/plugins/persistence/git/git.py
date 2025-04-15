import json
import os
from movai_core_shared.logger import Log
from dal.archive import Archive
from dal.plugins.classes import PersistencePlugin, Persistence, Plugin
from abc import abstractmethod
from dal.models.scopestree import ScopeInstanceVersionNode
from dal.validation import JsonValidator, default_version


class GitPlugin(PersistencePlugin):
    logger = Log.get_logger("git.mov.ai")
    _ROOT_PATH = os.path.join(os.getenv("MOVAI_USERSPACE", ""), "database")
    archive = Archive()

    def validate_data(self, schema, data: dict, out: dict):
        JsonValidator("2.4")
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
        return "2.4.0"

    @PersistencePlugin.versioning.getter
    def versioning(self):
        """
        returns if this plugin supports versioning
        """
        return True

    @staticmethod
    def remote(scope):
        return f"git@{scope}"

    def pull(self, **kwargs):
        try:
            scope = kwargs["scope"]
            branch = kwargs["branch"]
        except KeyError as e:
            raise ValueError("missing scope or alias") from e

        return GitPlugin.archive.pull(GitPlugin.remote(scope), branch)

    def read(self, **kwargs) -> dict:
        """
        load an object from the persistent layer, you must provide the
        following args
        - scope: example, "remote:owner/project"
        - ref: path inside the project, /Flow/v1/flow1.json
        - version: the desired version, v1.1

        The following argument is optional:
        - schema_version

        If the schema_version is not specified the default version will be used
        """
        try:
            scope = kwargs["scope"]
            ref = kwargs["ref"]
            version = kwargs["version"]
        except KeyError as e:
            raise ValueError("missing scope or name") from e

        path = GitPlugin.archive.get(ref, GitPlugin.remote(scope), version)
        data = {}
        with path.open("r") as f:
            data = json.loads(f.read())

        return data

    @abstractmethod
    def write(self, data: object, **kwargs):
        """
        Stores the object on the persistent layer.
        writes and creates new commit to relevant repository.

        if you pass a dict you must provide the following args:
            - scope
            - ref

        optional:
            - version: on what version to be based for changes to commit

        Currently a dict must be in one of the following form:
        - { <scope> : { {ref} : { <data> } } }
        - { <data> }

        The data part must comply with the schema of the scope
        """
        data_to_write: dict = data
        try:
            scope = kwargs["scope"]
            ref = kwargs["ref"]
            version = kwargs.get("version", None)
        except KeyError as e:
            raise ValueError("missing scope,ref or version") from e

        if isinstance(data, ScopeInstanceVersionNode):
            data_to_write = data.serialize()
        if isinstance(data, dict):
            try:
                obj = data[scope][ref]
            except KeyError:
                obj = data
            data_to_write = obj

        if "schema_version" in data_to_write:
            schema_version = data_to_write["schema_version"]
        else:
            schema_version = default_version
        validator = JsonValidator(schema_version)
        validation_res = validator.validate(file_path=None, content=data_to_write)
        if validation_res["status"] is False:
            self.logger.error(
                f"data is incompatible with schema version: {schema_version}\n",
                validation_res["message"],
            )

        self.archive.create_obj(GitPlugin.remote(scope), ref, data_to_write, base_version=version)
        commit_sha = self.archive.commit(
            ref, GitPlugin.remote(scope), message=f"modified file {ref}"
        )
        self.logger.debug(
            f"file written and committed path:{self.archive.local_path(GitPlugin.remote(scope))}/{ref}, commit sha:{commit_sha}"
        )

        return commit_sha

    def create_version(self, version_tag, **kwargs):
        scope = kwargs["scope"]
        base_version = kwargs["base_version"]
        message = kwargs["message"]
        return GitPlugin.archive.create_tag(
            GitPlugin.remote(scope), base_version, version_tag, message
        )

    def push(self, **kwargs):
        scope = kwargs["scope"]
        alias = kwargs.get("alias", "origin")

        return GitPlugin.archive.push(GitPlugin.remote(scope))

    def prev_version(self, **kwargs):
        scope = kwargs["scope"]
        version = kwargs["version"]
        return GitPlugin.archive.prev_version(GitPlugin.remote(scope), version)

    @abstractmethod
    def create_workspace(self, ref: str, **kwargs):
        """
        creates a new workspace
        """

    @abstractmethod
    def delete_workspace(self, ref: str):
        """
        deletes a existing workspace
        """

    @abstractmethod
    def workspace_info(self, ref: str):
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
        scope = kwargs["scope"]
        return GitPlugin.archive.list_models(GitPlugin.remote(scope))

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
        scope = kwargs["scope"]
        branches = kwargs["ref"] == "branches"
        return GitPlugin.archive.list_versions(GitPlugin.remote(scope), branches)

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
        ref = kwargs["ref"]
        scope = kwargs["scope"]
        version = kwargs["version"]

        new_version = self.archive.delete(GitPlugin.remote(scope), ref, version)
        if new_version is None:
            # Failed to delete
            pass
        else:
            return new_version

    @abstractmethod
    def rebuild_indexes(self, **kwargs):
        """
        force the database layer to rebuild
        all indexes
        """


Persistence.register_plugin("git", GitPlugin)
