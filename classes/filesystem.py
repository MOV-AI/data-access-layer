from os import symlink, unlink
from os.path import isdir, isfile, expanduser, islink
from pathlib import Path
from shutil import rmtree
from types import SimpleNamespace
from json import dump as json_dump


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
    def read(path):
        if not FileSystem.exist(path):
            raise Exception(f"file does not exist {path}")
        with open(path) as f:
            return f.read()

    @staticmethod
    def write(path, content, is_json=True):
        with open(path, "w+") as f:
            if is_json:
                json_dump(content, f, indent=4)
            else:
                f.write(content)

    @staticmethod
    def create_folder_recursively(folder_path) -> str:
        """creates a folder recursively with parent if does not exist

        Args:
            folder_path (str): desired folder path

        Returns:
            str: the created folder path
        """
        # somehow Path.mkdir does not work properly with ~
        folder_path = folder_path.replace('~', FileSystem.get_home_folder())
        if not isdir(folder_path):
            Path(folder_path).mkdir(parents=True, exist_ok=True)
        return folder_path

    @staticmethod
    def get_home_folder() -> str:
        """returns the absolute path of the home folder.

        Returns:
            str: path
        """
        return expanduser("~")

    @staticmethod
    def create_symbolic_link(src, dst):
        """creates symbolic link dst->str
           src folder had to exist, the dst is created as symlink

        Args:
            src (str): the target which we want the symbolic link point to
            dst (str): the symbolic link we want to create
        """
        if islink(dst):
            unlink(dst)
        symlink(src, dst)
