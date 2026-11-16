"""Tests for the Package scope, as Robotics uses it to save maps and point clouds.

The map_save_map callback of the map_saver_movai node (movai_localization) saves each file in a
Package: it gets or creates the package, adds the file, then sets the file's Value and FileLabel.
A 2D map is a PNG (bytes) and a YAML (text) in package "maps"; point clouds are PCD files (bytes)
in package "point_clouds".

These tests make the same calls with 150 MB of random bytes, the size of the largest point cloud
found so far, in place of a PNG or PCD file, and check the Redis keys the class creates.
Run them with -rP to see how long the large file takes to write and read.
"""
import hashlib
import os
import pickle
import time
from contextlib import contextmanager

import pytest

MB = 1024 * 1024
# the largest point cloud found so far
LARGE_FILE_SIZE = 150 * MB

PACKAGE = "test_package_maps"
MAP_NAME = "test_map"
PNG = f"{MAP_NAME}.png"
YAML = f"{MAP_NAME}.yaml"
# the YAML map_save_map writes next to the PNG
MAP_YAML = f"""image: {PNG}
resolution: 0.050000
origin: [-10.000000, -10.000000, 0.000000]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
"""


def save_map(png, yaml=MAP_YAML):
    """Save a 2D map in the test package with the calls map_save_map makes.

    Args:
        png (bytes): Content of the map image.
        yaml (str): Content of the map YAML.
    """
    from movai_core_shared.exceptions import DoesNotExist
    from dal.scopes.package import Package

    try:
        package = Package(PACKAGE)
    except DoesNotExist:
        package = Package(PACKAGE, new=True)

    file = package.add("File", PNG)
    file.Value = png
    file.FileLabel = MAP_NAME

    file = package.add("File", YAML)
    file.Value = yaml
    file.FileLabel = MAP_NAME


def file_keys(file_name):
    """Redis key of each attribute of a file of the test package."""
    return {
        attribute: f"Package:{PACKAGE},File:{file_name},{attribute}:"
        for attribute in ("Value", "Checksum", "FileLabel")
    }


def package_keys(redis_db):
    """Redis keys of the test package."""
    return {key.decode() for key in redis_db.scan_iter(match=f"Package:{PACKAGE},*")}


def stored_value(redis_db, key):
    """Value of a Redis key, unpickled like MovaiDB does."""
    return pickle.loads(redis_db.get(key))


def md5(value):
    """MD5 of a value, like the checksum Package saves."""
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.md5(value).hexdigest()


def delete_package(redis_db):
    """Delete the keys of the test package."""
    keys = list(redis_db.scan_iter(match=f"Package:{PACKAGE},*"))
    if keys:
        redis_db.delete(*keys)


@contextmanager
def timed(action):
    """Print how long an action takes."""
    start = time.perf_counter()
    yield
    print(f"{action} took {time.perf_counter() - start:.2f} s")


@pytest.fixture(scope="module")
def large_file():
    """150 MB of random bytes, in place of a PNG or PCD file."""
    return os.urandom(LARGE_FILE_SIZE)


@pytest.fixture
def redis_db(global_db):
    """Client of the Redis database packages are saved in, without the test package."""
    delete_package(global_db.db_write)
    yield global_db.db_write
    delete_package(global_db.db_write)


