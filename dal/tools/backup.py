"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Tiago Teixeira (tiago.teixeira@mov.ai) - 2020

   Backup a.k.a. Import Export tool
"""
import argparse
import datetime
import os
import re
import sys
from pathlib import Path
import warnings
from typing import List, Optional
import xml.etree.ElementTree as ET

from dal.movaidb import MovaiDB
from dal.scopes.package import Package

from dal.scopes.scope import Scope
from dal.utils.project_metadata import ProjectSource, FilesystemProjectSource
from movai_core_shared.envvars import RAISE_METADATA_VALIDATION_ERRORS
from movai_core_shared.exceptions import ExportException, ImportException, RemoveException
from movai_core_shared.logger import Log

LOGGER = Log.get_logger(__name__)


def test_reachable(redis_url):
    """Helper function to test wether a redis_server is reachable or not
    Args:
        redis_url (string): URL of redis server to test

    Returns:
        bool: True if reachable
    """
    try:
        from redis import Redis

        r = Redis(redis_url, socket_connect_timeout=1)
        return r.ping()
    except Exception as exc:
        print(f"Warning: {exc}")
        return False


class Backup:
    """Base class for Importer and Exporter."""

    SCOPES = [
        "Flow",
        "Node",
        "StateMachine",
        "Callback",
        "GraphicScene",
        "Annotation",
        "Package",
        "Ports",
        "Layout",
        "Robot",
        "System",
        "Configuration",
        "TaskTemplate",
        "Translation",
        "SharedDataTemplate",
        "SharedDataEntry",
        "Alert",
    ]

    def __init__(self, project, debug: bool = False, recursive=True):
        self.recursive = recursive
        self.project_path = os.path.abspath(project) if project else ""

        if debug:
            self.log = print
        else:
            # prints nothing
            self.log = lambda *args, **kwargs: None

        # Connect to Redis
        MovaiDB(db="global")

    @staticmethod
    def parse_manifest(manifest_lines: List[str], all_default=[None]) -> dict:
        """
        Parses manifest lines and returns the declared objects.

        Args:
            manifest_lines (List[str]): Lines of the manifest file.
            all_default: Default value for all objects, applied when '*' is found.

        Returns:
            dict: Parsed objects from the manifest.
        """
        objects = {}

        for line in manifest_lines:
            line = line.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            _type, _name = [part.strip() for part in line.split(":", 1)]
            if not _type or not _name:
                # what?
                continue
            if _type not in objects.keys():
                objects[_type] = []
            if _name != "*":
                objects[_type] += [_name]
                # force it
                continue
            # else, *
            names = all_default
            try:
                all_default.__getattribute__("__call__")
                names = all_default(_type)
            except AttributeError:
                pass
            finally:
                objects[_type] += names
            # endfor line in manifest
        # close manifest
        return objects

    @staticmethod
    def read_manifest(manifest: str, all_default=[None]) -> dict:
        """Reads a manifest file and returns the declared objects.

        Args:
            manifest (str): Path to the manifest file.
            all_default: Default value for all objects, applied when '*' is found.

        """
        # let it blow
        with open(manifest) as manifest_file:
            return Backup.parse_manifest(manifest_file.readlines(), all_default)

    @staticmethod
    def read_manifest_content(manifest_content: str, all_default=[None]) -> dict:
        """Reads a manifest content string and returns the declared objects.

        Args:
            manifest_content (str): Content of the manifest file.
            all_default: Default value for all objects, applied when '*' is found.

        """
        return Backup.parse_manifest(manifest_content.splitlines(), all_default)

    def run(self, objects: dict = {}):
        raise NotImplementedError


class Importer(Backup):
    """Imports project data to the database."""

    # we always skip deleting Package contents
    # because its the only scope that does not reference exact files
    SKIP_SCOPE_DELETE = ["Package"]

    def __init__(
        self,
        project,
        workspace: Optional[str] = None,
        package_version: Optional[str] = None,
        source: ProjectSource = None,
        force: bool = False,
        dry: bool = False,
        clean_old_data: bool = False,
        **kwargs,
    ):
        super().__init__(project, **kwargs)

        self.project = project
        self.project_path = os.path.abspath(project) if project else ""
        self.source = source or FilesystemProjectSource(self.project_path)
        self.import_container = workspace or self._extract_import_container()
        self.import_package_version = package_version or "N/A"

        self.force = force

        self.validate = not force
        self._delete = clean_old_data

        if not self.source.is_dir(""):
            raise ImportException("Project path does not exist")

        self._imported = {}

        self._db = MovaiDB()

    @staticmethod
    def _extract_import_container() -> str:
        """
        Extracts the import container name from the environment variable HOSTNAME.
        """

        hostname = os.getenv("HOSTNAME")
        return hostname if hostname else "unknown"

    def get_objs(self, scope):
        """Get all objects of a given scope.

        For importer, this is always [None].

        """
        return [None]

    def run(self, objects: dict = {}):
        """Imports the objects defined in the manifest."""
        for scope_name in Backup.SCOPES:
            if objects and scope_name not in objects:
                continue

            object_names = objects.get(scope_name)

            if object_names is not None and None in object_names:
                object_names = None

            scope = Scope.get_class(scope_name)

            data = scope.import_metadata(object_names, self.source, self.recursive)

            for name, data, file_path, tracked_names in data:
                scope_name = next(iter(data))

                if self._is_imported(scope_name, name):
                    continue

                # Validate format before importing
                try:
                    scope.validate_format(scope_name, data[scope_name][name], name)
                except ValueError as exc:
                    _msg = f"Failed to import {scope_name}:{name} - {exc}"
                    LOGGER.warning(_msg)
                    if RAISE_METADATA_VALIDATION_ERRORS:
                        raise ImportException(_msg) from exc

                # Import data
                self._import_data(scope_name, name, data, file_path, tracked_names)

    def _is_imported(self, scope, name) -> bool:
        """Wrapper to check if a scope:name pair is already imported."""
        return name in self._imported.get(scope, set())

    def _set_imported(self, scope, name):
        """Wrapper to set a scope:name pair as imported."""
        names = self._imported.setdefault(scope, set())
        if name not in names:
            LOGGER.debug(f"Imported {scope}:{name}")
            names.add(name)

    def _extract_package_version(self, package_path: Path) -> str:
        """
        If a package_path contains a package.xml file,
        extract the version from it.

        Args:
            package_path (Path): Path to the package directory.

        Returns:
            str: The version string if found in the format xx.xx.xx-xx, otherwise "N/A".

        """
        version_file = None

        for path in package_path.rglob("package.xml"):
            if path.is_file():
                version_file = path

        if version_file and version_file.exists():
            tree = ET.parse(version_file)
            root = tree.getroot()
            version_element = root.find("version")
            if version_element is None or version_element.text is None:
                return "N/A"
            build_version_element = root.find("export/build_version")
            if build_version_element is None or build_version_element.text is None:
                return version_element.text

            return f"{version_element.text}-{build_version_element.text}"

        return "N/A"

    def _update_package_tracking(self, scope, name, tracked_names=None):
        """Update package data structure for duplicate detection.

        Tracks which objects belong to which packages by parsing the import path.
        Expected structure: {package_name: {scope: [obj1, obj2, ...]}}

        Args:
            scope (str): The scope of the imported object (e.g., 'Flow', 'Node')
            name (str): The name of the imported object
        """
        try:
            package_name = self.project
            package_version = self.import_package_version or "N/A"
            # Typical MOV.AI structure: project/pkg_name/metadata/Scope/object.json
            path = Path(self.project_path)

            # If package version was not provided by caller, infer it from package.xml.
            if package_version in ("", "N/A"):
                # Check if the current path ends with "metadata"
                if path.name == "metadata":
                    # Parent directory is the package
                    package_name = path.parent.name
                    package_version = self._extract_package_version(path.parent)
                else:
                    # Otherwise, look for a parent with a "metadata" child
                    for parent in [path] + list(path.parents):
                        if (parent / "metadata").exists():
                            package_name = parent.name
                            package_version = self._extract_package_version(parent)
                            break

            tracked_objects = tracked_names if isinstance(tracked_names, list) else [name]
            LOGGER.debug(
                f"Updating package tracking for {scope}:{name} under package '{package_name}' in workspace '{self.import_container}' with version '{package_version}'"
            )
            # Persist only the new delta; merge/dedup logic lives in Package model.
            Package.update_packagedata(
                workspace=self.import_container,
                package_name=package_name,
                new_data={
                    "version": package_version,
                    "import-date": datetime.datetime.now().isoformat(),
                    scope: tracked_objects,
                },
            )

        except Exception as e:
            # Don't fail imports due to tracking issues, just log
            LOGGER.warning(f"Failed to update package tracking for {scope}:{name}: {e}")

    def _import_data(self, scope_name, name, data, path, tracked_names=None):
        """Imports data to the database.

        Args:
            scope (str): Scope of the data.
            name (str): Name of the data.
            data (dict): Data to import.
            path (str): Path of origin of the data.

        """
        LOGGER.debug(f"Importing {scope_name}:{name} from {self.source.display_path(path)}")
        data[scope_name][name]["InstallPath"] = self.source.display_path(path)

        # remove unwanted keys
        if self._delete and scope_name not in self.SKIP_SCOPE_DELETE:
            try:
                del data[scope_name][name]["_schema_version"]
            except KeyError:
                pass
            try:
                del data[scope_name][name]["relations"]
            except KeyError:
                pass
            # delete
            try:
                obj = Scope.get_class(scope_name)(name)
                self._db.delete_by_args(scope_name, Name=obj.name)
            except Exception:
                pass

        try:
            self._db.set(data)
            self._set_imported(scope_name, name)
            # Update package data structure for duplicate detection
            self._update_package_tracking(scope_name, name, tracked_names=tracked_names)
        except Exception as exc:
            _msg = f"Failed to import '{scope_name}:{name}'"
            LOGGER.warning(_msg)
            raise ImportException(_msg) from exc


class Exporter(Backup):
    """Exports projects data from the database."""

    def __init__(self, project, *args, write_files=True, **kwargs):
        super().__init__(project, *args, **kwargs)
        self.write_files = write_files
        # override state
        # 0 -> ask
        # 1 -> override all
        # 2 -> kell all
        self._override = 0

    def get_objs(self, scope):
        """Get all objects of a given scope."""
        return [None]

    def override(self, path):
        if self._override != 0:
            return self._override == 1

        if not os.path.exists(path):
            return True

        choice = (
            input(f"'{path}' already exists, replace it?\n[Y/n/[A]ll/[K]eep all]").strip().upper()
        )

        if not choice:
            # default
            return True

        choice = choice[0]
        if choice not in "YNAK":
            # default, again
            return True

        if choice in "YN":
            # one time choice
            return choice == "Y"
        # else, for ever choice
        self._override = "AK".index(choice) + 1
        return self._override == 1

    def remove_place_holder(self, files: dict) -> dict:
        """Remove placeholder callback files from the provided file dictionary.

        Args:
            files (dict): A dictionary mapping file paths to their contents.

        Returns:
            dict: A new dictionary excluding files whose paths match
            ``Callback/place_holder.*``.
        """
        return {
            key: value
            for key, value in files.items()
            if not re.search(r"Callback/place_holder\.", key)
        }

    def _write_files(self, files: dict):
        """Write files to the project directory, creating parent directories as needed.

        Only writes files that pass the override check.

        Args:
            files (dict): A dictionary mapping relative file paths to their
                string contents.
        """
        project_path = os.path.abspath(self.project_path)

        for path, data in files.items():
            if not self.override(path):
                continue
            file_path = os.path.join(project_path, path)

            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as file:
                file.write(data)

    def run(self, objects: dict = {}):
        """Exports the objects defined in the manifest."""
        ret = {}
        for scope_name in Backup.SCOPES:
            if objects and scope_name not in objects:
                continue

            object_names = objects.get(scope_name)

            scope = Scope.get_class(scope_name)

            if object_names is None and None in object_names:
                object_names = scope.get_all()

            ret.update(scope.export_metadata(object_names, self.recursive))

        ret = self.remove_place_holder(ret)

        # Write files to filesystem for retro compatibility
        if self.write_files:
            self._write_files(ret)

        return ret


class Remover(Backup):
    """Handles the deletion of metadata from the database.

    This class does not support force, nor recursive.

    Attributes:
        force (bool): Force flag to be validated, must be false, still an
            argument for validation.
        dry_run (bool): If a dry run (no actual changes to database) is to be
            performed.
        dry_print (func): Function used during dry run to print actions that
            would be performed.

    """

    def __init__(self, force: bool = False, dry: bool = False, **kwargs):
        """Sets up object for removal.

        Args:
            force (bool): Force flag to be validated.
            dry (bool): Dry run is executed.

        """
        super().__init__("", **kwargs)
        # force is not supported
        self.force = force
        # dry run, print info but does not change db
        self.dry_run = dry
        # list of removed data
        self._removed = {}

        if self.dry_run:
            # override remove_data to not remove data
            self._remove_data = lambda scope, name: self.set_removed(scope, name)
            # remove project root dir from it, plus an extra '/' (+1)
            self.dry_print = lambda *paths: [print(path) for path in paths]
        else:
            self._db = MovaiDB()
            self.dry_print = lambda *paths: None

    def get_objs(self, scope):
        """Get all objects in given a scope.

        In the case of remover, is simply [].

        Args:
            scope: Metadata scope.

        Returns:
            List containing a None.

        """
        return []

    def run(self, objects: dict = {}):
        """Remover main function, removes the defined objects.

        Args:
            objects: Dict with scope names as keys and list of items to be removed as value

        """
        if self.recursive:
            raise RemoveException("Remove only supports individual removal")

        if self.force:
            raise RemoveException("Remove does not support force")

        # iterate over Nodes, Flows, ...
        for scope_name in Backup.SCOPES:
            if scope_name not in objects:
                continue

            object_names = None if None in objects[scope_name] else objects[scope_name]
            self.remove_default(scope_name, object_names)

    def removed(self, scope, name):
        """Wrapper to check if a scope:name pair was already removed.

        Args:
            scope: Metadata scope.
            name: Item name.

        Returns:
            True if it has been removed, False otherwise.

        """
        return scope in self._removed and name in self._removed[scope]

    def set_removed(self, scope, name):
        """Wrapper to set a scope:name pair as removed.

        Args:
            scope: Metadata scope.
            name: Item name.

        """
        if scope not in self._removed:
            self._removed[scope] = []
        if name not in self._removed[scope]:
            self._removed[scope].append(name)

    def _remove_data(self, scope, name):  # pylint: disable=method-hidden
        """Deletes a scope:name pair if existent in the database.

        Args:
            scope: Metadata scope.
            name: Item name.

        """
        try:
            obj = Scope.get_class(scope)(name)
            # exists
            self._db.delete_by_args(scope, Name=obj.name)
            self.log(f"Removed {scope}:{name}")
        except Exception as e:
            error_msg = f"Item {scope}:{name} not present in database ({e})"
            raise RemoveException(error_msg) from e

    def remove_default(self, scope, names):
        """Deletes a series of scope:name pairs from the database.

        Args:
            scope: Metadata scope.
            name: Item name.

        """
        for name in names:
            if self.removed(scope, name):
                continue

            self.dry_print(f"Would remove {scope}:{name}")

            self._remove_data(scope, name)
            self.set_removed(scope, name)


def backup(args) -> int:
    """Main function to handle the backup actions based on provided arguments."""
    project = args.project
    recursive = not args.individual

    redis_write = test_reachable("redis-master")

    if args.action == "import":
        if redis_write:
            tool = Importer(
                project,
                force=args.force,
                dry=args.dry,
                debug=args.debug,
                recursive=recursive,
                clean_old_data=args.clean_old_data,
            )
        else:
            print("Skipping importer...")
            return 0
    elif args.action == "export":
        tool = Exporter(project, debug=args.debug, recursive=recursive)
    elif args.action == "remove":
        if redis_write:
            tool = Remover(
                force=args.force,
                dry=args.dry,
                debug=args.debug,
                recursive=recursive,
            )
            # so the action print is not 'Removed'
        else:
            print("Skipping remover...")
            return 0
        args.action = args.action[:-1]
    else:
        print(f"Unknown action {args.action}")
        return 1

    if args.manifest:
        objects = tool.read_manifest(args.manifest)
    else:
        objects = {}
        if args.type is not None:
            if args.name is None or args.name == "*":
                objects[args.type] = tool.get_objs(args.type)
            else:
                objects[args.type] = [args.name]

    try:
        tool.run(objects)
        print(args.action.capitalize() + "ed")
        return 0
    except ImportException as exc:
        import traceback

        print(traceback.format_exc(), end="", file=sys.stderr)
        print("error importing:", str(exc), file=sys.stderr)
    except ExportException as exc:
        print("error exporting:", str(exc), file=sys.stderr)
    except RemoveException as exc:
        print("error removing:", str(exc), file=sys.stderr)
    except Exception as e:
        import traceback

        print(traceback.format_exc(), end="", file=sys.stderr)
        print("unknown error:", type(e).__qualname__, "-", str(e), file=sys.stderr)

    # not exited before, means exception
    return 1


def main() -> int:
    """Main function to handle command line arguments and execute the backup tool."""
    warnings.warn(
        "The module tools.backup is deprecated, please use mobdata.",
        DeprecationWarning,
    )

    parser = argparse.ArgumentParser(description="Export/Import/Remove Mov.AI Data")
    parser.add_argument(
        "-a",
        "--action",
        help="export, import or remove",
        type=str,
        required=True,
        metavar="",
    )
    parser.add_argument(
        "-m",
        "--manifest",
        help="Manifest with declared objects to export/import/remove. ex.: Flow:Myflow",
        type=str,
        required=False,
        metavar="",
    )
    parser.add_argument(
        "-p",
        "--project",
        help="Folder to export to or import from.",
        type=str,
        required=True,
        metavar="",
    )
    parser.add_argument(
        "-t",
        "--type",
        help="Object type. Options: Flow, StateMachine, Node, Callback, Annotation",
        type=str,
        metavar="",
        default=None,
    )
    parser.add_argument("-n", "--name", help="Object name", type=str, metavar="", default=None)

    parser.add_argument("-r", "--root-path", help="Deprecated", type=str, metavar="", default=None)

    parser.add_argument(
        "-f",
        "--force",
        dest="force",
        action="store_true",
        help="Do not validate newly inserted instances",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        dest="debug",
        action="store_true",
        help="Print progress information",
    )

    parser.add_argument(
        "-d",
        "--dry",
        "--dry-run",
        dest="dry",
        action="store_true",
        help="Don't actually import or remove anything, simply print the file paths",
    )

    parser.add_argument(
        "-i",
        "--individual",
        dest="individual",
        action="store_true",
        help="Only export/import/remove the element, not the dependencies",
    )

    parser.add_argument(
        "-c",
        "--clean",
        dest="clean_old_data",
        action="store_true",
        help="Clean old data, after import",
    )

    parser.set_defaults(force=False, debug=False, dry=False)

    args, _ = parser.parse_known_args()

    ret_code = backup(args)

    return ret_code


if __name__ == "__main__":
    sys.exit(main())
