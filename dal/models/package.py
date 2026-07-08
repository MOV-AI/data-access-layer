"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Tiago Teixeira  (tiago.teixeira@mov.ai) - 2020

   Package Model
"""

import hashlib
from typing import Dict, Tuple
from .scopestree import scopes
from dal.scopes.system import System
from .model import Model

from movai_core_shared.logger import Log


logger = Log.get_logger(__name__)


class Package(Model):
    """
    Currently disabled, use deprecated one instead
    """

    # default __init__

    def get_checksum(self, file_name: str) -> str:
        """Get file's checksum"""
        return self.File[file_name].Checksum

    @staticmethod
    def get_file_checksum(file_path: str) -> str:
        """Calculates a file's checksum"""
        csum = hashlib.md5()
        # let it blow
        with open(file_path, "rb") as fd:
            for line in fd:
                csum.update(line)

        return csum.hexdigest()

    def add(self, *args, **kwargs):
        """This shouldn't be needed in the new API"""
        raise NotImplementedError()

    def is_checksum_valid(self, file_name: str, checksum: str) -> bool:
        """Check checksum"""
        return checksum == self.get_checksum(file_name)

    def file_exists(self, file_name: str, path_to: str) -> str:
        """Check existing file against computed checksum"""
        try:
            csum = self.get_file_checksum(path_to)
            if self.is_checksum_valid(file_name, csum):
                return csum
        except FileNotFoundError:
            pass
        return None

    def dump_file(self, file_name: str, path_to: str) -> Tuple[bool, str, str]:
        """Dump a file to storage"""
        file = self.File[file_name]

        csum = self.file_exists(file_name, path_to)

        if csum is None:
            with open(path_to, "wb") as fd:
                contents = file.Value
                try:
                    fd.write(contents.encode())
                except AttributeError:
                    # bytes has no attribute encode
                    fd.write(contents)
            # check checksum again
            csum = self.file_exists(file_name, path_to)
            if csum is None:
                raise RuntimeError("File checksum mismatch")
        return (True, path_to, csum)

    @staticmethod
    def dump(package: str, file_name: str, path_to: str) -> Tuple[bool, str, str]:
        """Dump a file to storage"""
        try:
            return scopes.from_path(package, scope="Package").dump_file(file_name, path_to)
        except KeyError:  # Scope does not exist
            return (False, path_to, None)

    @staticmethod
    def get_or_create(package_name: str) -> Model:
        """Tries to get a package, creates it if doesn't exist"""
        try:
            return scopes.from_path(package_name, scope="Package")
        except KeyError:
            return scopes().create("Package", package_name)

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
            logger.info("PackagesData not found: %s", e)
            return System("PackagesData", new=True, db=db)

    @staticmethod
    def clear_packagedata(db="local"):
        """Remove all package-tracking entries."""
        packages_data = Package.get_packagedata(db=db)
        try:
            packages_data.remove_partial({"Workspaces": "**"})
        except Exception as e:
            logger.warning("Failed to clear package data: %s", e)

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


Model.register_model_class("Package", Package)
