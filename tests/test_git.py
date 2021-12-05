import unittest   # The test framework
from classes import GitManager, FileSystem, MASTER, SLAVE
from json import loads as json_loads
USER = "Mograbi"


class TestGit(unittest.TestCase):
    slave_manager = GitManager(USER, SLAVE)
    master_manager = GitManager(USER, MASTER)

    def _validate_file(self, manager, filename, remote, version, expect: dict):
        path = manager.get_file(filename, remote, version)
        file_json = json_loads(FileSystem.read(path))
        self.assertEqual(sorted(expect.items()), sorted(file_json.items()))

    def test_get(self):
        remote = "https://github.com/Mograbi/test-git"
        self._validate_file(self.slave_manager, "file1", remote, "v0.1", json_loads("""
        {
            "filed1": 1,
            "field2": 2,
            "field3": [1, 2]
            }"""))

        self._validate_file(self.slave_manager, "file1", remote, "s0.1", json_loads("""
        {
            "filed1": "side-branch",
            "field2": 2,
            "field3": [1, 2]
            }"""))

        self._validate_file(self.slave_manager, "file1", remote, "7a8757e9fcdc", json_loads("""
        {
            "filed1": 1,
            "field2": 2
            }"""))

        self._validate_file(self.slave_manager, "file1", remote, "afa0d07d", json_loads("""
        {
            "filed1": "master",
            "field2": 2,
            "field3": [1, 2]
            }"""))

    def test_versions(self):
        pass

    def test_commit(self):
        pass

    def test_tag(self):
        pass


if __name__ == '__main__':
    unittest.main()
