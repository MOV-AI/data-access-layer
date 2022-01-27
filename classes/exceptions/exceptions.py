BASE_GIT_ERR = 100
VERSION_DOES_NOT_EXIST_ERR = BASE_GIT_ERR + 1
BRANCH_ALREADY_EXIST_ERR = BASE_GIT_ERR + 2
NO_CHANGES_TO_COMMIT_ERR = BASE_GIT_ERR + 3
SLAVE_MANAGER_CANNOT_CHANGE_ERR = BASE_GIT_ERR + 4
TAG_ALREADY_EXIST_ERR = BASE_GIT_ERR + 5

BASE_SCHEMA_ERR = 200
SCHEMA_VERSION_ERR = BASE_SCHEMA_ERR + 1
SCHEMA_TYPE_NOT_KNOWN = BASE_SCHEMA_ERR + 2

BASE_VALIDATION_ERR = 300
VALIDATION_ERR = BASE_VALIDATION_ERR + 1


# Git Errors
# ----------------------------------------------------------------------------
class GitException(Exception):
    def __init__(self, error, *args: object) -> None:
        self._error = error
        super().__init__(*args)

    @property
    def value(self):
        return self._error


class VersionDoesNotExist(GitException):
    def __init__(self, *args):
        super().__init__(VERSION_DOES_NOT_EXIST_ERR, *args)


class BranchAlreadyExist(GitException):
    def __init__(self, *args):
        super().__init__(BRANCH_ALREADY_EXIST_ERR, *args)


class NoChangesToCommit(GitException):
    def __init__(self, *args):
        super().__init__(NO_CHANGES_TO_COMMIT_ERR, *args)


class SlaveManagerCannotChange(GitException):
    def __init__(self, *args: object) -> None:
        super().__init__(SLAVE_MANAGER_CANNOT_CHANGE_ERR, *args)


class TagAlreadyExist(GitException):
    def __init__(self, *args: object) -> None:
        super().__init__(TAG_ALREADY_EXIST_ERR, *args)


# Schema Errors
# ----------------------------------------------------------------------------
class SchemaException(Exception):
    def __init__(self, error, *args: object) -> None:
        self._error = error
        super().__init__(*args)

    @property
    def value(self):
        return self._error


class SchemaVersionError(SchemaException):
    def __init__(self, *args: object) -> None:
        super().__init__(SCHEMA_VERSION_ERR, *args)


class SchemaTypeNotKnown(SchemaException):
    def __init__(self, *args: object) -> None:
        super().__init__(SCHEMA_TYPE_NOT_KNOWN, *args)


# Validation Errors
# ----------------------------------------------------------------------------
class ValidationException(Exception):
    def __init__(self, error, *args: object) -> None:
        self._error = error
        super().__init__(*args)

    @property
    def value(self):
        return self._error


class ValidationError(ValidationException):
    def __init__(self, *args: object) -> None:
        super().__init__(SCHEMA_VERSION_ERR, *args)
