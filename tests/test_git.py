import pytest
from dal.api.gitapi import MasterGitManager, SlaveGitManager
from dal.classes.filesystem.filesystem import FileSystem
from json import loads as json_loads
from dal.classes.exceptions import (
    NoChangesToCommit,
    SlaveManagerCannotChange,
    TagAlreadyExist,
    VersionDoesNotExist
)
USER = "Mograbi"
remote = "https://github.com/Mograbi/test-git"
slave_manager = SlaveGitManager(USER)
master_manager = MasterGitManager(USER)

def _validate_file(manager, filename, version, expect: dict):
    path = manager.get_file(filename, remote, version)
    file_json = json_loads(FileSystem.read(path))
    return sorted(expect.items()) == sorted(file_json.items())

def test_version():
    with pytest.raises(VersionDoesNotExist):
        _validate_file(slave_manager, "file1", "does-not-exist", json_loads("{}"))

def test_get():
    return _validate_file(slave_manager, "file1", "v0.1", json_loads("""
    {
        "filed1": 1,
        "field2": 2,
        "field3": [1, 2]
        }"""))
    '''
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
    '''
