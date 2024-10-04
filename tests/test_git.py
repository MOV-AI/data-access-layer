import os
import pytest
from json import loads as json_loads
from os.path import join as path_join

from dal.exceptions import (
    NoChangesToCommit,
    TagAlreadyExist,
    VersionDoesNotExist,
    RepositoryDoesNotExist,
    FileDoesNotExist
)
from dal.classes.filesystem import FileSystem
from dal.archive import Archive, BaseArchive
from dal.api.gitapi import GIT_BASE_FOLDER


# ######################## AUX Functions #################################### #
def _validate_file(archive: BaseArchive, remote, filename, version, expect: dict):
    path = archive.get(filename, remote, version)
    file_json = json_loads(path.read_text())
    assert(sorted(expect.items()) == sorted(file_json.items()))


@pytest.fixture(scope="session", autouse=True)
def clean_environment(request):
    used_users = ["TEMP", "TEMP2", "TEMP3", "temp-movai", "TEMP-delete", "TEMP-version"]

    for user in used_users:
        path = path_join(GIT_BASE_FOLDER, user)
        FileSystem.delete(path)
###############################################################################

def should_run_test():
    """
    check if the current environment is run github or not.
    some tests (git related) will be hard to test from inside github because of
    credentials issues when clonning.
    """
    return not (os.environ.get('CI') in ('True', 'true'))

def test_basic():
    global archive
    archive = Archive(user="TEMP")
    assert(archive is not None)


@pytest.mark.parametrize("params, expected_error", [
    (("git@github.com:MOV-AI/DOES_NOT_EXIST.git", "file", "v", json_loads("{}")), RepositoryDoesNotExist),
    (("git@github.com:MOV-AI/ANOTHER_DOES_NOT_EXIST.git", "file", "v", json_loads("{}")), RepositoryDoesNotExist),
    (("https://github.com/Mograbi/test-git", "file1", "vDoesNotExist", json_loads("{}")), VersionDoesNotExist),
    (("https://github.com/Mograbi/test-git", "file2", "v11DoesNotExist", json_loads("{}")), VersionDoesNotExist),
    (("https://github.com/Mograbi/test-git", "doesnotexist.json", "v0.1", json_loads("{}")), FileDoesNotExist),
])
def test_read_errors(params, expected_error):
    if not should_run_test():
        pytest.skip("cannot check this from inside gitub pipeline")
    archive = Archive(user="TEMP")
    with pytest.raises(expected_error):
        _validate_file(archive, *params)


@pytest.mark.parametrize("params", [
    # use tag as a version
    ("https://github.com/Mograbi/test-git", "file1", "v0.1", json_loads("""{
                                                                            "filed1": 1,
                                                                                "field2": 2,
                                                                                "field3": [1, 2]
                                                                        }""")),
    ("https://github.com/Mograbi/test-git", "file1", "s0.1", json_loads("""{
                                                                            "filed1": "side-branch",
                                                                            "field2": 2,
                                                                            "field3": [1, 2]
                                                                        }""")),
    # use a branch as a version
    ("https://github.com/Mograbi/test-git", "file1", "side-branch", json_loads("""{
                                                                                    "filed1": "side-branch",
                                                                                    "field2": 2,
                                                                                    "field3": [1, 2]
                                                                                }""")),
    ("https://github.com/Mograbi/test-git", "file1", "master", json_loads("""{
                                                                                    "filed1": "master",
                                                                                    "field2": 2,
                                                                                    "field3": [1, 2]
                                                                                }""")),
    # use commit hash as a version
    ("https://github.com/Mograbi/test-git", "file2", "b8252bb89646", json_loads("""{
                                                                                    "field1": "master branch",
                                                                                    "field2": 4
                                                                                }"""))
])
def test_read(params):
    if not should_run_test():
        pytest.skip("cannot check this from inside gitub pipeline")
    archive = Archive(user="TEMP")
    _validate_file(archive, *params)


def test_commit_errors():
    if not should_run_test():
        pytest.skip("cannot check this from inside gitub pipeline")
    archive = Archive(user="TEMP2")
    with pytest.raises(NoChangesToCommit):
        archive.commit("file1", "https://github.com/Mograbi/test-git", base_version="master", message="")


