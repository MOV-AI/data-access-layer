
class GitException(Exception):
    def __init__(self, error, *args: object) -> None:
        self._error = error
        super().__init__(*args)

    @property
    def value(self):
        return self._error


class VersionDoesNotExist(GitException):
    def __init__(self, *args):
        super().__init__(5, *args)


class BranchAlreadyExist(GitException):
    def __init__(self, *args):
        super().__init__(6, *args)


class NoChangesToCommit(GitException):
    def __init__(self, *args):
        super().__init__(7, *args)


class SlaveManagerCannotChange(GitException):
    def __init__(self, *args: object) -> None:
        super().__init__(8, *args)


class TagAlreadyExist(GitException):
    def __init__(self, *args: object) -> None:
        super().__init__(9, *args)
