"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
from abc import ABC, abstractmethod, abstractproperty
from movai_core_shared.logger import Log
from .plugin import Plugin, PluginManager


class PersistentObject(ABC):
    """
    This class represents a interface for a persistent object
    A persistent object is a object that can be stored on a
    persistent media like disc, database, key-value store
    """

    @abstractmethod
    def write(self, **kwargs):
        """
        Writes object on the persistant layer
        """

    @abstractmethod
    def delete(self, **kwargs):
        """
        Delte object from the persistant layer
        """


class PersistencePlugin(Plugin):
    """
    A interface for a workspace plugin
    """

    def __init__(self, **kwargs):
        self._args = kwargs

    @abstractproperty
    def versioning(self):
        """
        returns if this plugin supports versioning
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
    def write(self, data: object, **kwargs):
        """
        write data to the persistent layer
        """

    @abstractmethod
    def read(self, **kwargs):
        """
        read data from the persistent layer
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


class Persistence(PluginManager):
    """
    Implements an interface for accessing the persistance
    layer
    """
    logger = Log.get_logger("persistence.mov.ai")

    @classmethod
    def plugin_class(cls):
        """
        Get current class plugin
        """
        return "persistence"
