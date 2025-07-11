import unittest
import unittest.mock

from dal.movaidb.database import MovaiDB, extract_keys

import unittest
from typing import List, Tuple, Any


DATA_VALID = {
    'Robot': {
        '2dd2cac0bb7b439f8cc923852a19a290': {
            'Status': {
                'active_flow': '',
                'nodes_lchd': [],
                'persistent_nodes_lchd': [],
                'active_states': [],
                'core_lchd': [],
                'locks': [],
                'timestamp': 1750946517.3606594,
                'active_scene': ''
            }
        }
    }
}

SCHEMA = {
    "Robot": {
        "$name": {
            "Label": "str",
            "RobotName": "&name",
            "IP": "ip_add",
            "RobotType": "str",
            "RobotModel": "str",
            "Info": "str",
            "Actions": "list",
            "Notifications": "list",
            "Alerts": "hash",
            "Status": "hash",
            "Parameter": {
                "$name": {
                    "Value": "any",
                    "TTL": "int",
                    "_timestamp": "float"
                }
            }
        }
    }
}

EXPECTED_KEYS: List[Tuple[str, Any, str]] = [
    (
        'Robot:2dd2cac0bb7b439f8cc923852a19a290,Status:',
        {
            'active_flow': '',
            'nodes_lchd': [],
            'persistent_nodes_lchd': [],
            'active_states': [],
            'core_lchd': [],
            'locks': [],
            'timestamp': 1750946517.3606594,
            'active_scene': ''
        },
        'hash'
    )
]



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

    def test_search(self):
        mock_scan_iter = unittest.mock.MagicMock(
            side_effect=[
                [
                    b"SharedDataEntry:ps_group_1,Field:scan_areas,Value:ps_1",
                    b"SharedDataEntry:ps_group_1,Field:scan_point,Value:ps_scan_point",
                    b"SharedDataEntry:ps_group_1,Field:vis_areas,Value:ps_vis_area",
                    b"SharedDataEntry:ps_group_2,Field:scan_areas,Value:ps_2",
                    b"SharedDataEntry:ps_group_2,Field:scan_point,Value:ps_scan_point_2",
                ]
            ]
        )

        def mock_dict_to_keys(_):
            return [
                ("SharedDataEntry:ps_group_1,Field:scan_areas,Value:*", ["ps_1"], "any"),
                ("SharedDataEntry:ps_group_1,Field:scan_point,Value:*", "ps_scan_point", "any"),
            ]

        movaidb = MovaiDB("local")
        # Apply mocks using context managers for better readability and control
        with unittest.mock.patch.object(
            movaidb, "dict_to_keys", new=mock_dict_to_keys
        ), unittest.mock.patch.object(movaidb.db_read, "scan_iter", new=mock_scan_iter):
            # Call the search method
            result = movaidb.search({})  # argument is irrelevant due to mock
            # Check the result
            self.assertEqual(
                result,
                [
                    "SharedDataEntry:ps_group_1,Field:scan_areas,Value:ps_1",
                    "SharedDataEntry:ps_group_1,Field:scan_point,Value:ps_scan_point",
                ],
            )

    def test_exists_by_args(self):
        mock_scan_iter = unittest.mock.MagicMock(
            side_effect=[
                [
                    b"SharedDataEntry:ps_group_1,Field:scan_areas,Value:ps_1",
                    b"SharedDataEntry:ps_group_1,Field:scan_point,Value:ps_scan_point",
                    b"SharedDataEntry:ps_group_1,Field:vis_areas,Value:ps_vis_area",
                    b"SharedDataEntry:ps_group_2,Field:scan_areas,Value:ps_2",
                    b"SharedDataEntry:ps_group_2,Field:scan_point,Value:ps_scan_point_2",
                ]
            ]
        )

        movaidb = MovaiDB("local")
        # Apply mocks using context managers for better readability and control
        with unittest.mock.patch.object(movaidb.db_read, "scan_iter", new=mock_scan_iter):
            # Call the search method
            self.assertTrue(movaidb.exists_by_args("SharedDataEntry", Name="ps_group_1"))


class TestExtractKeys(unittest.TestCase):
    def test_valid_structure(self):
        result = extract_keys(DATA_VALID, SCHEMA)
        self.assertEqual(result, EXPECTED_KEYS)

    def test_missing_key_raises(self):
        bad_data = {
            'Robot': {
                'some_id': {
                    'MissingStatus': {}
                }
            }
        }
        with self.assertRaises(ValueError) as context:
            extract_keys(bad_data, SCHEMA)
        self.assertIn("Unexpected key", str(context.exception))

    def test_reference_key(self):
        data = {
            'Robot': {
                'robot42': {
                    'RobotName': 'robot42'
                }
            }
        }
        expected = [('Robot:robot42,RobotName:robot42', '', '&name')]
        result = extract_keys(data, SCHEMA)
        self.assertEqual(result, expected)