@pytest.fixture
def redis_full(redis_db):
    """Lower Redis maxmemory so that the large file does not fit, then restore it.

    MovaiDB.validate_file_write refuses a file when its size plus REDIS_WRITE_BUFFER (64 MB) is
    more than maxmemory minus the memory in use. This leaves room for the buffer and half of the
    file, so the test does not need to fill the 1 GB of the test Redis.

    The eviction policy is set to noeviction, like the Redis of EE, so that if the file is ever
    written, Redis refuses the next writes instead of evicting the keys of other tests.
    """
    from dal.movaidb.database import REDIS_WRITE_BUFFER

    maxmemory = redis_db.config_get("maxmemory")["maxmemory"]
    policy = redis_db.config_get("maxmemory-policy")["maxmemory-policy"]
    used_memory = redis_db.info("memory")["used_memory"]
    redis_db.config_set("maxmemory-policy", "noeviction")
    redis_db.config_set("maxmemory", used_memory + REDIS_WRITE_BUFFER + LARGE_FILE_SIZE // 2)
    yield
    redis_db.config_set("maxmemory", maxmemory)
    redis_db.config_set("maxmemory-policy", policy)


class TestPackage:
    def test_new_package(self, redis_db):
        """A new package does not open until a file value is set, and new=True creates it."""
        from movai_core_shared.exceptions import AlreadyExist, DoesNotExist
        from dal.scopes.package import Package

        with pytest.raises(DoesNotExist):
            Package(PACKAGE)

        file = Package(PACKAGE, new=True).add("File", YAML)
        # creating the package and adding a file write nothing to Redis
        assert package_keys(redis_db) == set()
        with pytest.raises(DoesNotExist):
            Package(PACKAGE)

        file.Value = MAP_YAML
        Package(PACKAGE)
        with pytest.raises(AlreadyExist):
            Package(PACKAGE, new=True)

    def test_save_map(self, redis_db, large_file):
        """Each file of a saved map has a Value, Checksum and FileLabel key, and nothing else."""
        with timed(f"Saving a map with a {LARGE_FILE_SIZE // MB} MB PNG"):
            save_map(large_file)

        png_keys = file_keys(PNG)
        yaml_keys = file_keys(YAML)
        assert package_keys(redis_db) == {*png_keys.values(), *yaml_keys.values()}

        # values are pickled, so bytes stay bytes and text stays str
        assert stored_value(redis_db, png_keys["Value"]) == large_file
        assert stored_value(redis_db, png_keys["Checksum"]) == md5(large_file)
        assert stored_value(redis_db, png_keys["FileLabel"]) == MAP_NAME
        assert stored_value(redis_db, yaml_keys["Value"]) == MAP_YAML
        assert stored_value(redis_db, yaml_keys["Checksum"]) == md5(MAP_YAML)
        assert stored_value(redis_db, yaml_keys["FileLabel"]) == MAP_NAME

    def test_save_map_again(self, redis_db, large_file):
        """Saving a map again replaces the values and checksums of its files."""
        save_map(large_file)
        new_png = os.urandom(MB)
        new_yaml = MAP_YAML.replace("resolution: 0.050000", "resolution: 0.100000")
        save_map(new_png, new_yaml)

        png_keys = file_keys(PNG)
        yaml_keys = file_keys(YAML)
        assert package_keys(redis_db) == {*png_keys.values(), *yaml_keys.values()}
        assert stored_value(redis_db, png_keys["Value"]) == new_png
        assert stored_value(redis_db, png_keys["Checksum"]) == md5(new_png)
        assert stored_value(redis_db, yaml_keys["Value"]) == new_yaml
        assert stored_value(redis_db, yaml_keys["Checksum"]) == md5(new_yaml)

    def test_read_back(self, redis_db, large_file, tmp_path):
        """The files of a saved map read back unchanged through the Package class."""
        from dal.scopes.package import Package

        save_map(large_file)
        checksum = md5(large_file)
        package = Package(PACKAGE)

        with timed(f"Reading a {LARGE_FILE_SIZE // MB} MB file"):
            value = package.File[PNG].Value
        assert value == large_file
        assert package.File[PNG].FileLabel == MAP_NAME
        assert package.File[YAML].Value == MAP_YAML
        assert package.get_checksum(PNG) == checksum
        assert package.is_checksum_valid(PNG, checksum)

        path = str(tmp_path / PNG)
        with timed(f"Dumping a {LARGE_FILE_SIZE // MB} MB file to disk"):
            result = Package.dump(PACKAGE, PNG, path)
        assert result == (True, path, checksum)
        with open(path, "rb") as dumped:
            assert dumped.read() == large_file

    def test_file_too_large(self, redis_db, large_file, redis_full):
        """A file that does not fit in Redis's free memory raises an error and writes no keys."""
        from dal.scopes.package import Package

        file = Package(PACKAGE, new=True).add("File", PNG)
        with pytest.raises(Exception, match="Cannot write key"):
            file.Value = large_file

        assert package_keys(redis_db) == set()
