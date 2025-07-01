"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Tiago Teixeira (tiago.teixeira@mov.ai) - 2020

   Backup a.k.a. Import Export tool
"""

import argparse
import hashlib
import json
import os
import pickle
import re
import sys
from importlib import import_module
import warnings

from dal.movaidb import MovaiDB


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


def _from_path(name):
    try:
        from dal.models.scopestree import scopes

        return scopes.extract_reference(name)[2]
    except KeyError:
        # not a path and `scope` wasn't passed
        # we don't care
        return name


_re_config = re.compile(r"^\$\(\s*config\s+([${}a-zA-Z0-9_]+)\.?.*\)$")
_re_envvar = re.compile(r"\$\{?(.+?)\}?$")
_re_place_holder = re.compile(r"(/)?place_holder(?(1)(/|$)|)")


class BackupException(Exception):
    pass


class ImportException(Exception):
    pass


class ExportException(Exception):
    pass


class RemoveException(Exception):
    """Exception used when removing metadata."""

    pass


class Factory:
    CLASSES_CACHE = {}

    @staticmethod
    def get_class(scope):
        """Get scope class."""
        if scope not in Factory.CLASSES_CACHE:
            mod = import_module("dal.scopes")

            try:
                Factory.CLASSES_CACHE[scope] = getattr(mod, scope)
            except AttributeError as exc:
                raise BackupException(f"Scope does not exists {scope}") from exc

        return Factory.CLASSES_CACHE[scope]


class Backup:
    MOVAI_USERSPACE = os.getenv("MOVAI_USERSPACE")
    _ROOT_PATH = f"{MOVAI_USERSPACE}/database"

    SCOPES = [
        "Flow",
        "Node",
        "StateMachine",
        "Callback",
        "GraphicScene",
        "Annotation",
        "Package",
        "Ports",
        "Message",
        "GraphicAsset",
        "Layout",
        "Robot",
        "System",
        "Configuration",
        "TaskTemplate",
        "SharedDataTemplate",
        "SharedDataEntry",
    ]

    def __init__(self, project, debug: bool = False, recursive=True):
        self.project = project
        self.recursive = recursive
        self.project_path = os.path.join(Backup._ROOT_PATH, project)

        if debug:
            self.log = print
        else:
            # prints nothing
            self.log = lambda *args, **kwargs: None

        # Connect to Redis
        MovaiDB(db="global")

    @staticmethod
    def read_manifest(manifest: str, all_default=[None]) -> dict:
        """Reads a manifest file and returns the declared objects.

        Args:
            manifest (str): Path to the manifest file.
            all_default: Default value for all objects, applied when '*' is found.

        """
        objects = {}
        # let it blow
        with open(manifest) as manifest_file:
            for line in manifest_file:
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
                try:
                    all_default.__getattribute__("__call__")
                    names = all_default(_type)
                except AttributeError:
                    names = all_default
                finally:
                    objects[_type] += names
            # endfor line in manifest
        # close manifest
        return objects

    def run(self, objects: dict = {}):
        raise NotImplementedError


class Importer(Backup):
    """Imports project data to the database."""

    def __init__(
        self,
        project,
        force: bool = False,
        dry: bool = False,
        clean_old_data: bool = False,
        **kwargs,
    ):
        super().__init__(project, **kwargs)

        self.force = force
        self.dry_run = dry
        self.validate = not force
        self._delete = clean_old_data

        if not os.path.isdir(self.project_path):
            raise ImportException("Project path does not exist")

        self._imported = {}

        if self.dry_run:
            # override import_data to not import data
            self._import_data = lambda scope, name, _: self.set_imported(scope, name)
            # remove project root dir from it, plus an extra '/' (+1)
            self.dry_print = lambda *paths: [
                print(path[len(self.project_path) + 1 :]) for path in paths
            ]
        else:
            from dal.movaidb.database import MovaiDB

            self._db = MovaiDB()
            self.dry_print = lambda *paths: None

    def get_objs(self, scope):
        """Get all objects of a given scope.

        For importer, this is always [None].

        """
        return [None]

    def run(self, objects: dict = {}):
        """Imports the objects defined in the manifest."""
        if len(objects) == 0:
            # means import all we find
            # so ...
            def should_import(scope):
                return True

            def get_objects(scope):
                return None

        else:

            def should_import(scope):
                return scope in objects

            def get_objects(scope):
                return None if None in objects[scope] else objects[scope]

        for scope_name in Backup.SCOPES:
            if not should_import(scope_name):
                continue

            try:
                importer = self.__getattribute__(f"import_{scope_name.lower()}")

                def args(scope, names):
                    return (names,)

            except AttributeError:
                importer = self.import_default

                def args(scope, names):
                    return (scope, names)

            object_names = get_objects(scope_name)
            importer(*args(scope_name, object_names))

    def imported(self, scope, name) -> bool:
        """Wrapper to check if a scope:name pair is already imported."""
        return scope in self._imported and name in self._imported[scope]

    def set_imported(self, scope, name):
        """Wrapper to set a scope:name pair as imported."""
        if scope not in self._imported:
            self._imported[scope] = []
        if name not in self._imported[scope]:
            self.log(f"Imported {scope}:{name}")
            self._imported[scope].append(name)

    def _list_files(self, scope, extract=None, match=None):
        """Lists files in the given scope."""
        extractor = extract
        if extract is None:

            def extractor(file):
                return file

        matcher = match
        if matcher is None:

            def matcher(file):
                return True

        scope_path = os.path.join(self.project_path, scope)

        try:
            return [
                (extractor(file), os.path.join(scope_path, file))
                for file in os.listdir(scope_path)
                if matcher(file)
            ]
        except FileNotFoundError:
            # "ignore" it
            return []

    def _get_files(self, scope, names, build=None, match=None):
        """Get files from the given scope.

        Raises:
            ImportException: If the scope directory is not found or if the file does not match.

        """
        names = [_from_path(n) for n in names]

        if len(names) == 0:
            return []

        builder = build
        if builder is None:

            def builder(name):
                return name

        matcher = match
        if matcher is None:
            # maybe default to os.path.isfile(file) ?
            def matcher(file):
                return True

        scope_path = os.path.join(self.project_path, scope)
        if not os.path.isdir(scope_path):
            if self.validate:
                raise ImportException(f"{scope} directory not found")
            else:
                print(f"{scope} directory not found")

        files = []
        for name in names:
            file_path = os.path.join(scope_path, builder(name))
            if not matcher(file_path):
                _msg = f"{scope}:{name} not found"
                self.log(_msg)
                if self.validate:
                    raise ImportException(_msg)
                else:
                    print(_msg)
                    continue
            files.append((name, file_path))

        return files

    def get_files(
        self,
        scope,
        names,
        extract=lambda file: os.path.splitext(file)[0],
        build=lambda name: f"{name}.json",
        list_match=lambda file: file.endswith(".json"),
        get_match=os.path.isfile,
    ):
        if names is None:
            return self._list_files(scope, extract, list_match)
        return self._get_files(scope, names, build, get_match)

    def _import_data(self, scope, name, data):
        """Imports data to the database."""
        # remove unwanted keys
        if self._delete:
            try:
                del data[scope][name]["_schema_version"]
            except KeyError:
                pass
            try:
                del data[scope][name]["relations"]
            except KeyError:
                pass
            # delete
            try:
                obj = Factory.get_class(scope)(name)
                self._db.delete_by_args(scope, Name=obj.name)
            except Exception:
                pass
        try:
            self._db.set(data, validate=self.validate)
            self.set_imported(scope, name)
        except Exception:
            _msg = f"Failed to import '{scope}:{name}'"
            if self.validate:
                self.log(_msg)
                raise ImportException(_msg)
            else:
                # force print
                print(_msg)

    def import_default(self, scope, names=None):
        """Default import function.

        Imports the specified names to the database, if names is None (default), imports every file.

        """
        files = self.get_files(scope, names)

        for name, file_path in files:
            if self.imported(scope, name):
                continue

            self.dry_print(file_path)

            try:
                with open(file_path) as file:
                    data = json.load(file)
            except json.JSONDecodeError:
                with open(file_path, "rb") as file:
                    data = pickle.load(file)

            self._import_data(scope, name, data)

    def import_configuration(self, names=None):
        files = self.get_files("Configuration", names)

        for name, file_path in files:
            if self.imported("Configuration", name):
                continue

            yaml_path = re.sub(r"\.json$", r".yaml", file_path)

            self.dry_print(file_path)
            self.dry_print(yaml_path)

            try:
                with open(file_path) as file:
                    data = json.load(file)
            except json.JSONDecodeError:
                with open(file_path, "rb") as file:
                    data = pickle.load(file)

            # add yaml code
            try:
                with open(yaml_path) as file:
                    data["Configuration"][name]["Yaml"] = file.read()
            except:
                # probably file not found
                pass

            self._import_data("Configuration", name, data)

    def import_callback(self, names=None):
        """Imports Callback, similar to import_default but also updates Callback's Code."""
        # default lambdas
        files = self.get_files("Callback", names)

        for name, file_path in files:
            if self.imported("Callback", name):
                continue

            # remove 'json', add 'py'
            code_path = file_path[:-4] + "py"

            # .json and .py
            self.dry_print(file_path, code_path)

            try:
                with open(file_path) as file:
                    data = json.load(file)
            except json.JSONDecodeError:
                with open(file_path, "rb") as file:
                    data = pickle.load(file)
            if os.path.isfile(code_path):
                with open(code_path) as code:
                    data["Callback"][name]["Code"] = code.read()

            self._import_data("Callback", name, data)

    def import_package(self, names=None):
        """Import Package, recursively look for files of the package"""
        dirs = self.get_files(
            "Package",
            names,
            extract=None,
            build=None,
            list_match=None,
            get_match=os.path.isdir,
        )

        for name, dir_path in dirs:
            if self.imported("Package", name):
                continue

            # base
            file_dict = {}
            data = {
                "Package": {
                    name: {
                        # reference
                        "File": file_dict
                    }
                }
            }

            for root, _, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    self.dry_print(file_path)
                    checksum = hashlib.md5()
                    with open(file_path, "rb") as fd:
                        contents = fd.read()
                    checksum.update(contents)

                    try:
                        contents = contents.decode()
                    except UnicodeError:
                        pass

                    file_dict[file_path.replace(dir_path, "", 1)[1:]] = {
                        "Value": contents,
                        "Checksum": checksum.hexdigest(),
                        "FileLabel": file,
                    }

            self._import_data("Package", name, data)

    def import_message(self, names=None):
        files = self.get_files("Message", names)

        for name, file_path in files:
            if self.imported("Message", name):
                continue

            msg_dict = {"Msg": {}, "Srv": {}, "Action": {}}
            data = {"Message": {name: msg_dict}}

            self.dry_print(file_path)

            with open(file_path) as file:
                json_dict = json.load(file)

            messages = [(k, msg) for k in json_dict for msg in json_dict[k]]
            base_path = os.path.join(self.project_path, "Message", name)
            for pack in messages:
                message_path = os.path.join(base_path, pack[1])
                this_dict = {}
                cmp_path = f"{message_path}.compiled"
                src_path = f"{message_path}.source"
                self.dry_print(cmp_path, src_path)
                with open(cmp_path) as fd:
                    this_dict["Compiled"] = fd.read()
                with open(src_path) as fd:
                    this_dict["Source"] = fd.read()
                msg_dict[pack[0]][pack[1]] = this_dict

            # clean it
            for _type in list(msg_dict.keys()):
                if len(msg_dict[_type]) == 0:
                    del msg_dict[_type]

            self._import_data("Message", name, data)

    def import_ports(self, names=None):
        def to_import(ports):
            return ports in names or ports.split("/")[0] in names

        if names is None:

            def to_import(ports):
                return True

        packages = None
        if names is not None:
            packages = []
            for name in names:
                package = name.split("/", 1)[0]
                if package not in packages:
                    packages.append(package)

        files = self.get_files("Ports", packages)

        for package, pkg_path in files:
            with open(pkg_path) as fd:
                pkg_json = json.load(fd)

            self.dry_print(pkg_path)

            for name in pkg_json["Ports"]:
                if self.imported("Ports", name) or not to_import(name):
                    continue

                data = {"Ports": {name: pkg_json["Ports"][name]}}

                # imports dependencies
                self.dependencies_ports(pkg_json["Ports"][name])

                self._import_data("Ports", name, data)

    def import_tasktemplate(self, names=None):
        files = self.get_files("TaskTemplate", names)

        for name, file_path in files:
            if self.imported("TaskTemplate", name):
                continue

            self.dry_print(file_path)

            with open(file_path) as file:
                data = json.load(file)

            # dependencies
            if self.recursive:
                self.dependencies_tasktemplate(data["TaskTemplate"][name])

            self._import_data("TaskTemplate", name, data)

    def import_flow(self, names=None):
        """Imports Flow, similar to import_default but imports dependencies."""
        files = self.get_files("Flow", names)

        for name, file_path in files:
            if self.imported("Flow", name):
                continue

            self.dry_print(file_path)

            with open(file_path) as file:
                data = json.load(file)

            # dependencies
            # nodes
            if self.recursive:
                node_inst_dict = data["Flow"][name].get("NodeInst", {})
                for key in node_inst_dict:
                    template = node_inst_dict[key].get("Template")
                    if template:
                        try:
                            self.import_node([template])
                        except AttributeError:
                            self.import_default("Flow", [template])
                # inner flows
                container_dict = data["Flow"][name].get("Container", {})
                for key in container_dict:
                    contained_flow = container_dict[key].get("ContainerFlow")
                    if contained_flow:
                        try:
                            self.import_flow([contained_flow])
                        except AttributeError:
                            self.import_default("Flow", [contained_flow])

            self._import_data("Flow", name, data)

    def import_node(self, names=None):
        """Imports Node, similar to import_default but imports dependencies."""
        files = self.get_files("Node", names)

        for name, file_path in files:
            if self.imported("Node", name):
                continue

            self.dry_print(file_path)

            with open(file_path) as file:
                data = json.load(file)

            # dependencies
            if self.recursive:
                self.dependencies_node(data["Node"][name])

            self._import_data("Node", name, data)

    def import_shareddataentry(self, names=None):
        files = self.get_files("SharedDataEntry", names)

        for name, file_path in files:
            if self.imported("SharedDataEntry", name):
                continue

            self.dry_print(file_path)

            with open(file_path) as file:
                data = json.load(file)

            # dependencies
            if self.recursive:
                dep = data["SharedDataEntry"][name]["TemplateID"]
                try:
                    self.import_shareddatatemplate([dep])
                except AttributeError:
                    self.import_default("SharedDataTemplate", [dep])

            self._import_data("SharedDataEntry", name, data)

    def import_statemachine(self, names=None):
        # all defaults
        files = self.get_files("StateMachine", names)

        for name, file_path in files:
            if self.imported("StateMachine", name):
                continue

            self.dry_print(file_path)

            with open(file_path) as file:
                data = json.load(file)

            # dependencies
            if self.recursive:
                sm = data["StateMachine"][name]
                for state in sm["State"]:
                    callback = sm["State"][state].get("Callback")
                    if callback and _re_place_holder.search(callback) is None:
                        try:
                            self.import_callback([callback])
                        except AttributeError:
                            self.import_default("Callback", [callback])

            self._import_data("StateMachine", name, data)

    def import_graphicscene(self, names=None):
        # all defaults
        files = self.get_files("GraphicScene", names)

        for name, file_path in files:
            if self.imported("GraphicScene", name):
                continue

            self.log(file_path)

            try:
                with open(file_path) as file:
                    data = json.load(file)
            except (json.JSONDecodeError, UnicodeError):
                with open(file_path, "rb") as file:
                    data = pickle.load(file)

            # dependencies
            if self.recursive:
                scene = data["GraphicScene"][name]
                for asset_type in scene["AssetType"]:
                    for asset in scene["AssetType"][asset_type]:
                        annotations = list(
                            scene["AssetType"][asset_type][asset].get("Annotation", {}).keys()
                        )
                        try:
                            self.import_annotation(annotations)
                        except AttributeError:
                            self.import_default("Annotation", annotations)

            self._import_data("GraphicScene", name, data)

    def dependencies_ports(self, ports: dict):
        if "Package" in ports["Data"]:
            try:
                self.import_message([ports["Data"]["Package"]])
            except AttributeError:
                self.import_default("Message", [ports["Data"]["Package"]])

    def dependencies_tasktemplate(self, tasktemplate: dict):
        # get importers
        try:
            sdt_importer = self.import_shareddatatemplate

            def sdt_args(names):
                return (names,)

        except AttributeError:
            sdt_importer = self.import_default

            def sdt_args(names):
                return ("SharedDataTemplate", names)

        try:
            cb_importer = self.import_callback

            def cb_args(names):
                return (names,)

        except AttributeError:
            cb_importer = self.import_default

            def cb_args(names):
                return ("Callback", names)

        try:
            self.import_flow

            def flow_args(names):
                return (names,)

        except AttributeError:
            self.import_default

            def flow_args(names):
                return ("Flow", names)

        # now, the dependencies
        callbacks = [
            tasktemplate["ScoringFunction"],
            tasktemplate["GenericScoringFunction"],
            tasktemplate["TaskFilter"],
        ]

        shared_data = list(tasktemplate["SharedData"].keys())

        if len(shared_data) > 0:
            sdt_importer(*sdt_args(shared_data))

        # remove place_holder
        callbacks = [c for c in callbacks if _re_place_holder.search(c) is None]
        cb_importer(*cb_args(callbacks))

    def dependencies_node(self, node: dict):
        try:
            sm_importer = self.import_statemachine

            def sm_args(names):
                return (names,)

        except AttributeError:
            sm_importer = self.import_default

            def sm_args(names):
                return ("StateMachine", names)

        try:
            cb_importer = self.import_callback

            def cb_args(names):
                return (names,)

        except AttributeError:
            cb_importer = self.import_default

            def cb_args(names):
                return ("Callback", names)

        try:
            cf_importer = self.import_configuration

            def cf_args(names):
                return (names,)

        except AttributeError:
            cf_importer = self.import_default

            def cf_args(names):
                return ("Configuration", names)

        ports_inst_dict = node.get("PortsInst", {})
        for key in ports_inst_dict:
            ports_inst = ports_inst_dict[key]
            _in = ports_inst.get("In", [])
            for iport in _in:
                callback = _in[iport].get("Callback")
                if callback and _re_place_holder.search(callback) is None:
                    cb_importer(*cb_args([callback]))
                if ports_inst.get("Template") == "MovAI/StateMachine":
                    state_machine = _in[iport].get("Parameter", {}).get("StateMachine")
                    if state_machine:
                        sm_importer(*sm_args([state_machine]))

        # configs
        for param in node.get("Parameter", {}).values():
            value = param.get("Value", None)
            if not isinstance(value, str):
                continue
            m = _re_config.match(value)
            if m is None:
                continue
            conf = m.group(1)
            m = _re_envvar.match(conf)
            if m:
                conf_name = os.getenv(m.group(1), None)
                if conf_name is None:
                    print(f"Could not find value for {m.group(1)}")
                    continue
            else:
                conf_name = conf

            cf_importer(*cf_args([conf_name]))


