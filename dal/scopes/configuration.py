"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020
Module that implements Configuration scope class
"""
import yaml
from box import Box
from movai_core_shared.exceptions import DoesNotExist
from dal.movaidb import MovaiDB
from .scope import Scope


class Configuration(Scope):
    """Configuration class"""

    scope = "Configuration"

    def __init__(self, name, version="latest", new=False, db="global"):
        super().__init__(
            scope="Configuration", name=name, version=version, new=new, db=db
        )

    # ported
    def get_value(self) -> dict:
        """Returns a dictionary with the configuration values"""
        if self.Type == "xml":
            return self.Yaml
        return yaml.load(self.Yaml, Loader=yaml.FullLoader)

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
                '"%s" is not a valid parameter in configuration "%s"'
                % (param, self.name)
            )
        return value


class Config(Box):
    """Config with dot accessible elements"""

    def __init__(self, name):
        config = MovaiDB().get_value({"Configuration": {name: {"Yaml": ""}}})
        if not config:
            raise DoesNotExist("Configuration %s was not found" % config)
        config = yaml.load(config, Loader=yaml.FullLoader)
        super().__init__(Box(config))
