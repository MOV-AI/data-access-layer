from os import stat, rmdir, symlink, unlink, remove
from os.path import isdir, isfile, expanduser, islink
from pathlib import Path
from shutil import rmtree
from types import SimpleNamespace

from git.refs import remote


class FileSystem:
    """.
    """
    def __init__(self):
        pass

    @classmethod
    def load(cls, file_path: str) -> SimpleNamespace:
        pass

    def save(self, file_path: str, file_type: str = "json") -> bool:
        pass

    def remove(self, path: str) -> bool:
        pass

    @staticmethod
    def remove_recursively(path: str):
        mydir = Path(path)
        rmtree(mydir)

    @staticmethod
    def exist(path):
        if isdir(path) or isfile(path):
            return True
        return False

    @staticmethod
    def create_folder_recursively(folder_path):
        # somehow Path.mkdir does not work properly with ~
        folder_path = folder_path.replace('~', FileSystem.get_home_folder())
        if not isdir(folder_path):
            Path(folder_path).mkdir(parents=True, exist_ok=True)
        return folder_path

    @staticmethod
    def get_home_folder():
        return expanduser("~")

    @staticmethod
    def create_symbolic_link(src, dst):
        if islink(dst):
            unlink(dst)
        symlink(src, dst)