class Exporter(Backup):
    """Exports projects data from the database."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # create base directory
        if not os.path.exists(self.project_path):
            os.makedirs(self.project_path)

        # avoid multiple exports
        self._exported = {
            # don't export place_holder
            "Callback": ["place_holder"]
        }
        # override state
        # 0 -> ask
        # 1 -> override all
        # 2 -> kell all
        self._override = 0

    def read_manifest(self, manifest):
        return Backup.read_manifest(manifest, self.get_objs)

    def get_objs(self, scope):
        """Get all objects of a given scope."""
        return Factory.get_class(scope).get_all()

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

    def exported(self, scope, name):
        return scope in self._exported and name in self._exported[scope]

    def set_exported(self, scope, name):
        if scope not in self._exported:
            self._exported[scope] = []
        if name not in self._exported[scope]:
            self.log(f"Exported {scope}:{name}")
            self._exported[scope].append(name)

    def run(self, objects: dict = {}):
        """Exports the objects defined in the manifest."""
        if len(objects) == 0:
            raise ExportException("No objects to export")

        for scope_name in Backup.SCOPES:
            if scope_name not in objects:
                # not to export
                continue

            try:
                exporter = self.__getattribute__(f"export_{scope_name.lower()}")

                def args(scope, name):
                    return (name,)

            except AttributeError:
                exporter = self.export_default

                def args(scope, name):
                    return (scope, name)

            for obj_id in objects[scope_name]:
                self.log(f"Exporting {scope_name}:{obj_id}")
                exporter(*args(scope_name, obj_id))

    def export_default(self, scope, name):
        name = _from_path(name)
        if self.exported(scope, name):
            # not exporting again
            return

        path = os.path.join(self.project_path, scope)

        if not os.path.exists(path):
            os.makedirs(path)

        try:
            obj = Factory.get_class(scope)(name)
        except Exception as e:
            raise ExportException(f"Can't find {scope}:{name} - (Exc: {e})")

        json_path = os.path.join(scope, f"{name}.json")
        self.dict2file(obj.get_dict(), json_path)

        self.set_exported(scope, name)

    def export_callback(self, name):
        name = _from_path(name)

        if self.exported("Callback", name):
            return

        Callback = Factory.get_class("Callback")

        self.export_default("Callback", name)
        # didn't blow before, so must exist
        obj = Callback(name)

        code_path = os.path.join(self.project_path, "Callback", f"{name}.py")
        self.code2file(obj.Code, code_path)

    def export_package(self, name):
        name = _from_path(name)
        if self.exported("Package", name):
            return

        Package = Factory.get_class("Package")

        package_path = os.path.join(self.project_path, "Package", name)
        if not os.path.exists(package_path):
            os.makedirs(package_path)

        try:
            package = Package(name)
        except:
            raise ExportException(f"Can't find Package:{name}")

        for key in package.File:
            file_path = os.path.join(package_path, key)
            file_dir = os.path.dirname(file_path)
            if file_dir != "":
                os.makedirs(file_dir, exist_ok=True)
            self.dump2file(package.File[key].Value, file_path)

        self.set_exported("Package", name)

    def export_message(self, name):
        """
        Message/
            <pack_name|obj_id>.json
            <pack_name|obj_id>/
                <Type>(<msg_1>.source
                <Type>/<msg_1>.compiled
                <Type>/<msg_2>.source
                <Type>/<msg_2>.compiled
                ...
            ...
        """

        name = _from_path(name)

        if self.exported("Message", name):
            return

        Message = Factory.get_class("Message")
        try:
            obj = Message(name)
        except:
            raise ExportException(f"Can't find Message:{name}")

        message_path = os.path.join(self.project_path, "Message", name)
        files = [("Msg", k) for k in obj.Msg.keys()]
        files += [("Srv", k) for k in obj.Srv.keys()]
        files += [("Action", k) for k in obj.Action.keys()]

        json_dict = {
            "Msg": list(obj.Msg.keys()),
            "Srv": list(obj.Srv.keys()),
            "Action": list(obj.Action.keys()),
        }
        self.dict2file(json_dict, message_path + ".json")

        for pack in files:
            msg_type_dict = obj.__getattribute__(pack[0])
            msg = msg_type_dict[pack[1]]
            base_path = os.path.join(message_path, pack[1])
            self.dump2file(msg.Source, base_path + ".source")
            self.dump2file(msg.Compiled, base_path + ".compiled")

        self.set_exported("Message", name)

    def export_flow(self, name):
        name = _from_path(name)

        if self.exported("Flow", name):
            return

        Flow = Factory.get_class("Flow")

        try:
            flow = Flow(name)
        except:
            raise ExportException(f"Can't find Flow:{name}")

        # export dependencies
        # nodes
        if self.recursive:
            for node in flow.NodeInst:
                template = flow.NodeInst[node].Template
                if template:
                    try:
                        self.export_node(template)
                    except AttributeError:
                        self.export_default("Node", template)
            # inner flows
            for container in flow.Container:
                inner_flow = flow.Container[container].ContainerFlow
                if inner_flow:
                    try:
                        self.export_flow(inner_flow)
                    except AttributeError:
                        self.export_default("Flow", inner_flow)

        self.export_default("Flow", name)

    def export_tasktemplate(self, name):
        name = _from_path(name)

        if self.exported("TaskTemplate", name):
            return

        TaskTemplate = Factory.get_class("TaskTemplate")

        try:
            tasktemplate = TaskTemplate(name)
        except Exception:
            raise ExportException(f"Can't find TaskTemplate:{name}")

        if self.recursive:
            self.dependencies_tasktemplate(tasktemplate)
        self.export_default("TaskTemplate", name)

    def export_shareddataentry(self, name):
        name = _from_path(name)

        if self.exported("SharedDataEntry", name):
            return

        SharedDataEntry = Factory.get_class("SharedDataEntry")

        try:
            sde = SharedDataEntry(name)
        except Exception:
            raise ExportException(f"Can't find SharedDataEntry:{name}")

        # dependencies
        if self.recursive:
            try:
                self.export_shareddatatemplate(sde.TemplateID)
            except AttributeError:
                self.export_default("SharedDataTemplate", sde.TemplateID)

        self.export_default("SharedDataEntry", name)

    def export_node(self, name):
        name = _from_path(name)

        if self.exported("Node", name):
            return

        Node = Factory.get_class("Node")

        try:
            node = Node(name)
        except Exception:
            raise ExportException(f"Can't find Node:{name}")

        if self.recursive:
            self.dependencies_node(node)

        self.export_default("Node", name)

    def export_statemachine(self, name):
        name = _from_path(name)

        if self.exported("StateMachine", name):
            return

        if self.recursive:
            StateMachine = Factory.get_class("StateMachine")

            try:
                sm = StateMachine(name)
            except:
                raise ExportException(f"Can't find StateMachine:{name}")

            for state in sm.State:
                callback = sm.State[state].Callback
                if callback:
                    try:
                        self.export_callback(callback)
                    except AttributeError:
                        self.export_default("Callback", callback)

        self.export_default("StateMachine", name)

    def export_ports(self, name):
        name = _from_path(name)
        if self.exported("Ports", name):
            return

        Ports = Factory.get_class("Ports")

        try:
            ports = Ports(name)
        except:
            raise ExportException(f"Can't find Ports:{name}")

        if self.recursive:
            if "Package" in ports.Data:
                try:
                    self.export_message(ports.Data["Package"])
                except AttributeError:
                    self.export_default("Message", ports.Data["Package"])

        first_part = name.split("/", 1)[0]

        # read from whatever exists
        ports_path = os.path.join(self.project_path, "Ports", first_part + ".json")
        if os.path.exists(ports_path):
            with open(ports_path) as fd:
                json_dict = json.load(fd)
        else:
            json_dict = {"Ports": {}}

        data = ports.get_dict()
        json_dict["Ports"][name] = data["Ports"][name]

        self.dict2file(json_dict, ports_path)
        self.set_exported("Ports", name)

    def export_graphicscene(self, name):
        name = _from_path(name)
        if self.exported("GraphicScene", name):
            return

        if self.recursive:
            GraphicScene = Factory.get_class("GraphicScene")

            try:
                scene = GraphicScene(name)
            except:
                raise ExportException(f"Can't find GraphicScene:{name}")

            try:
                self.export_package("maps")
            except AttributeError:
                self.export_default("Package", "maps")

            try:
                self.export_package("meshes")
            except AttributeError:
                self.export_default("Package", "meshes")

            try:
                self.export_package("point_clouds")
            except AttributeError:
                self.export_default("Package", "point_clouds")

            for asset_type in scene.AssetType:
                for asset in scene.AssetType[asset_type].AssetName:
                    for key in scene.AssetType[asset_type].AssetName[asset].Annotation:
                        try:
                            self.export_annotation(key)
                        except AttributeError:
                            self.export_default("Annotation", key)

        self.export_default("GraphicScene", name)

    def export_configuration(self, name):
        name = _from_path(name)
        if self.exported("Configuration", name):
            return

        Configuration = Factory.get_class("Configuration")

        try:
            config = Configuration(name)
        except:
            raise ExportException(f"Can't find Configuration:{name}")

        self.export_default("Configuration", name)

        # export yaml as external file
        path = os.path.join(self.project_path, "Configuration", f"{name}.yaml")
        self.code2file(config.Yaml, path)

    def dict2file(self, data, path):
        real_path = os.path.join(self.project_path, path)
        if not self.override(real_path):
            return

        b = data
        for i in range(2):
            b = b[next(iter(b.keys()))]
        try:
            del b["_schema_version"]
        except KeyError:
            pass
        try:
            del b["relations"]
        except KeyError:
            pass
        # remove the code from json, code should only exists in .py
        try:
            del b["Code"]
        except KeyError:
            pass
        # remove the yaml from configuration, yaml should only exists in .yaml
        try:
            del b["Yaml"]
        except KeyError:
            pass
        # the Dummy field is deprecated, to keep compatibility
        # if Dummy is true, it must be replaced with
        # Remappable = false and Launch = false
        try:
            if b["Dummy"] is True:
                b["Remappable"] = False
                b["Launch"] = False

            del b["Dummy"]
        except KeyError:
            pass

        try:
            _data = json.dumps(data, sort_keys=True, indent=4)
            mode = "w+"
        except:
            _data = pickle.dumps(data)
            mode = "wb+"

        os.makedirs(os.path.dirname(real_path), exist_ok=True)
        with open(real_path, mode) as file:
            file.write(_data)

    def ports2file(self, data, path):
        try:
            with open(path) as file:
                current = json.load(file)
        except FileNotFoundError:
            current = {"Ports": {}}

        for obj in data:
            current["Ports"].update(obj["Ports"])

        self.dict2file(current, path)

    def code2file(self, code, path):
        if not self.override(path):
            return

        with open(path, "w+") as file:
            file.write(code)

    def dump2file(self, data, path):
        if not self.override(path):
            return

        mode = "w+"
        if isinstance(data, bytes):
            mode = "wb+"
        real_path = os.path.join(self.project_path, path)
        os.makedirs(os.path.dirname(real_path), exist_ok=True)
        with open(real_path, mode) as file:
            file.write(data)

    def dependencies_tasktemplate(self, tasktemplate):
        try:
            sdt_exporter = self.export_shareddatatemplate

            def sdt_args(names):
                return (names,)

        except AttributeError:
            sdt_exporter = self.export_default

            def sdt_args(names):
                return ("SharedDataTemplate", names)

        try:
            cb_exporter = self.export_callback

            def cb_args(names):
                return (names,)

        except AttributeError:
            cb_exporter = self.export_default

            def cb_args(names):
                return ("Callback", names)

        for key in ("ScoringFunction", "GenericScoringFunction", "TaskFilter"):
            cb_exporter(*cb_args(getattr(tasktemplate, key)))

        for key in tasktemplate.SharedData.keys():
            sdt_exporter(*sdt_args(key))

    def dependencies_node(self, node):
        try:
            sm_exporter = self.export_statemachine

            def sm_args(name):
                return (name,)

        except AttributeError:
            sm_exporter = self.export_default

            def sm_args(name):
                return ("Callback", name)

        try:
            cb_exporter = self.export_callback

            def cb_args(name):
                return (name,)

        except AttributeError:
            cb_exporter = self.export_default

            def cb_args(name):
                return ("StateMachine", name)

        try:
            cf_exporter = self.export_configuration

            def cf_args(name):
                return (name,)

        except AttributeError:
            cf_exporter = self.export_default

            def cf_args(name):
                return ("Configuration", name)

        for portsInst in node.PortsInst:
            port = node.PortsInst[portsInst]
            for iport in port.In:
                callback = port.In[iport].Callback
                if callback:
                    cb_exporter(*cb_args(callback))
                if port.Template == "MovAI/StateMachine":
                    sm = port.In[iport].Parameter["StateMachine"]
                    if sm:
                        sm_exporter(*sm_args(sm))

        # configs
        for param in node.Parameter.values():
            if not isinstance(param.Value, str):
                # not a string
                continue
            m = _re_config.match(param.Value)
            if m is None:
                continue
            conf = m.group(1)
            m = _re_envvar.match(conf)
            if m:
                # TODO getting from envvars will probably be replaced
                # by looking in the robot config
                conf_name = os.getenv(m.group(1), None)
                if conf_name is None:
                    # error, print always
                    print(f"Could not find value for {m.group(1)}")
                    continue
            else:
                conf_name = conf

            cf_exporter(*cf_args(conf_name))


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
            from dal.movaidb.database import MovaiDB

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

    def _remove_data(self, scope, name):
        """Deletes a scope:name pair if existent in the database.

        Args:
            scope: Metadata scope.
            name: Item name.

        """
        try:
            obj = Factory.get_class(scope)(name)
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


def main(args) -> int:
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
            # so the action print is not 'Removeed'
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


if __name__ == "__main__":
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

    ret_code = main(args)

    exit(ret_code)
