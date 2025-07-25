"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2022

   DAL Exceptions
"""
from enum import IntEnum


class GitErr(IntEnum):
    BASE_GIT_ERR = 100
    VERSION_DOES_NOT_EXIST_ERR = 101
    BRANCH_ALREADY_EXIST_ERR = 102
    NO_CHANGES_TO_COMMIT_ERR = 103
    SLAVE_MANAGER_CANNOT_CHANGE_ERR = 104
    TAG_ALREADY_EXIST_ERR = 105
    GIT_USER_ERR = 106
    FILE_DOES_NOT_EXIST = 107
    REPO_DOES_NOT_EXIST = 108
    GIT_PERMISSION_ERR = 109


class SchemaErr(IntEnum):
    BASE_SCHEMA_ERR = 200
    SCHEMA_VERSION_ERR = 201
    SCHEMA_TYPE_NOT_KNOWN = 202
    SCHEMA_LOAD_ERR = 203


class ValidationErr(IntEnum):
    BASE_VALIDATION_ERR = 300
    VALIDATION_ERR = 301


class ArchiveErr(IntEnum):
    BASE_ARCHIVE_ERR = 400
    NO_ACTIVE_ARCHIVE_REGISTERED = 401
    ARCHIVE_NOT_REGISTERED = 402
    ARCHIVE_ALREADY_REGISTERED = 403


class DalException(Exception):
    pass


# Git Errors
# ----------------------------------------------------------------------------
class GitException(DalException):
    def __init__(self, error, *args: object) -> None:
        self._error = error
        super().__init__(*args)

    @property
    def value(self):
        return self._error


class VersionDoesNotExist(GitException):
    def __init__(self, *args):
        super().__init__(GitErr.VERSION_DOES_NOT_EXIST_ERR, *args)


class BranchAlreadyExist(GitException):
    def __init__(self, *args):
        super().__init__(GitErr.BRANCH_ALREADY_EXIST_ERR, *args)


class NoChangesToCommit(GitException):
    def __init__(self, *args):
        super().__init__(GitErr.NO_CHANGES_TO_COMMIT_ERR, *args)


class SlaveManagerCannotChange(GitException):
    def __init__(self, *args: object) -> None:
        super().__init__(GitErr.SLAVE_MANAGER_CANNOT_CHANGE_ERR, *args)


class TagAlreadyExist(GitException):
    def __init__(self, *args: object) -> None:
        super().__init__(GitErr.TAG_ALREADY_EXIST_ERR, *args)


class GitUserErr(GitException):
    def __init__(self, *args: object) -> None:
        super().__init__(GitErr.GIT_USER_ERR, *args)


class FileDoesNotExist(GitException):
    def __init__(self, *args):
        super().__init__(GitErr.FILE_DOES_NOT_EXIST, *args)


class RepositoryDoesNotExist(GitException):
    def __init__(self, *args):
        super().__init__(GitErr.REPO_DOES_NOT_EXIST, *args)


class GitPermissionErr(GitException):
    def __init__(self, *args):
        super().__init__(GitErr.GIT_PERMISSION_ERR, *args)


# Schema Errors
# ----------------------------------------------------------------------------
class SchemaException(DalException):
    def __init__(self, error, *args: object) -> None:
        self._error = error
        super().__init__(*args)

    @property
    def value(self):
        return self._error


class SchemaVersionError(SchemaException):
    def __init__(self, *args: object) -> None:
        super().__init__(SchemaErr.SCHEMA_VERSION_ERR, *args)


class SchemaTypeNotKnown(SchemaException):
    def __init__(self, *args: object) -> None:
        super().__init__(SchemaErr.SCHEMA_TYPE_NOT_KNOWN, *args)


class SchemaLoadError(SchemaException):
    def __init__(self, *args: object) -> None:
        super().__init__(SchemaErr.SCHEMA_LOAD_ERR, *args)


# Validation Errors
# ----------------------------------------------------------------------------
class ValidationException(DalException):
    def __init__(self, error, *args: object) -> None:
        self._error = error
        super().__init__(*args)

    @property
    def value(self):
        return self._error


class ValidationError(ValidationException):
    def __init__(self, *args: object) -> None:
        super().__init__(ValidationErr.VALIDATION_ERR, *args)


# Archive Errors
# ----------------------------------------------------------------------------
class ArchiveException(DalException):
    def __init__(self, error, *args: object) -> None:
        self._error = error
        super().__init__(*args)


class NoActiveArchiveRegistered(ArchiveException):
    def __init__(self, *args: object) -> None:
        super().__init__(ArchiveErr.NO_ACTIVE_ARCHIVE_REGISTERED, *args)


class ArchiveNotRegistered(ArchiveException):
    def __init__(self, *args: object) -> None:
        super().__init__(ArchiveErr.ARCHIVE_NOT_REGISTERED, *args)


class ArchiveAlreadyRegistered(ArchiveException):
    def __init__(self, *args: object) -> None:
        super().__init__(ArchiveErr.ARCHIVE_ALREADY_REGISTERED, *args)
