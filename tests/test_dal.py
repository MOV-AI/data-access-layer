import json
import unittest
from json import loads as json_loads
from api.dal_api import SlaveDAL, MasterDAL
from classes.filesystem import FileSystem
from classes.exceptions import SchemaTypeNotKnown, ValidationError

USER = "Mograbi"
remote = "https://github.com/Mograbi/test-git"


class TestDAL(unittest.TestCase):
    # this is a Public repository that will be used for testing

    def __init__(self, methodName: str = ...) -> None:
        self.slave_dal = SlaveDAL(USER)
        self.master_dal = MasterDAL(USER)
        # remove previously existing testing environment
        FileSystem.remove_recursively(
            self.slave_dal.get_local_path(remote))
        super().__init__(methodName)

    def _validate_file_content(self, dal, filename, version, expect: dict,
                               should_validate=True):
        path = dal.get(filename, remote, version, should_validate)
        file_json = json_loads(FileSystem.read(path))
        self.assertEqual(sorted(expect.items()), sorted(file_json.items()))

    def test_get(self):
        self.assertRaises(SchemaTypeNotKnown,
                          self._validate_file_content,
                          self.slave_dal, "file1", "v0.1", json_loads("{}"))

        self._validate_file_content(self.slave_dal, "file1", "v0.1", json_loads("""
        {
            "filed1": 1,
            "field2": 2,
            "field3": [1, 2]
            }"""),
            should_validate=False)

        self._validate_file_content(self.slave_dal, "file1", "7a8757e9fcdc", json_loads("""
        {
            "filed1": 1,
            "field2": 2
            }"""),
            should_validate=False)

        self._validate_file_content(self.slave_dal, "node1", "f634498ecaf0", json_loads("""
        {
            "Node": {
                "node1": {
                "Info": "this is info",
                "Label": "Node1",
                "LastUpdate": {
                    "date": "20/01/2022",
                    "user": "Mograbi"
                }
                }
            }
            }"""),
            should_validate=True)

    def test_commit(self):
        pass

    def test_pull(self):
        pass

    def test_push(self):
        pass

    def test_diff(self):
        pass

    def test_validate(self):
        node1 = json_loads("""
        {
            "Node": {
                "node1": {
                    "Info": "d",
                    "Label": "d",
                    "LastUpdate": {
                        "date": "sdf",
                        "user": "Mograbi"
                    }
                }
            }
        }
        """)
        with open('/tmp/node1.json', 'w') as f:
            f.write(json.dumps(node1))
        self.slave_dal.validate('/tmp/node1.json')

        node2 = json_loads("""
        {
            "Node": {
                "node1": {
                }
            }
        }
        """)
        with open('/tmp/node2.json', 'w') as f:
            f.write(json.dumps(node2))
        self.assertRaises(
            ValidationError,
            self.slave_dal.validate,
            '/tmp/node2.json'
        )


if __name__ == "__main__":
    unittest.main()
