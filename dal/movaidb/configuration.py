"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2022
"""

from os import path
from dal.plugins import Resource

dir_path = path.dirname(path.realpath(__file__))
__SCHEMAS_URL__ = f"file://{dir_path}/../validation/schema"


class Configuration:
    class API(dict):
        """
        # Represents the API template dict. Can be Imported or saved into Redis
        """

        __API__ = {}

        def __init__(self, version: str = "latest", url: str = __SCHEMAS_URL__):
            super(type(self), self).__init__()
            # We force the version of the schemas to the deprecated version
            version = "1.0"
            self.__url = path.join(url, version)
            self.__version = version
            if version not in type(self).__API__:
                # load builtins schemas
                current_path = path.join(url, version)
                type(self).__API__[version] = {
                    path.splitext(schema_file)[0]: Resource.read_json(
                        path.join(current_path, schema_file)
                    )["schema"]
                    for schema_file in Resource.list_resources(current_path)
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

        @classmethod
        def get_schema(cls, version, name):
            """
            return scope schema for the specifed version
            """
            try:
                return cls(version=version).get_api()[name]
            except KeyError:
                return {}

        def get_api(self):
            """
            return the current API
            """
            return type(self).__API__[self.__version]
