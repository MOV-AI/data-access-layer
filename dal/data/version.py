"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
from abc import ABC, abstractproperty
from .tree import CallableNode


class VersionObject(ABC):
    """
    A versionable object, it handles different versions of
    the same object
    """

    @abstractproperty
    def version(self):
        """
        the current version
        """
        raise NotImplementedError


class VersionNode(CallableNode, VersionObject):
    """
    Implements a Schema Versions Node
    """

    def __init__(self, version):
        self._version = version
        super().__init__()

    @property
    def version(self):
        """
        The current version
        """
        return self._version

    @property
    def node_type(self):
        return "version"

    @property
    def path(self):
        """
        get the tree path
        """
        if self.parent is None:
            return self._version

        return f"{self.parent.path}/{self._version}"
