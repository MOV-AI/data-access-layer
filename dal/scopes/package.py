"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020

   Module for the Package namespace
"""
import copy
import hashlib
import os

from typing import Dict

from dal.scopes.scope import Scope
from dal.scopes.system import System
from dal.scopes.structures import Struct
from dal.helpers.helpers import Helpers
from movai_core_shared.logger import Log


LOGGER = Log.get_logger("spawner.mov.ai")


class FileStruct(Struct):
    """Helper class to provide callbacks on attributes set"""

    def __init__(self, name, struct_dict, prev_struct, db):
        super().__init__(name=name, struct_dict=struct_dict, prev_struct=prev_struct, db=db)
        self.__dict__["setattr_callback"] = {"Value": self.set_checksum}

    def __setattr__(self, name, value):
        if name in self.attrs:
            self.__dict__[name] = value
            self.movaidb.set(Helpers.join_first({name: value}, self.prev_struct))
            if name in self.__dict__["setattr_callback"]:
                self.setattr_callback[name](name, value)
        elif name in self.lists:
            raise AttributeError(('"%s" is a list not an attribute') % name)
        elif name in self.hashs:
            raise AttributeError(('"%s" is a hash not an attribute') % name)
        else:
            raise AttributeError(('Attribute "%s" does not exist') % name)

    def set_checksum(self, name, value):
        """Callback to calculate and save the checksum"""
        checksum = hashlib.md5()
        if isinstance(value, bytes):
            checksum.update(value)
        else:
            checksum.update(value.encode("utf-8"))
        result = checksum.hexdigest()
        self.__dict__["Checksum"] = result
        self.movaidb.set(Helpers.join_first({"Checksum": result}, self.prev_struct))


class Package(Scope):
    """Package class deals with packages/files uploaded to the db"""

    scope = "Package"

    def __init__(self, name, version="latest", new=False, db="global"):
        super().__init__(scope="Package", name=name, version=version, new=new, db=db)

    def add(self, key, name, **kwargs):  # check if exixts and give error
        new_struct = dict()
        for elem in self.struct_dict[key]:
            # the value in the struct
            new_struct[name] = self.struct_dict[key][elem]

        temp = copy.deepcopy(self.prev_struct)

        if key == "File":
            self.__dict__[key][name] = FileStruct(key, new_struct, temp, self.db)
        else:
            self.__dict__[key][name] = Struct(key, new_struct, temp, self.db)

        for arg_key, arg_value in kwargs.items():
            setattr(self.__dict__[key][name], arg_key, arg_value)

        return self.__dict__[key][name]

    def get_checksum(self, file_name):
        """get the file checksum from the db"""
        return self.File[file_name].Checksum

    def get_file_checksum(self, file_path):
        """Opens a file and calculates the checksum"""
        tst_checksum = hashlib.md5()

        try:
            with open(file_path, "rb") as infile:
                for line in infile:
                    tst_checksum.update(line)
        except Exception:
            pass

        return tst_checksum.hexdigest()

    def is_checksum_valid(self, file_name, checksum):
        """Compares db checksum with file checksum"""
        return checksum == self.get_checksum(file_name)

    def dump_file(self, file_name, path_to):
        """Dump a file from redis. Uses the checksum to validate the dump."""
        file = self.File[file_name]

        # check if file already exists
        dumped_file_checksum = self.file_exists(file_name, path_to)

        if not dumped_file_checksum:
            with open(path_to, "wb") as infile:
                value = file.Value
                if isinstance(value, bytes):
                    infile.write(value)
                else:
                    infile.write(value.encode("utf-8"))
            dumped_file_checksum = self.file_exists(file_name, path_to)
            if not dumped_file_checksum:
                LOGGER.error(f"{file_name} Checksum is not valid")
            return (dumped_file_checksum is not None, path_to, dumped_file_checksum)

        return (True, path_to, dumped_file_checksum)

    def file_exists(self, file_name, path_to):
        """check if file already exists and checksum is valid"""
        if os.path.exists(path_to):
            dumped_file_checksum = self.get_file_checksum(path_to)
            if self.is_checksum_valid(file_name, dumped_file_checksum):
                return dumped_file_checksum
        return None

    @classmethod
    def dump(cls, package, file_name, path_to):
        """Dump redis file to disk"""
        res = (False, path_to, None)
        try:
            pack = Package(package)
            res = pack.dump_file(file_name, path_to)
        except Exception as error:
            LOGGER.error(repr(error))
        return res

    @staticmethod
    def get_or_create(package_name):
        try:
            return Package(package_name)
        except Exception as e:
            return Package(package_name, new=True)

    @staticmethod
    def get_packagedata(db="local") -> System:
        """
        Retrieve package-tracking root System object.

        Args:
            db (str): The database identifier to connect to (default is "local").

        Returns:
            System: Root System object for PackagesData.
        """
        try:
            return System("PackagesData", db=db)
        except Exception as e:
            LOGGER.info("PackagesData not found: %s", e)
            return System("PackagesData", new=True, db=db)

    @staticmethod
    def clear_packagedata(db="local"):
        """Remove all package-tracking entries."""
        packages_data = Package.get_packagedata(db=db)
        try:
            packages_data.remove_partial({"Workspaces": "**"})
        except Exception as e:
            LOGGER.warning("Failed to clear package data: %s", e)

        raw_cache = packages_data.__dict__.get("Workspaces")
        if isinstance(raw_cache, dict):
            raw_cache.clear()

    @staticmethod
    def update_packagedata(workspace: str, package_name: str, new_data: Dict):
        """
        Update the PackagesData value.

        Merges package/scope/object entries into existing data.

        Structure:
            {
                "workspace_name": {
                    "package_name": {
                        "version": "1.0.0-1",
                        "import-date": "2024-06-01T12:00:00Z",
                        "data": {
                            "ScopeName": ["object_a", "object_b"]
                        }
                    }
                }
            }

        Args:
            new_data (Dict): A dictionary containing the new data for the packages.
        """
        # Get or create the root PackagesData
        package_data = Package.get_packagedata(db="local")

        # Check if the workspace exists, if not create it
        if workspace in package_data.Workspaces:
            workspace_data = package_data.Workspaces[workspace]
        else:
            workspace_data = package_data.add("Workspaces", workspace)

        workspace_packages = workspace_data.Packages if hasattr(workspace_data, "Packages") else {}
        if package_name in workspace_packages:
            package_struct = workspace_packages[package_name]
            db_data = package_struct.Value if isinstance(package_struct.Value, dict) else {}
        else:
            package_struct = workspace_data.add("Packages", package_name)
            db_data = {}

        if not isinstance(db_data, dict):
            db_data = {}

        # Preserve scalar metadata fields when provided
        if "version" in new_data and isinstance(new_data["version"], str):
            db_data["version"] = new_data["version"]
        if "import-date" in new_data and isinstance(new_data["import-date"], str):
            db_data["import-date"] = new_data["import-date"]

        # Ensure "data" sub-dict exists for scope lists
        if "data" not in db_data or not isinstance(db_data["data"], dict):
            db_data["data"] = {}

        # Merge scope object lists into "data" sub-dict
        for scope_name, objects in new_data.items():
            if scope_name in ("version", "import-date"):
                continue
            if not isinstance(objects, list):
                continue
            if scope_name not in db_data["data"] or not isinstance(
                db_data["data"][scope_name], list
            ):
                db_data["data"][scope_name] = []
            for obj_name in objects:
                if obj_name not in db_data["data"][scope_name]:
                    db_data["data"][scope_name].append(obj_name)

        package_struct.Value = db_data
