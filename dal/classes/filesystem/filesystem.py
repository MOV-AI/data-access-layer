"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2022
"""

from os import symlink, unlink, rename
from os.path import isdir, isfile, expanduser, islink, dirname
from pathlib import Path
from shutil import rmtree
from json import dump as json_dump


class FileSystem:
    """FileSystem class that will handle all functions related to
       creating/deleting/modifying files on the system locally.
    """
    def __init__(self):
        pass

    @staticmethod
    def remove_recursively(path: str):
        """remove given path recursively in case it included
           another folders inside it

        Args:
            path (str): the path to folder/file
        """
        if isdir(path):
            mydir = Path(path)
            rmtree(mydir)

    @staticmethod
    def is_exist(path: str) -> bool:
        """check if the giver path file/folder do exist in filesystem

        Args:
            path (str): the path to check

        Returns:
            bool: whether the path exist locally or not.
        """
        if isdir(path) or isfile(path):
            return True
        return False

    @staticmethod
    def read(path: str) -> str:
        """read the given file and returns it's content

        Args:
            path (str): the file path to read from

        Raises:
            Exception: in case file does not exist

        Returns:
            str: file content
        """
        content = ""
        if not FileSystem.is_exist(path):
            raise Exception(f"file does not exist {path}")
        with open(path) as f:
            content = f.read()
        return content

    @staticmethod
    def write(path, content, is_json=True):
        """write given content to the given path
           in case path foes not exist it will be created.

        Args:
            path (str): the path to write to
            content (str/json): the content to be written
            is_json (bool, optional): specifying if it a json file or not.
                                      Defaults to True.
        """
        folder_path = dirname(path)
        FileSystem.create_folder_recursively(folder_path)
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
        """creates symbolic link dst->src
           src folder had to exist, the dst is created as symlink

        Args:
            src (str): the target which we want the symbolic link point to
            dst (str): the symbolic link we want to create
        """
        if islink(dst):
            unlink(dst)
        symlink(src, dst)

    @staticmethod
    def rename_folder(folder_path: str, new_name: str):
        """rename given folder to a new_name

        Args:
            folder_path (str): the current path of the folder
            new_name (str): the new folder name.

        Raises:
            Exception: in case folder does not exist
        """
        if not isdir(folder_path):
            raise Exception(f"folder {folder_path} does not exist")
        rename(folder_path, new_name)
