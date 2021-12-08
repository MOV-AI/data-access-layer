import unittest

from git import exc   # The test framework
from classes import MasterGitManager, SlaveGitManager, FileSystem
from json import loads as json_loads

from classes.exceptions import BranchAlreadyExist, GitException, SlaveManagerCannotChange, TagAlreadyExist, VersionDoesNotExist
USER = "Mograbi"


class TestGit(unittest.TestCase):
    slave_manager = SlaveGitManager(USER)
    master_manager = MasterGitManager(USER)
    # this is a Public repository that will be used for testing
    remote = "https://github.com/Mograbi/test-git"

    def _validate_file(self, manager, filename, version, expect: dict):
        path = manager.get_file(filename, self.remote, version)
        file_json = json_loads(FileSystem.read(path))
        self.assertEqual(sorted(expect.items()), sorted(file_json.items()))

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
        except SlaveManagerCannotChange:
            # we should recieve an exception because slave manager are
            # not allowed to commit
            self.assertIsNone(commit_hash)
        path = self.master_manager.get_file("file1", self.remote, "v0.1")
        FileSystem.write(path, new_content)
        commit_hash = self.master_manager.commit_file(self.remote,
                                                      filename="file1.json",
                                                      new_branch="branch-b",
                                                      message="'added field4'")
        try:
            self.master_manager.commit_file(self.remote,
                                            filename="file1",
                                            new_branch="branch-b")
            self.assertFalse(True, "should through exception \
                                    BranchAlreadyExist")
        except GitException:
            # we have 2 possible errors here, no changes to commit and
            # branch already exist.
            pass

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
