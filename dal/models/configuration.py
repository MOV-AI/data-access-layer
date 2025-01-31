"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva  (manuel.silva@mov.ai) - 2020
   - Moawiya Mograni (moawiya@mov.ai) - 2023
"""
import pickle
import yaml
from dal.movaidb import MovaiDB
from .model import Model
from dal.helpers.cache import ThreadSafeCache
from movai_core_shared.logger import Log
from dal.classes.common.singleton import Singleton

LOGGER = Log.get_logger("ParamParser.mov.ai")

class ConfigirationCache(metaclass=Singleton):
    def __init__(self):
        self._map = {}

    def yaml_load(self, config_name, yaml_str):
        with self.__class__._lock:  # Lock for thread safety
            map_key = config_name
            if map_key in self._map:
                return self._map[map_key]
            value = yaml.load(yaml_str, Loader=yaml.FullLoader)
            self._map[map_key] = value
            return value
    
    def clean_config_cache(self):
        with self.__class__._lock:
            self._map = {}
        
class Configuration(Model):
    """
    Provides xml or yaml configuration
    """
    logger = Log.get_logger("ParamParser.mov.ai")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = MovaiDB().db_read
        self.cache = ThreadSafeCache()

    def _get_db_yaml(self) -> str:
        """will read the Yaml string value from db and returns it

        Returns:
            str: the Yaml string returned from db
        """
        return pickle.loads(self.db.get(f"Configuration:{self.ref},Yaml:"))

    def get_value(self) -> dict:
        """Returns a dictionary with the configuration values"""
        
        if self.Type == "xml":
            # Yaml is the name of the field
            return self.Yaml

        config_dict = ConfigirationCache().yaml_load(self.ref, self.Yaml)
        return config_dict

    def get_param(self, param: str) -> any:
        """Returns the configuration value of a key in the format param.subparam.subsubparam"""

        value = None
        dict_value = self.get_value()
        fields = param.split(".")
        try:
            temp_dict = dict_value

            for elem in fields:
                temp_dict = temp_dict[elem] if elem in temp_dict else None

                if temp_dict is None:
                    # this means either temp_dict returned None (happens when key: _empty_) or missing key
                    break

            value = temp_dict

        except Exception as exc:
            raise Exception(
                f'"{param}" is not a valid parameter in configuration "{self.path}"'
            ) from exc
        return value

# Register class as model of scope Flow
Model.register_model_class("Configuration", Configuration)
