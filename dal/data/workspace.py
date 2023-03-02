"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
from abc import ABC, abstractproperty
from dal.plugins.classes import Persistence
from dal.data.tree import DictNode


class WorkspaceManager:
    """
    A static class that holds all methods to operate with workspaces
    """

    @staticmethod
    def list_workspaces():
        """
        get a list of available workspaces
        """
        workspaces = ["global"]
        plugin = Persistence.get_plugin_class("filesystem")()
        workspaces.extend(plugin.list_workspaces())
        return workspaces

    @staticmethod
    def create_workspace(workspace: str, **kwargs):
        """
        create a new workspace
        """
        if workspace == "global":
            raise ValueError("workspace do not support operation")

        plugin = Persistence.get_plugin_class("filesystem")()
        plugin.create_workspace(workspace, **kwargs)

    @staticmethod
    def delete_workspace(workspace: str):
        """
        create a new workspace
        """
        if workspace == "global":
            raise ValueError("workspace do not support operation")

        plugin = Persistence.get_plugin_class("filesystem")()
        plugin.delete_workspace(workspace)

    @staticmethod
    def workspace_info(workspace: str):
        """
        get information about a workspace
        """
        if workspace == "global":
            return {
                "label": "global",
                "url": "/global"
            }

        plugin = Persistence.get_plugin_class("filesystem")()
        return plugin.workspace_info(workspace)

    """
    A simple workspace exception
    """


class WorkspaceObject(ABC):
    """
    This class represents a interface for a workspace object
    A workspace object is a object that belongs to a specific
    Workspacw
    """

    @abstractproperty
    def workspace(self):
        """
        the object workspace
        """
        raise NotImplementedError


class WorkspaceNode(DictNode, WorkspaceObject):
    """
    Implements a workspace tree node, to define a workspace
    we must provide a name, and a underlying plugin
    """

    def __init__(self, workspace, plugin, readonly: bool = False):
        self._workspace = workspace
        self._plugin = plugin
        self._readonly = readonly
        super().__init__()

    @property
    def workspace(self):
        """
        The current version
        """
        return self._workspace

    @property
    def readonly(self):
        """
        The current version
        """
        return self._readonly

    @property
    def plugin(self):
        """
        Get the current plugin for this workspace
        """
        return self._plugin

    @property
    def node_type(self):
        return "workspace"

    @property
    def path(self):
        """
        get the tree path
        """
        if self.parent is None:
            return self._workspace

        return f"{self.parent.path}/{self._workspace}"

    def reload(self, **kwargs):
        """
        Reload the cached data on this workspace
        """
        raise NotImplementedError

    def unload(self, **kwargs):
        """
        Unload the cached data on this workspace
        """
        raise NotImplementedError

    def write(self, data: object, **kwargs):
        """
        write object to this workspace
        """
        self._plugin.write(data, **kwargs)

    def pull(self, **kwargs):
        return self._plugin.pull(**kwargs)

    def prev_version(self, **kwargs):
        return self._plugin.prev_version(**kwargs)

    def push(self, **kwargs):
        return self._plugin.push(**kwargs)

    def create_version(self, version_tag, **kwargs):
        return self._plugin.create_version(**kwargs)

    def read(self, **kwargs):
        """
        read object from this workspace
        """
        data = self._plugin.read(**kwargs)
        if "schema_version" in data:
            del data["schema_version"]
        return data

    def delete(self, data: object = None, **kwargs):
        """
        delete object from this workspace
        """
        self._plugin.delete(data, **kwargs)

    def backup(self, **kwargs):
        """
        backup object from this workspace to a zip file
        """
        self._plugin.backup(**kwargs)

    def restore(self, **kwargs):
        """
        restore a object from a zip file to this workspace
        """
        self._plugin.restore(**kwargs)