def test_commit():
    if not should_run_test():
        pytest.skip("cannot check this from inside gitub pipeline")
    archive = Archive(user="TEMP2")
    path = archive.get("file1", "https://github.com/Mograbi/test-git", "master")
    FileSystem.write(path, json_loads(
                            """{
                                "filed1": "master",
                                "field2": 2,
                                "field3": [1, 2],
                                "new_field": "new"
                            }"""))
    new_commit = archive.commit("file1", "https://github.com/Mograbi/test-git", base_version="master", message="new commit")


def test_revert():
    if not should_run_test():
        pytest.skip("cannot check this from inside gitub pipeline")
    archive = Archive(user="TEMP3")
    path = archive.get("file1", "https://github.com/Mograbi/test-git", "master")
    before_commit = json_loads(path.read_text())

    FileSystem.write(path, json_loads(
                            """{
                                "filed1": "master",
                                "field2": 2,
                                "field3": [1, 2],
                                "new_field": "test_revert"
                            }"""))
    new_commit = archive.commit("file1", "https://github.com/Mograbi/test-git", base_version="master", message="new commit test revert")
    path = archive.get("file1", "https://github.com/Mograbi/test-git", "master")
    after_commit = json_loads(path.read_text())

    assert(sorted(before_commit.items()) != sorted(after_commit.items()))

    path = archive.revert("https://github.com/Mograbi/test-git", "file1", "master")
    assert(sorted(before_commit.items()) == sorted(json_loads(path.read_text()).items()))

    assert(sorted(after_commit.items()) == sorted(json_loads("""{
                                "filed1": "master",
                                "field2": 2,
                                "field3": [1, 2],
                                "new_field": "test_revert"
                            }""").items()))


def test_version_errors():
    if not should_run_test():
        pytest.skip("cannot check this from inside gitub pipeline")
    archive = Archive(user="TEMP-version")
    remote = "https://github.com/Mograbi/test-git"
    with pytest.raises(RepositoryDoesNotExist):
        archive.create_version("git@github.com:Mograbi/doesnotexist", "master", "new_version")
    with pytest.raises(TagAlreadyExist):
        archive.create_version(remote, "master", "v0.1")


def test_version():
    if not should_run_test():
        pytest.skip("cannot check this from inside gitub pipeline")
    archive = Archive(user="TEMP-version")
    remote = "https://github.com/Mograbi/test-git"
    archive.create_version(remote, "master", "new_tag")
    archive.get("file1", remote, "new_tag")
    archive.create_version(remote, "master", "v1.0", message="creating new tag v1.0")


@pytest.mark.parametrize("params, expected_error", [
    (("git@github.com:MOV-AI/DOES_NOT_EXIST.git", "file", "v"), RepositoryDoesNotExist),
    (("git@github.com:MOV-AI/ANOTHER_DOES_NOT_EXIST.git", "file", "v"), RepositoryDoesNotExist),
    (("https://github.com/Mograbi/test-git", "file1", "vDoesNotExist"), VersionDoesNotExist),
    (("https://github.com/Mograbi/test-git", "file2", "v11DoesNotExist"), VersionDoesNotExist),
    (("https://github.com/Mograbi/test-git", "doesnotexist.json", "v0.1"), FileDoesNotExist),
])
def test_delete_errors(params, expected_error):
    if not should_run_test():
        pytest.skip("cannot check this from inside gitub pipeline")
    archive = Archive(user="TEMP")
    with pytest.raises(expected_error):
        archive.delete(*params)


def test_delete():
    if not should_run_test():
        pytest.skip("cannot check this from inside gitub pipeline")
    archive = Archive(user="TEMP-delete")
    remote = "https://github.com/Mograbi/test-git"
    # we remove file1 from master
    archive.delete(remote, "file1", "master")

    with pytest.raises(FileDoesNotExist):
        # when getting file1 from master it will try to get from the HEAD
        # which we already removed that file commit agot
        archive.get("file1", remote, "master")
