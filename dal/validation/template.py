"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
from types import SimpleNamespace
from dal.plugins import Resource, ResourceException


class Template:  # pylint: disable=too-few-public-methods
    """
    Loads a config file from json based on a given schema

    Example:

        protocol_config = {
            "name": str,
            "parameters": dict,
        }

        callback_config = {
            "name": str,
            "libs": dict,
            "file": str
        }

        port_config = {
            "name": str,
            "direction": str,
            "protocol": protocol_config,
            "callback": callback_config
        }

        node_config = {
            "logfile": str,
            "name": str,
            "parameters": dict,
            "ports": [port_config]
        }

        c = Template.load("node.json", node_config, "./tests/configs")
    """

    @staticmethod
    def load(uri: str, config: dict):
        """
        Loads a configuration file, validate against config schema
        returns a Template object
        """
        try:
            json = Resource.read_json(uri)
        except ResourceException as e:
            raise ValueError("Invalid uri {}".format(str)) from e

        # Create a new config object from the validated data
        # of the json file against our config schema
        return Template(**Template._validate_and_copy(json, config))

    @staticmethod
    def load_dict(values: dict, config: dict):
        """
        Creates a template from a dictionary
        """
        return Template(**Template._validate_and_copy(values, config))

    @staticmethod
    def _validate_and_copy(values: dict, config: dict):
        """
        Validate against the values against the config schema
        """
        result = {}
        for k, v in values.items():

            # Key of values must exists on the config section, or else skip
            try:
                # T is the type that we will check against the value v
                T = config[k]
            except KeyError:
                continue

            # when a T is a simple python type only checks
            # the type o value v and add it to the result
            # dictionary
            if isinstance(T, type):
                if not isinstance(v, T):
                    raise ValueError("Value of {} is not {}".format(k, T))
                result[k] = v
                continue

            # when T is a dict it means it's a json object with no
            # constrains, any key/value pair can exists
            # simple convert the dict to a SimpleNamespace
            # https://docs.python.org/3/library/types.html#types.SimpleNamespace
            if isinstance(T, dict) and isinstance(v, dict):
                result[k] = SimpleNamespace(
                    **Template._validate_and_copy(v, T))
                continue

            # when T is a list, means we have a list of objects
            if isinstance(T, list):

                # the value in json for this key must also be an array
                if not isinstance(v, list):
                    raise ValueError("Value of {} is not a list".format(k))

                # By architecture definition we can't have multiple elements defining
                # the array, len(T) must be always 1
                if len(T) != 1:
                    raise ValueError(
                        "A array in the config schema must have only one object, {}".format(k))

                # our T to validate the elements of the json list is the
                # element 0 on the list T
                T = T[0]
                l = []
                for e in v:

                    # when a T is a simple python type only checks
                    # the type of element on the json list and add it to the result
                    # and append it to our list
                    if isinstance(T, type):
                        if not isinstance(e, T):
                            raise ValueError(
                                "Value of {} is not {}".format(k, T))
                        list.append(l, e)
                        continue

                    # e must now be a dict, validate the structure and append
                    # the new Template object to our list
                    if isinstance(e, dict) and isinstance(T, dict):
                        list.append(
                            l, Template(**Template._validate_and_copy(e, T)))
                        continue

                    # This should never happen, this means either we did not
                    # covered all the cases, or there is a bad value in the
                    # the config file
                    raise ValueError("Unexpected type in array, {}".format(T))

                result[k] = l
                continue

            # This should never happen, this means either we did not
            # covered all the cases, or there is a bad value in the
            # the config file
            raise ValueError("Unexpected type in configuration, {}".format(T))

        return result

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
