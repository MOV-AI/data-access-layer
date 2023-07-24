"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020
Module that implements Configuration scope class
"""
import pickle
import yaml
from box import Box
from movai_core_shared.exceptions import DoesNotExist
from dal.movaidb import MovaiDB
from dal.helpers.cache import ThreadSafeCache
from .scope import Scope


class Configuration(Scope):
    """Configuration class"""

    scope = "Configuration"

    def __init__(self, name, version="latest", new=False, db="global"):
        super().__init__(scope="Configuration", name=name, version=version, new=new, db=db)
        self.__dict__["_db_read"] = MovaiDB(db).db_read
        self.__dict__["_data"] = {}
        self.__dict__["_cache"] = ThreadSafeCache()
        self.__dict__["_ref"] = f"Scopes:Configuration:{name}:{version}"
        self.__dict__["_str"] = self._get_db_yaml()

    def _get_db_yaml(self) -> str:
        """will read the Yaml string value from db and returns it

        Returns:
            str: the Yaml string returned from db
        """
        yaml_str = self._db_read.get(f"Configuration:{self.name},Yaml:")
        if yaml_str is not None:
            return pickle.loads(yaml_str)
        return yaml_str

    def get_value(self) -> dict:
        """Returns a dictionary with the configuration values"""
        if self.Type == "xml":
            # Yaml is the name of the field
            return self._get_db_yaml()

        db_yaml = self._get_db_yaml()
        if db_yaml != self._str or self._ref not in self._cache:
            # we need to update it because of the scopes caching system
            _data = yaml.load(db_yaml, Loader=yaml.FullLoader)
            self._cache[self._ref] = _data
            self.__dict__["_str"] = db_yaml

        return self._cache[self._ref]

    # ported
    def get_param(self, param: str):
        """Returns the configuration value of a key in the format param.subparam.subsubparam"""
        value = None
        dict_value = self.get_value()
        fields = param.split(".")
        try:
            temp_dict = dict_value
            for elem in fields:
                temp_dict = temp_dict[elem]
            value = temp_dict
        except Exception:
            raise Exception(
                '"%s" is not a valid parameter in configuration "%s"' % (param, self.name)
            )
        return value


class Config(Box):
    """Config with dot accessible elements"""

    def __init__(self, name):
        # raises DoesNotExist in case Configuration name does not exist
        config = Configuration(name).get_value()
        super().__init__(Box(config))
