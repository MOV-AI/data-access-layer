from typing import Dict, Optional, Any, Union
from types import SimpleNamespace
import pydantic
from .base_model import MovaiBaseModel
from .configuration import Configuration
from movai_core_shared.logger import Log

logger = Log.get_logger(__name__)
PARAMETER_KEY_REGEX = pydantic.constr(regex=r"^[0-9a-zA-Z_]+$")
FIELD_KEY_REGEX = pydantic.constr(regex=r"^[0-9a-zA-Z_!@?-]+$")


class FieldValue(pydantic.BaseModel):
    Type: Optional[str] = None
    Value: Optional[Union[str, bool]] = None


class Annotation(MovaiBaseModel):
    Type: Optional[str] = None
    Policy: Optional[str] = None
    Parameter: Optional[Dict[PARAMETER_KEY_REGEX, Any]] = pydantic.Field(default_factory=dict)
    Field: Optional[Dict[FIELD_KEY_REGEX, FieldValue]] = pydantic.Field(default_factory=dict)

    class Meta:
        model_key_prefix = "Annotation"

    def get_computed_annotation(self) -> Dict:
        """Get computed annotation keys

        Returns:
        Dict: Dict of all annotation keys and values evaluated
        """

        res_dict = {}
        fields = self.Field or self.parameter_to_field(self.Parameter)
        for key in fields:
            computed = self.generate_computed(key, fields[key], self.ref)
            res_dict[key] = computed
        return res_dict

    def parameter_to_field(self, param):
        """Helper function to transform Annotation parameter into the same format as Field"""
        return {
            x[0]: {
                "Value": SimpleNamespace(**{"value": x[1]}),
                "Type": SimpleNamespace(**{"value": self.get_data_type(x[1])}),
            }
            for x in param.items()
        }

    def get_data_type(self, data):
        """Helper function to get data type of a given value (in same format of front-end)"""
        predicates_to_value = [
            {"predicate": isinstance(data, str), "value": "string"},
            {
                "predicate": isinstance(data, int) and not isinstance(data, bool),
                "value": "number",
            },
            {"predicate": isinstance(data, float), "value": "number"},
            {"predicate": isinstance(data, bool), "value": "boolean"},
            {"predicate": isinstance(data, dict), "value": "object"},
            {"predicate": isinstance(data, list), "value": "array"},
            {"predicate": True, "value": "any"},
        ]
        # return data type
        return [x for x in predicates_to_value if x["predicate"]][0]["value"]

    def generate_computed(self, property_name, annotation_property, annotation_path):
        """Helper function to generate computed annotation key based on annotation property"""
        prop_value = annotation_property["Value"].value
        prop_type = annotation_property["Type"].value
        configuration_name = prop_value if prop_type == "config" else None
        return {
            "key": property_name,
            "annotation": {
                "name": annotation_path,
                "key": property_name,
                "type": prop_type,
                "value": prop_value,
            },
            "value": self.get_configuration_value(configuration_name)
            if configuration_name
            else prop_value,
        }

    def get_configuration_value(self, configuration_path):
        """Helper function to get a configuration value from a config path"""
        if not configuration_path:
            return {}
        try:
            config_key_path = configuration_path.split(".")
            config_name = config_key_path[0]
            config_key_path.pop(0)
            config = Configuration(config_name)
            return config.get_param(config_key_path)
        except Exception as e:  # pylint: disable=broad-except
            logger.error(e)
            return {}
