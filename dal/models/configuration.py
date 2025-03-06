"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva  (manuel.silva@mov.ai) - 2020
   - Moawiya Mograni (moawiya@mov.ai) - 2023
"""
import pickle
from typing import Any
import yaml
from dal.movaidb import MovaiDB
from .model import Model
from dal.helpers.cache import ThreadSafeCache


class Configuration(Model):
    """
    Provides xml or yaml configuration
    """

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

    def get_value(self, cached=True) -> dict:
        """Returns a dictionary with the configuration values"""
        if self.Type == "xml":
            # Yaml is the name of the field
            return self.Yaml
        # Don't need to go to DB, the schema is already loaded in the constructor of the class
        # TODO:We can implement a proper caching system later to save this yaml.load operation
        return yaml.load(self.Yaml, Loader=yaml.FullLoader)

    def get_param(self, param: str) -> Any:
        """Returns the configuration value of a key in the format param.subparam.subsubparam"""

        dict_value = self.get_value()
        fields = param.split(".")

        try:
            temp_dict = dict_value

            for elem in fields:
                temp_dict = temp_dict.get(elem)
                if temp_dict is None:
                    # this means either temp_dict returned None (happens when key: _empty_) or missing key
                    break

            return temp_dict

        except Exception as exc:
            raise Exception(
                f'"{param}" is not a valid parameter in configuration "{self.path}"'
            ) from exc


# Register class as model of scope Flow
Model.register_model_class("Configuration", Configuration)
