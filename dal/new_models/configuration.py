
from .base_model import MovaiBaseModel
from pydantic import Field, validator
import yaml
import json
from typing import List, Union
import xmltodict


class Configuration(MovaiBaseModel):
    Type: str = "yaml"
    Yaml: dict = Field(default_factory=dict)

    def _original_keys(self) -> List[str]:
        return super()._original_keys() + ["Type", "Yaml"]

    class Meta:
        model_key_prefix = "Configuration"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @validator("Yaml", pre=True, always=True)
    def _validate_data(cls, v):
        if isinstance(v, str):
            res = yaml.load(v, Loader=yaml.FullLoader)
            if isinstance(res, dict):
                return res
            if isinstance(res, str):
                return xmltodict.parse(v)
        if not isinstance(v, dict):
            return {}
        return v

    def get_param(self, param: str) -> any:
        """ Returns the configuration value of a key in the format param.subparam.subsubparam """
        value = None
        fields = param.split('.')
        try:
            temp_dict = self.Yaml
            for elem in fields:
                temp_dict = temp_dict[elem] if elem in temp_dict else None 
                if temp_dict is None:
                    # this means either temp_dict returned None (happens when key: _empty_) or missing key
                    break
            value = temp_dict

        except Exception as exc:
            raise Exception(
                f'"{param}" is not a valid parameter in Configuration "{self.name}"') from exc

        return value
