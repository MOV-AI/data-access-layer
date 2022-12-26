from abc import abstractmethod
from pathlib import Path
from typing import Any
from dal.exceptions import (
    NoActiveArchiveRegistered,
    ArchiveNotRegistered,
    ArchiveAlreadyRegistered,
)


class BaseArchive:
    active_archive = None
    classes = {}

    def __call__(self, user: str = "MOVAI_USER") -> "BaseArchive":
        """whenever an instance of Archive is called this method should run and
           return an instance of the active archive

        Args:
            user (str, optional): the user to be used in the Archive.
                                  in case None the Archive should handle this.
                                  Defaults to None.

        Raises:
            NoActiveArchiveRegistered: in case there was no active archive
                                       registered.

        Returns:
            BaseArchive: an instance of the Active Archive used in code.
        """
        if BaseArchive.active_archive is None:
            raise NoActiveArchiveRegistered("")
        return BaseArchive.active_archive.get_client(user)

    def __init_subclass__(cls, id=None):
        if id is None:
            return
        if id in BaseArchive.classes:
            raise ArchiveAlreadyRegistered(f"Archive id={id}")

        BaseArchive.classes[id] = cls

    @classmethod
    def set_active_archive(cls, name):
        if name not in cls.classes:
            raise ArchiveNotRegistered(name)
        cls.active_archive = cls.classes[name]

    @abstractmethod
    def get_client(self, **kwargs) -> "BaseArchive":
        """instantiate Archive instance and returns it."""

    @abstractmethod
    def get(self, obj_name: str, remote: str, version: str, **kwargs) -> Path:
        """Get an Object from remote Archive, and save it locally.

        Args:
            obj_name (str): Name of the object.
            remote (str): Remote link.
            version (str): Version desired.

        Returns:
            Path: the local path of the requested File.
        """

    @abstractmethod
    def delete(self, remote: str, obj_name: str, version: str, **kwargs) -> str:
        """deletes an object.

        Args:
            obj_name (str): Name of the object (path)
            remote (str): Remote link.
            version (str): Version desired to remove from.

        Returns:
            str: new version hash.
        """

    @abstractmethod
    def commit(self, obj_name: str, remote: str, **kwargs) -> str:
        """saves changes locally, will create new version if requested.

        Args:
            obj_name (str): name of object to comit
            remote (str): the remote link of the repo.

        Returns:
            str: new version hash
        """

    @abstractmethod
    def pull(self, remote: str, **kwargs) -> Any:
        """pull changes from remote Archive to local one.

        Args:
            remote (str): remote link of Archive
        """

    @abstractmethod
    def push(self, remote: str, **kwargs) -> Any:
        """push changes from local to remote Archive.

        Args:
            remote (str): remote Archive link
        """

    @abstractmethod
    def create_obj(self, remote: str, relative_path: str, content: str, **kwargs):
        """will create new obj locally (relative path to local archive)
           of the local repository path.

        Args:
            remote (str): the remote archive link
            relative_path (str): the relative path to the root of the local archive
            content (str): the obj content to be added
        """

    @abstractmethod
    def diff(self, remote: str, obj_name: str, **kwargs) -> str:
        """return diff to the desired obj

        Args:
            remote (str): remote Archive link
            obj_name (str): name of the desired object to be checked.

        Returns:
            str: string representing the diff to the changes done
        """

    @abstractmethod
    def local_path(self, remote: str, **kwargs) -> Path:
        """return the local path of the given remote Archive

        Args:
            remote (str): remote Archive link.

        Returns:
            Path: local path of the desired remote link.
        """

    @abstractmethod
    def revert(self, remote: str, ob_name: str, version: str, **kwargs) -> Path:
        """revert a given version to previous one and return the file path
           for the reverted version

        Args:
            remote (str): the remote link of the repository.
            obj_name (str): Name of the object (path).
            version (str): the version we want to revert

        Returns:
            Path: the local path of the requested File.
        """

    @abstractmethod
    def create_version(
        self, remote: str, base_version: str, new_version: str, **kwargs
    ) -> bool:
        """create a new version based on another version.

        Args:
            remote (str): remote Archive link.
            base_version (str): the base version.
            new_version (str): the new desired version.

        Returns:
            bool: True/False whether the creation succeeded or not.
        """
