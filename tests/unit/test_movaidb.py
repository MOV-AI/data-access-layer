import unittest

from dal.movaidb.database import MovaiDB


class TestMovaiDB(unittest.TestCase):
    def test_args_to_dict(self):
        repl = {"Name": "ps_group_1", "SharedDataEntry": "ps_group_1"}

        # basic_case
        source_dict = {
            "SharedDataEntry": {
                "*": {
                    "Label": "*",
                    "Description": "*",
                    "LastUpdate": "*",
                    "Version": "*",
                    "TemplateID": "*",
                    "Field": {"*": {"Value": "*"}},
                }
            }
        }
        expected_output = {
            "SharedDataEntry": {
                "ps_group_1": {
                    "Label": "*",
                    "Description": "*",
                    "LastUpdate": "*",
                    "Version": "*",
                    "TemplateID": "*",
                    "Field": {"*": {"Value": "*"}},
                }
            }
        }

        self.assertEqual(MovaiDB.args_to_dict(source_dict, repl), expected_output)

        # no_replacements
        source_dict = {"x": 1, "y": {"z": 2}}
        expected_output = {"x": 1, "y": {"z": 2}}
        self.assertEqual(MovaiDB.args_to_dict(source_dict, repl), expected_output)

        # empty_dict
        source_dict = {}
        expected_output = {}
        self.assertEqual(MovaiDB.args_to_dict(source_dict, repl), expected_output)

    def test_validate(self):
        data = {"Value": ["ps_vis_area"]}
        api = {"Value": "any"}
        base_key = "SharedDataEntry:ps_group_1,Field:vis_areas,"
        keys = [
            ("SharedDataEntry:ps_group_1,Field:scan_areas,Value:", ["ps_1"], "any"),
            ("SharedDataEntry:ps_group_1,Field:scan_point,Value:", "ps_scan_point", "any"),
        ]

        expected_result = [
            ("SharedDataEntry:ps_group_1,Field:scan_areas,Value:", ["ps_1"], "any"),
            ("SharedDataEntry:ps_group_1,Field:scan_point,Value:", "ps_scan_point", "any"),
            ("SharedDataEntry:ps_group_1,Field:vis_areas,Value:", ["ps_vis_area"], "any"),
        ]
        MovaiDB.validate(data, api, base_key, keys)
        self.assertEqual(keys, expected_result)

    def test_keys_to_dict(self):
        kv = [("Robot:f488dd196a8c441c97a227a315048fc7,RobotName:241_107", "")]
        expected_output = {"Robot": {"f488dd196a8c441c97a227a315048fc7": {"RobotName": "241_107"}}}
        self.assertEqual(MovaiDB.keys_to_dict(kv), expected_output)

    def test_dict_to_keys(self):
        _input = {"Var": {"context": {"ID": {"TID": {"Parameter": "msg"}}}}}
        expected_output = [("Var:context,ID:TID,Parameter:", "msg", "hash")]
        self.assertEqual(MovaiDB("local").dict_to_keys(_input), expected_output)

    def test_generate_search_wild_key(self):
        _input = {"Package": {"mov-fe-app-ide": {"File": "*"}}}
        self.assertEqual(
            MovaiDB.generate_search_wild_key(_input, only_pattern=False),
            "Package:mov-fe-app-ide,File*",
        )
