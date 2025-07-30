"""Copyright (C) Mov.ai  - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential

Developers:
- Moawiya Mograbi (moawiya@mov.ai) - 2022
"""

from pathlib import Path
from json import load


class FileSystem:
    """FileSystem class that will handle all functions related to
    creating/deleting/modifying files on the system locally.
    """

    def __init__(self):
        pass

    @staticmethod
    def read_json(path: Path) -> dict:
        """Read a json file.

        Args:
            path (Path): The file path to read from.

        Returns:
            dict: Dict representation of the json file.

        """
        with open(path, "r") as file:
            return load(file)
