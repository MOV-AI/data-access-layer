import unittest
from ..dal.api.gitapi import MasterGitManager, SlaveGitManager
from ..dal.classes.filesystem.filesystem import FileSystem
from json import loads as json_loads
from ..dal.classes.exceptions import (
    NoChangesToCommit,
    SlaveManagerCannotChange,
    TagAlreadyExist,
    VersionDoesNotExist
)
USER = "Mograbi"


class TestGit(unittest.TestCase):
    """Main UnitTest for testing various git functionality
    """
    slave_manager = SlaveGitManager(USER)
    master_manager = MasterGitManager(USER)
    # this is a Public repository that will be used for testing
    remote = "https://github.com/Mograbi/test-git"

    def __init__(self, methodName: str = ...) -> None:
        # remove previously existing testing environment
        FileSystem.remove_recursively(
            self.slave_manager._get_local_path(self.remote))
        FileSystem.remove_recursively(
            self.master_manager._get_local_path(self.remote))
        super().__init__(methodName=methodName)

    @pytest.mark.skip(reason="no way of currently testing this")
    def _validate_file(self, manager, filename, version, expect: dict):
        path = manager.get_file(filename, self.remote, version)
        file_json = json_loads(FileSystem.read(path))
        self.assertEqual(sorted(expect.items()), sorted(file_json.items()))

    @pytest.mark.skip(reason="no way of currently testing this")
    def test_get(self):
        self.assertRaises(VersionDoesNotExist,
                          self._validate_file,
                          self.slave_manager,
                          "file1", "does-not-exist", json_loads("{}"))
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

    @pytest.mark.skip(reason="no way of currently testing this")
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
        self.assertRaises(SlaveManagerCannotChange,
                          self.slave_manager.commit_file,
                          self.remote,
                          "file1.json")
        path = self.master_manager.get_file("file1", self.remote, "v0.1")
        FileSystem.write(path, new_content)
        self.assertRaises(VersionDoesNotExist,
                          self.master_manager.commit_file,
                          self.remote,
                          filename="file1",
                          new_branch="branch-b",
                          base_branch="does-not-exist")
        commit_hash = self.master_manager.commit_file(self.remote,
                                                      filename="file1.json",
                                                      new_branch="branch-b",
                                                      message="'added field4'")
        self.assertIsNotNone(commit_hash)
        self.assertRaises(NoChangesToCommit,
                          self.master_manager.commit_file,
                          self.remote,
                          filename="file1",
                          new_branch="branch-b")

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

        self.assertRaises(SlaveManagerCannotChange,
                          self.slave_manager.create_file,
                          self.remote,
                          "Node/node1.json",
                          new_content,
                          base_version=None)
        self.master_manager.create_file(self.remote,
                                        "Node/node1.json",
                                        new_content,
                                        base_version=None)
        commit_hash_3 = self.master_manager.commit_file(
                                                    self.remote,
                                                    "Node/node1.json",
                                                    new_branch=None,
                                                    base_branch="master",
                                                    message="added node1")
        self.assertIsNotNone(commit_hash_3)

        self.master_manager.create_file(self.remote,
                                        "Node/node2.json",
                                        new_content,
                                        base_version=None)
        commit_hash_4 = self.master_manager.commit_file(
                                                    self.remote,
                                                    "Node/node2.json",
                                                    new_branch=None,
                                                    base_branch="branch-b",
                                                    message="added node2")
        self.assertIsNotNone(commit_hash_4)

    @pytest.mark.skip(reason="no way of currently testing this")
    def test_tag(self):
        self.assertTrue(
            self.master_manager.create_tag(
                                self.remote, base_version="s0.1",
                                tag="d0.1", message="creating d0.1 tag"))
        self.assertRaises(TagAlreadyExist,
                          self.master_manager.create_tag,
                          self.remote, "s0.1",
                          "d0.1", "creating d0.1 tag")
        self.assertTrue(
            self.master_manager.create_tag(
                                self.remote, base_version="master",
                                tag="v0.2", message="creating v0.2 tag"))


if __name__ == '__main__':
    unittest.main()
