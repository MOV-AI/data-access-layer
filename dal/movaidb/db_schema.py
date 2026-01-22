from os import path
from typing import Dict

from dal.plugins.classes import Resource
from dal.validation import SCHEMA_FOLDER_PATH


class DBSchema(dict):
    """Represents the database schema for each scope."""

    __API__: Dict[str, Dict[str, Dict]] = {}  # First key is the Version, the second is the scope

    def __init__(self):
        super(type(self), self).__init__()  # pylint: disable=bad-super-call
        self.__version = "1.0"
        self.__url = path.join(SCHEMA_FOLDER_PATH, self.__version)

        if self.__version not in type(self).__API__:
            self.load_schemas_from_files()

    def load_schemas_from_files(self):
        """Load builtins schemas."""
        type(self).__API__[self.version] = {
            path.splitext(schema_file)[0]: Resource.read_json(path.join(self.__url, schema_file))[
                "schema"
            ]
            for schema_file in Resource.list_resources(self.__url)
            if schema_file.endswith(".json")
        }

    @property
    def version(self):
        """Current version"""
        return self.__version

    @property
    def url(self):
        """Base uri"""
        return self.__url

    def __setitem__(self, key, value):
        raise NotImplementedError

    def __getitem__(self, key):
        return type(self).__API__[self.__version][key]

    def __iter__(self):
        return type(self).__API__[self.__version].__iter__

    def __repr__(self):
        return type(self).__API__[self.__version].__repr__()

    def __str__(self):
        return type(self).__API__[self.__version].__str__()

    def keys(self):
        return type(self).__API__[self.__version].keys()

    def values(self):
        return type(self).__API__[self.__version].values()

    def get_api(self):
        """
        return the current API
        """
        return type(self).__API__[self.__version]
