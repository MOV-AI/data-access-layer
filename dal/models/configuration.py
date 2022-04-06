"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva  (manuel.silva@mov.ai) - 2020
"""
import yaml
from .model import Model


class Configuration(Model):
    """
    Provides xml or yaml configuration
    """

    def get_value(self) -> dict:
        """Returns a dictionary with the configuration values"""

        if self.Type == "xml":

            # Yaml is the name of the field
            return self.Yaml

        return yaml.load(self.Yaml, Loader=yaml.FullLoader)

    def get_param(self, param: str) -> any:
        """ Returns the configuration value of a key in the format param.subparam.subsubparam """

        value = None

        dict_value = self.get_value()

        fields = param.split('.')

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
                f'"{param}" is not a valid parameter in configuration "{self.path}"') from exc

        return value


# Register class as model of scope Flow
Model.register_model_class("Configuration", Configuration)
