from .base_model import MovaiBaseModel
from pydantic import Field, validator
import yaml
import json
from typing import List, Union, Any
import xmltodict


class Configuration(MovaiBaseModel):
    Type: str = "yaml"
    Yaml: str = ""
    data: dict = Field(default_factory=dict)  # runtime parameter

    def _original_keys(self) -> List[str]:
        return super()._original_keys() + ["Type", "Yaml"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.data:
            self._convert_yaml_dict()

    def get_value(self) -> dict:
        """Returns a dictionary with the configuration values"""
        return self.data

    def _convert_yaml_dict(self):
        data = yaml.load(self.Yaml, Loader=yaml.FullLoader)
        if isinstance(data, dict):
            self.data = data
            self.Type = "yaml"
        else:
            self.Type = "xml"
            self.data = xmltodict.parse(self.Yaml)

    def __setattr__(self, __name: str, __value: Any) -> None:
        ret = super().__setattr__(__name, __value)
        if __name == "Yaml":
            self._convert_yaml_dict()
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
                f'"{param}" is not a valid parameter in Configuration "{self.name}"'
            ) from exc

        return value
