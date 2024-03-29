"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2023
   - Erez Zomer (erez@mov.ai) - 2023
"""
from typing import List, Any
import xmltodict
import yaml

from box import Box

from pydantic import Field, constr, field_validator

from movai_core_shared.exceptions import ConfigurationError
from .base import MovaiBaseModel


class Configuration(MovaiBaseModel):
    """A class that implements the Configuration Model."""

    Type: constr(to_lower=True) = "yaml"
    Yaml: str = ""
    data: dict = Field(default_factory=dict)  # runtime parameter

    @field_validator("Type", mode="before")
    @classmethod
    def _validate_type(cls, value):
        if value is None or value == "":
            return "yaml"
        return value

    @classmethod
    def _original_keys(cls) -> List[str]:
        """keys that are originally defined part of the model.

        Returns:
            List[str]: list including the original keys
        """
        return super()._original_keys() + ["Type", "Yaml"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.data:
            self._parse_data()

    def get_value(self) -> dict:
        """Returns a dictionary with the configuration values"""
        return self.data

    def _parse_data(self):
        try:
            if self.Type == "yaml" or self.Type == "Yaml":
                data = yaml.load(self.Yaml, Loader=yaml.FullLoader)
            elif self.Type == "xml":
                data = xmltodict.parse(self.Yaml)
            else:
                raise ConfigurationError(f"The format {self.Type} is Unknown")
            if data is None:
                data = dict()
        except Exception as exc:
            raise ConfigurationError(f"Got an error while parsin data: {str(exc)}") from exc

        if not isinstance(data, dict):
            raise ConfigurationError(f"Parsing the data of configuration {self.name} failed.")
        self.data = data

    def __setattr__(self, __name: str, __value: Any) -> None:
        ret = super().__setattr__(__name, __value)
        if __name == "Yaml":
            self._parse_data()
        return ret

    def get_param(self, param: str) -> any:
        """Returns the configuration value of a key in the format param.subparam.subsubparam"""
        value = None
        fields = param.split(".")
        try:
            temp_dict = self.data
            for elem in fields:
                temp_dict = temp_dict[elem] if elem in temp_dict else None
                if temp_dict is None:
                    # this means either temp_dict returned None (happens when key: _empty_) or missing key
                    break
            value = temp_dict

        except Exception as exc:
            raise Exception(
                f"{param} is not a valid parameter in Configuration {self.name}"
            ) from exc

        return value


class Config(Box):
    """Config with dot accessible elements"""

    def __init__(self, name):
        # raises DoesNotExist in case Configuration name does not exist
        config = Configuration(name).get_value()
        super().__init__(Box(config))
