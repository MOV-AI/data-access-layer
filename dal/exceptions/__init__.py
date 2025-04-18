"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2022
"""

from .exceptions import (
    VersionDoesNotExist,
    BranchAlreadyExist,
    NoChangesToCommit,
    SlaveManagerCannotChange,
    TagAlreadyExist,
    GitUserErr,
    SchemaTypeNotKnown,
    SchemaVersionError,
    ValidationError,
    NoActiveArchiveRegistered,
    ArchiveNotRegistered,
    ArchiveAlreadyRegistered,
    FileDoesNotExist,
    RepositoryDoesNotExist,
    GitPermissionErr,
)

__all__ = [
    "VersionDoesNotExist",
    "BranchAlreadyExist",
    "NoChangesToCommit",
    "SlaveManagerCannotChange",
    "TagAlreadyExist",
    "GitUserErr",
    "SchemaTypeNotKnown",
    "SchemaVersionError",
    "ValidationError",
    "NoActiveArchiveRegistered",
    "ArchiveNotRegistered",
    "ArchiveAlreadyRegistered",
    "FileDoesNotExist",
    "RepositoryDoesNotExist",
    "GitPermissionErr",
]
