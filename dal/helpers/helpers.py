"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020
"""
import copy


class Helpers:
    """Helper Methods"""

    @staticmethod
    def get_partial_dict(_input: dict, key: dict) -> dict:
        """Giving a full dict and a beggining return the full dict containing that beggining"""
        partial_dict = {}

        def iterate(_input, key, partial):
            for key, v2 in key.items():
                v1 = _input.get(key, {})
                if isinstance(v2, dict):
                    partial.update({key: {}})
                    iterate(v1, v2, partial[key])
                else:
                    partial.update({key: v1})

        iterate(_input, key, partial_dict)
        return partial_dict

    @staticmethod
    def update_dict(_base_dict: dict, _add_dict: dict) -> dict:
        """Join a dictionary with another dictionary"""
        base_dict = copy.deepcopy(_base_dict)
        add_dict = copy.deepcopy(_add_dict)

        def update(base_dict):
            for key, value in base_dict.items():
                if isinstance(value, dict):
                    update(value)
                else:
                    base_dict[key] = add_dict

        if base_dict == {}:
            return add_dict
        if add_dict == {}:
            return base_dict

        update(base_dict)
        return base_dict

    @staticmethod
    def get_args(prev_struct) -> dict:
        tmp_truct = copy.deepcopy(prev_struct)
        args = {}

        def iterate(struct, key=None):
            for s_key, s_value in struct.items():
                if key:
                    args[key] = s_key
                    key = None
                else:
                    key = s_key
                if isinstance(s_value, dict):
                    iterate(s_value, key)
        iterate(tmp_truct)
        return args

    @staticmethod
    def join_first(add_struct: dict, prev_struct: dict) -> dict:
        return Helpers.update_dict(prev_struct, add_struct)

    @staticmethod
    def replace_dict_values(haystack: dict, needle: any, value: any) -> None:
        for (k, v) in haystack.items():
            if isinstance(v, dict):
                Helpers.replace_dict_values(v, needle, value)
            elif v == needle:
                haystack[k] = value

    @staticmethod
    def find_by_key(data, target):
        for k, v in data.items():
            if k == target:
                yield data
            elif isinstance(v, dict):
                for result in Helpers.find_by_key(v, target):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    if isinstance(d, dict):
                        for result in Helpers.find_by_key(d, target):
                            yield result
