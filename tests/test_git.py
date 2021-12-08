import unittest   # The test framework
from classes import GitManager, FileSystem, MASTER, SLAVE
from json import loads as json_loads
USER = "Mograbi"


class TestGit(unittest.TestCase):
    slave_manager = GitManager(USER, SLAVE)
    master_manager = GitManager(USER, MASTER)
    # this is a Public repository that will be used for testing
    remote = "https://github.com/Mograbi/test-git"

    def _validate_file(self, manager, filename, version, expect: dict):
        path = manager.get_file(filename, self.remote, version)
        file_json = json_loads(FileSystem.read(path))
        self.assertEqual(sorted(expect.items()), sorted(file_json.items()))

    def test_get(self):
        self._validate_file(self.slave_manager, "file1", "v0.1", json_loads("""
        {
            "filed1": 1,
            "field2": 2,
            "field3": [1, 2]
            }"""))

        self._validate_file(self.slave_manager, "file1", "s0.1", json_loads("""
        {
            "filed1": "side-branch",
            "field2": 2,
            "field3": [1, 2]
            }"""))

        self._validate_file(self.slave_manager, "file1", "7a8757e9fcdc", json_loads("""
        {
            "filed1": 1,
            "field2": 2
            }"""))

        self._validate_file(self.slave_manager, "file1", "afa0d07d", json_loads("""
        {
            "filed1": "master",
            "field2": 2,
            "field3": [1, 2]
            }"""))

    def test_versions(self):
        pass

    def test_commit(self):
        # this would checkout file1 from v0.1
        path = self.slave_manager.get_file("file1", self.remote, "v0.1")
        new_content = json_loads("""
        {
            "filed1": 1,
            "field2": 2,
            "field3": [1, 2],
            "field4": "branch-b"
            }""")
        FileSystem.write(path, new_content)
        commit_hash = None
        try:
            commit_hash = self.slave_manager.commit_file(self.remote,
                                                         "file1.json")
            self.assertTrue(False, "slave manager shouldn't be allowed\
                                    to commit to index")
        except Exception:
            # we should recieve an exception because slave manager are
            # not allowed to commit
            self.assertIsNone(commit_hash)
        path = self.master_manager.get_file("file1", self.remote, "v0.1")
        FileSystem.write(path, new_content)
        commit_hash = self.master_manager.commit_file(self.remote,
                                                      filename="file1.json",
                                                      new_branch="branch-b",
                                                      message="'added field4'")
        FileSystem.write(path, new_content)

        path = self.master_manager.get_file("file1", self.remote, "master")
        FileSystem.write(path, new_content)
        commit_hash_2 = self.master_manager.commit_file(
                                                    self.remote,
                                                    "file1.json",
                                                    new_branch=None,
                                                    base_branch="master",
                                                    message="changed file1")

        self.assertIsNotNone(commit_hash_2)
        # validate the change we wrote
        self._validate_file(self.master_manager,
                            "file1", commit_hash, new_content)
        self._validate_file(self.master_manager,
                            "file1", commit_hash_2, new_content)

    def test_tag(self):
        pass


if __name__ == '__main__':
    unittest.main()
