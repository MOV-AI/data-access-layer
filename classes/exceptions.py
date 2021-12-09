BASE_GIT_ERR = 10

VERSION_DOES_NOT_EXIST_ERR = BASE_GIT_ERR + 1
BRANCH_ALREADY_EXIST_ERR = BASE_GIT_ERR + 2
NO_CHANGES_TO_COMMIT = BASE_GIT_ERR + 3
SLAVE_MANAGER_CANNOT_CHANGE = BASE_GIT_ERR + 4
TAG_ALREADY_EXIST = BASE_GIT_ERR + 5


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
        super().__init__(NO_CHANGES_TO_COMMIT, *args)


class SlaveManagerCannotChange(GitException):
    def __init__(self, *args: object) -> None:
        super().__init__(SLAVE_MANAGER_CANNOT_CHANGE, *args)


class TagAlreadyExist(GitException):
    def __init__(self, *args: object) -> None:
        super().__init__(TAG_ALREADY_EXIST, *args)
