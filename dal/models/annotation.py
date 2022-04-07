"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Tiago Teixeira  (tiago.teixeira@mov.ai) - 2020

   Annotation Model
"""
from typing import Dict
from types import SimpleNamespace
from dal.scopes import ScopesTree
from movai_core_shared.logger import Log
from .model import Model

logger = Log.get_logger('Annotation')


class Annotation(Model):
    """ Annotation Model """

    # default __init__

    def get_computed_annotation(self) -> Dict:
        """ Get computed annotation keys

        Returns:
        Dict: Dict of all annotation keys and values evaluated
        """

        res_dict = {}
        if "Field" in self:
            fields = self.Field
        else:
            fields = parameter_to_field(self.Parameter)  # populate computed_annotations_dict
        for key in fields:
            computed = generate_computed(key, fields[key], self.ref)
            res_dict[key] = computed
        return res_dict


Model.register_model_class("Annotation", Annotation)

def generate_computed(property_name, annotation_property, annotation_path):
    """ Helper function to generate computed annotation key based on annotation property """
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
        "value": get_configuration_value(configuration_name) if configuration_name else prop_value
    }

def get_configuration_value(configuration_path):
    """ Helper function to get a configuration value from a config path """
    if not configuration_path:
        return {}
    try:
        config_key_path = configuration_path.split('.')
        config_name = config_key_path[0]
        config_key_path.pop(0)
        scopes = ScopesTree()
        config = scopes().Configuration[config_name]
        val = config.get_value()
        for key in config_key_path:
            val = val[key]
        return val
    except Exception as e: # pylint: disable=broad-except
        logger.error(e)
        return {}

def parameter_to_field(param):
    """ Helper function to transform Annotation Parameter into the same format as Field """
    return {
        x[0]: {
            "Value": SimpleNamespace(**{"value": x[1]}),
            "Type": SimpleNamespace(**{"value": get_data_type(x[1])})
        }
        for x in param.items()
    }

def get_data_type(data):
    """ Helper function to get data type of a given value (in same format of front-end) """
    predicates_to_value = [
        {"predicate": isinstance(data, str), "value": "string"},
        {"predicate": isinstance(data, int) and not isinstance(
            data, bool), "value": "number"},
        {"predicate": isinstance(data, float), "value": "number"},
        {"predicate": isinstance(data, bool), "value": "boolean"},
        {"predicate": isinstance(data, dict), "value": "object"},
        {"predicate": isinstance(data, list), "value": "array"},
        {"predicate": True, "value": "any"},
    ]
    # return data type
    return [x for x in predicates_to_value if x["predicate"]][0]["value"]
