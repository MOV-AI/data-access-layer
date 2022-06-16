from abc import abstractmethod
from pathlib import Path
from typing import Any


class BaseArchive:
    active_archive = None
    classes = {}

    def __call__(self) -> "BaseArchive":
        if BaseArchive.active_archive is None:
            raise Exception("No active Archive registered")
        return BaseArchive.active_archive.get_client()

    def __init_subclass__(cls, id=None):
        if id is None:
            return
        if id in BaseArchive.classes:
            raise Exception("Archive id={id} is already registered")

        BaseArchive.classes[id] = cls

    @classmethod
    def set_active_archive(cls, name):
        if name not in cls.classes:
            raise Exception("Archive not registered")
        cls.active_archive = cls.classes[name]

    @abstractmethod
    def get_client(self, **kwargs) -> "BaseArchive":
        """instantiate Archive instance and returns it.
        """
        pass

    @abstractmethod
    def get(self,
            obj_name: str,
            remote: str,
            version: str,
            **kwargs) -> Path:
        """Get an Object from remote Archive, and save it locally.

        Args:
            obj_name (str): Name of the object.
            remote (str): Remote link.
            version (str): Version desired.

        Returns:
            Path: the local path of the requested File.
        """
        pass

    @abstractmethod
    def commit(self,
               obj_name: str,
               remote: str,
               **kwargs) -> str:
        """saves changes locally, will create new version if requested.

        Args:
            obj_name (str): name of object to comit
            remote (str): the remote link of the repo.

        Returns:
            str: new version hash
        """
        pass

    @abstractmethod
    def pull(self, remote: str, **kwargs) -> Any:
        """pull changes from remote Archive to local one.

        Args:
            remote (str): remote link of Archive
        """
        pass

    @abstractmethod
    def push(self, remote: str, **kwargs) -> Any:
        """push changes from local to remote Archive.

        Args:
            remote (str): remote Archive link
        """

    @abstractmethod
    def create_obj(self,
                   remote: str,
                   relative_path: str,
                   content: str,
                   **kwargs):
        """will create new obj locally (relative path to local archive)
           of the local repository path.

        Args:
            remote (str): the remote archive link
            relative_path (str): the relative path to the root of the local archive
            content (str): the obj content to be added
        """
        pass

    @abstractmethod
    def diff(self, remote: str, obj_name: str, **kwargs) -> str:
        """return diff to the desired obj

        Args:
            remote (str): remote Archive link
            obj_name (str): name of the desired object to be checked.

        Returns:
            str: string representing the diff to the changes done
        """
        pass

    @abstractmethod
    def local_path(self, remote: str, **kwargs) -> Path:
        """return the local path of the given remote Archive

        Args:
            remote (str): remote Archive link.

        Returns:
            Path: local path of the desired remote link.
        """
        pass
