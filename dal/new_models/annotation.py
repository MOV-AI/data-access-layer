from typing import Dict, Optional, Any, Union, List
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

    @classmethod
    def _original_keys(cls) -> List[str]:
        return super()._original_keys() + ["Type", "Policy", "Parameter", "Field"]

    def get_computed_annotation(self) -> Dict:
        """Get computed annotation keys

        Returns:
        Dict: Dict of all annotation keys and values evaluated
        """

        res_dict = {}
        fields = self.Field or {
            x[0]: FieldValue(Type=self._get_data_type(x[1]), Value=x[1]) for x in self.Parameter.items()
        }
        for key in fields:
            computed = self._generate_computed(key, fields[key], self.ref)
            res_dict[key] = computed
        return res_dict

    def _get_data_type(self, data):
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

    def _generate_computed(self, property_name, annotation_property, annotation_path):
        """Helper function to generate computed annotation key based on annotation property"""
        prop_value = annotation_property.Value
        prop_type = annotation_property.Type
        configuration_name = prop_value if prop_type == "config" else None
        return {
            "key": property_name,
            "annotation": {
                "name": annotation_path,
                "key": property_name,
                "type": prop_type,
                "value": prop_value,
            },
            "value": self._get_configuration_value(configuration_name)
            if configuration_name
            else prop_value,
        }

    def _get_configuration_value(self, configuration_path):
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
