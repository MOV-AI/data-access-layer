"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
import os
import json
import glob
import uuid
import re
import base64
import tempfile
from urllib.parse import urlparse
from binascii import Error as BinasciiError
from datetime import datetime
from movai.core import Log
from ...plugin import Plugin
from DAL.dataaccesslayer.dal.data import (schemas, PersistencePlugin, TreeNode, SchemaPropertyNode,
                                          Persistence, ScopeInstanceVersionNode, ScopesTree)
from movai.models import Model
from movai.remote import RemoteArchive
from DAL.dataaccesslayer.dal.backup import RestoreManager


__DRIVER_NAME__ = "Mov.ai Filesystem Plugin"
__DRIVER_VERSION__ = "0.0.1"


class FilesystemPlugin(PersistencePlugin):
    """
    Implements a workspace that stores in a local storage
    """
    # Probably this should go to another place
    _ROOT_PATH = os.path.join(os.getenv('MOVAI_USERSPACE', ""), "database")
    _ARCHIVE_URI = os.getenv('MOVAI_MANAGER_URI', "http://localhost:5004")
    _FLEET_TOKEN = os.getenv('FLEET_TOKEN', None)
    _ARCHIVE_USER = None
    _ARCHIVE_PASSWORD = None
    logger = Log.get_logger("filesystem.mov.ai")

    @staticmethod
    def parse_fleet_token():
        """
        Parse the fleet token to get the archive credentials, thee
        credentials are stored in a env var called FLEET_TOKEN
        as a base64 encoded string with the following format
        <user>:<password>
        """
        # Check if we have already parsed the credentials
        if None not in (FilesystemPlugin._ARCHIVE_USER, FilesystemPlugin._ARCHIVE_PASSWORD):
            return

        # The credentials are base64 encoded so we decode it
        try:
            token_bytes = FilesystemPlugin._FLEET_TOKEN.encode('ascii')
            base64_bytes = base64.b64decode(token_bytes)
            token_decoded = base64_bytes.decode('ascii')
        except BinasciiError as e:
            raise ValueError("Invalid Fleet token") from e

        # Split the result to get User and Password
        tokens = token_decoded.split(':')

        try:
            FilesystemPlugin._ARCHIVE_USER = tokens[0]
            FilesystemPlugin._ARCHIVE_PASSWORD = tokens[1]
        except IndexError as e:
            raise ValueError("Invalid Fleet token") from e

    @staticmethod
    def get_scope_from_upstream(scope: str):
        """
        Get a scope from an upstream server, this function is called
        everytime a scope does not exists in the local archive
        it is basicly a wrapper aroung the RemoteArchive client
        and the RestoreManager class, it uses them to fetch a full
        backup of dependencies from a remote archive and restore
        it on the local archive
        """
        url = urlparse(FilesystemPlugin._ARCHIVE_URI)

        # We only accept http/https urls for the manager
        if url.scheme not in ("http", "https"):
            raise ValueError("Invalid Manager Url")

        # If the URL is pointed to the localhost it means we are the
        # the manager, there is no place to look up to
        if url.hostname in ("localhost", "127.0.0.1"):
            raise FileNotFoundError

        # Parse the fleet token from environment variable
        try:
            FilesystemPlugin.parse_fleet_token()
        except ValueError as e:
            raise FileNotFoundError from e

        # We use the RemoteArchive to download a backup
        # with the scope and all the dependencies
        # from a remote archive, then we use RestoreManager to
        # run a restore Job
        with tempfile.TemporaryDirectory() as tempdir:

            FilesystemPlugin.logger.info(
                "Requesting scope (%s) from manager (%s)", scope, FilesystemPlugin._ARCHIVE_URI)

            target_file = os.path.join(str(tempdir), "backup.zip")

            # Uses RemoteArchive to Fetch scopes and dependencies
            # from the remote archive
            client = RemoteArchive(FilesystemPlugin._ARCHIVE_URI,
                                   FilesystemPlugin._ARCHIVE_USER, FilesystemPlugin._ARCHIVE_PASSWORD)

            # Something went wrong, probably we do not have the scope
            if not client.backup([scope], target_file):
                FilesystemPlugin.logger.error(
                    "Error downloading scope (%s) and dependencies from the manager (%s)", scope, FilesystemPlugin._ARCHIVE_URI)
                raise FileNotFoundError

            FilesystemPlugin.logger.info(
                "scope (%s) and dependencies retrieced from the manager (%s)", scope, FilesystemPlugin._ARCHIVE_URI)

            # We now restore the retrieved archive
            try:
                job_id = RestoreManager.create_job(target_file)
                RestoreManager.start_job(job_id)
            except ValueError as e:
                raise FileNotFoundError from e

    def validate_data(self, schema: TreeNode, data: dict, out: dict):
        """
        Validate a dict against a schema
        """
        try:
            # if we are on a property node, store it on the database
            if isinstance(schema, SchemaPropertyNode):
                out[schema.name] = data[schema.name]
                return

            # it's not a terminal element, compose the next
            # base key and process this node children
            out[schema.name] = {}

            if schema.attributes.get("is_hash", True):
                for name in data[schema.name].keys():
                    out[schema.name][name] = {}
                    for child in schema.children:
                        self.validate_data(
                            child, data[schema.name][name], out[schema.name][name])
                return

            for child in schema.children:
                self.validate_data(child, data[schema.name], out[schema.name])

        except (KeyError, AttributeError):

            # No schema! check in this node children if any
            for child in schema.children:
                self.validate_data(child, data, out)

    @Plugin.plugin_name.getter
    def plugin_name(self):
        """
        Get current plugin class
        """
        return __DRIVER_NAME__

    @Plugin.plugin_version.getter
    def plugin_version(self):
        """
        Get current plugin class
        """
        return __DRIVER_VERSION__

    @PersistencePlugin.versioning.getter
    def versioning(self):
        """
        returns if this plugin supports versioning
        """
        return True

    def create_workspace(self, ref: str, **kwargs):
        """
        creates a new workspace
        """
        workspace = os.path.join(FilesystemPlugin._ROOT_PATH, ref)
        if not os.path.exists(workspace):
            os.mkdir(workspace)

    def workspace_info(self, ref: str):
        """
        get information about a workspace
        """
        return {
            "label": ref,
            "url": f"/{ref}"
        }

    def delete_workspace(self, ref: str):
        """
        deletes a existing workspace
        """
        raise NotImplementedError

    def list_workspaces(self):
        """
        list available workspaces
        """
        pattern = os.path.join(FilesystemPlugin._ROOT_PATH, "*")

        workspaces = []
        for folder in glob.glob(pattern):
            if not os.path.isdir(folder):
                continue
            workspace = folder.replace(FilesystemPlugin._ROOT_PATH, '')
            workspaces.append(workspace[1:])

        return workspaces

    def list_scopes(self, **kwargs):
        """
        list all existing scopes
        """
        try:
            scope = kwargs.get("scope", "*")
            workspace = kwargs.get(
                "workspace", self._args["workspace"])
        except KeyError as e:
            raise ValueError("missing workspace") from e

        pattern = os.path.join(FilesystemPlugin._ROOT_PATH,
                               workspace, scope, "*")
        scopes = []
        for folder in glob.glob(pattern):

            tokens = os.path.split(folder)
            try:
                folder = tokens[0]
                ref = tokens[1]
            except IndexError:
                continue

            tokens = os.path.split(folder)
            try:
                folder = tokens[0]
                scope = tokens[1]
            except IndexError:
                continue

            scopes.append({
                "url": f"{workspace}/{scope}/{ref}", #folder.replace(FilesystemPlugin._ROOT_PATH, ""),
                "scope": scope,
                "ref": ref
            })

        return scopes

    def get_scope_info(self, **kwargs):
        """
        get the information of a scope
        """
        raise NotImplementedError

    def backup(self, **kwargs):
        """
        archive a scope/scopes into a zip file
        """
        try:
            scope = kwargs["scope"]
            ref = kwargs["ref"]
            version = kwargs["version"]
            workspace = kwargs.get(
                "workspace", self._args["workspace"])
            archive = kwargs["archive"]
        except KeyError as e:
            raise KeyError("missing scope, ref, version or archive") from e

        # base path for the scope we are trying to backup
        basepath = os.path.join(
            FilesystemPlugin._ROOT_PATH, workspace, scope, ref)

        # If we did not have to store the files on the filesystem using the
        # stupid pattern <tag>-<epoch>-<uuid> as proposed by Limor
        # this process would be much easier

        # First time we just check if we have any scope with that version in
        # our archive, otherwise we try to fetch it from a remote archive
        try:
            data_folder = glob.glob(os.path.join(basepath, f"{version}-*"))[0]
        except IndexError:
            # try and fetch the scope from a remote archive
            FilesystemPlugin.get_scope_from_upstream(
                os.path.join(workspace, scope, ref, version))

        # if still not there
        try:
            data_folder = glob.glob(os.path.join(basepath, f"{version}-*"))[0]
        except IndexError as e:
            raise FileNotFoundError from e

        # Read the data and the stored relations
        try:
            data_filename = os.path.join(data_folder, "data.json")
            relations_filename = os.path.join(data_folder, "relations.json")
            with open(data_filename, 'r') as data_fp:
                data = data_fp.read()
            with open(relations_filename, 'r') as relations_fp:
                relations = json.load(relations_fp)
        except FileNotFoundError as e:
            raise FileNotFoundError from e

        # Write files in the zip archive
        archive.writestr(data_filename.replace(
            FilesystemPlugin._ROOT_PATH+"/", ""), data)
        archive.writestr(relations_filename.replace(
            FilesystemPlugin._ROOT_PATH+"/", ""), json.dumps(relations))

    def restore(self, **kwargs):
        """
        restore a scope/scopes from a zip file
        """
        try:
            scope = kwargs["scope"]
            ref = kwargs["ref"]
            version = kwargs["version"]
            workspace = kwargs.get(
                "workspace", self._args["workspace"])
            archive = kwargs["archive"]
        except KeyError as e:
            raise KeyError("missing scope, ref, version or archive") from e

        # If we did not have to store the files on the filesystem using the
        # stupid pattern <tag>-<epoch>-<uuid> as proposed by Limor
        # this process would be much easier
        archive_files = archive.namelist()
        search_filter = re.compile(f"{workspace}/{scope}/{ref}/{version}-*-*")

        # search for all files that we need data.json and relation.json
        scope_file_list = list(filter(search_filter.match, archive_files))

        # first check if we already have a folder with that name
        # if yes we do not continue, it means we have already
        # data object in the archive
        try:
            scope_folder = os.path.dirname(scope_file_list[0])
            data_folder = os.path.join(
                FilesystemPlugin._ROOT_PATH, scope_folder)
            os.makedirs(data_folder, exist_ok=False)
        except IndexError as e:
            raise FileNotFoundError("Scope not present in archive") from e
        except OSError:
            # Folder already exists, meaning this object already
            # exists in the database
            return

        # extract all objects
        for archived_file in scope_file_list:
            archive.extract(archived_file, FilesystemPlugin._ROOT_PATH)

    def list_versions(self, **kwargs):
        """
        list all existing scopes
        """
        try:
            scope = kwargs["scope"]
            ref = kwargs["ref"]
            workspace = kwargs.get(
                "workspace", self._args["workspace"])
        except KeyError as e:
            raise ValueError("missing workspace, scope, or ref") from e

        pattern = os.path.join(FilesystemPlugin._ROOT_PATH,
                               workspace, scope, ref, "*")
        versions = []
        for folder in glob.glob(pattern):
            tokens = os.path.split(folder)
            try:
                folder = tokens[0]
                version = tokens[1]
            except IndexError:
                continue

            tokens = version.split("-")
            try:
                tag = tokens[0]
                date = tokens[1]
            except IndexError:
                continue

            versions.append({
                "url": f"{workspace}/{scope}/{ref}/{tag}", #os.path.join(folder.replace(FilesystemPlugin._ROOT_PATH, ""), tag),
                "tag": tag,
                "date": date}
            )

        return versions

    def get_related_objects(self, **kwargs):
        """
        Get a list of all related objects
        """
        model = kwargs.get("model", None)
        depth = kwargs.get("depth", 0)
        level = kwargs.get("level", 0)
        search_filter = kwargs.get("search_filter", None)

        # If we are passing a model we can get all the information
        # from the model itself
        if issubclass(type(model), Model):
            scope = model.scope
            ref = model.ref
            schema = model.schema
            data = model.serialize()
            workspace = model.workspace
            version = model.version
        else:
            # No model, the user must have passed the required
            # arguments
            try:
                scope = kwargs["scope"]
                ref = kwargs["ref"]
                version = kwargs["version"]
                workspace = kwargs.get(
                    "workspace", self._args["workspace"])
                data = None
            except KeyError as e:
                raise KeyError("missing scope, ref or version") from e

        # The base path for this object:
        # <ROOT_PATH>/<workspace_id>/<scope>/ref
        basepath = os.path.join(
            FilesystemPlugin._ROOT_PATH, workspace, scope, ref)

        # We list all folders with the following pattern:
        # <base_path>/<version>-*
        # we only use the the first item found, in theory there should
        # not exist more than one
        out = set()
        try:
            data_folder = glob.glob(os.path.join(basepath, f"{version}-*"))[0]
        except IndexError:
            return out

        # We first check if we have cached relations ( see rebuild_indexes )
        # if that's the case return the cached information
        try:
            # We look for a file called relations.json, it holds a cache
            # to this objects relation
            filename = os.path.join(data_folder, "relations.json")
            with open(filename, 'r') as data_fp:
                relations = json.load(data_fp)

            for value in relations:
                target_workspace, target_scope, target_ref, target_version = ScopesTree.extract_reference(
                    value)

                # We add the found related object in the list
                # if we passed a search filter we check if scope
                # is in the list, otherwise the list will be
                # None and trigger a TypeError
                try:
                    if target_scope in search_filter:
                        out.add(
                            f"{target_workspace}/{target_scope}/{target_ref}/{target_version}")
                except TypeError:
                    out.add(
                        f"{target_workspace}/{target_scope}/{target_ref}/{target_version}")

                if level < depth:
                    out.update(
                        Model.get_relations(
                            workspace=target_workspace, scope=target_scope,
                            ref=target_ref, version=target_version,
                            level=level+1, depth=depth, search_filter=search_filter))

            return out

        except FileNotFoundError:
            pass

        # No cache found, this mean we have to check for relations using
        # the worst possible, this method is costly
        if data is None:
            # if data is no set it means we need to load it from
            # the file system
            try:
                filename = os.path.join(data_folder, "data.json")
                with open(filename, 'r') as data_fp:
                    data = json.load(data_fp)

                schema_version = data.get("schema_version", "1.0")
                schema = schemas(scope, schema_version)
                data = data[scope][ref]
            except FileNotFoundError:
                return out

        # We use the method implemented in Models to search for available
        # relations
        try:
            relations_def = Model.get_relations_definition(scope)
            Model._get_relations_list(
                relations_def, schema, data, out, 0, depth, search_filter)
        except AttributeError:
            pass
        return out

    def write(self, data: object, **kwargs):
        """
        Stores the object on the persistent layer
        """
        try:
            workspace = kwargs.get(
                "workspace", self._args["workspace"])
        except KeyError as e:
            raise ValueError("Missing workspace") from e

        # when we are saving we must know what version we are
        # storing
        try:
            tag = kwargs["version"]
        except KeyError as e:
            raise ValueError("Please specify version tag") from e

        # A Tree object already have the required information
        if issubclass(type(data), ScopeInstanceVersionNode):

            #if data.version == "__UNVERSIONED__":

            schema = data.schema
            scope = data.scope
            ref = data.ref
            obj = data.serialize()

        # For a dictionary a user must provide some arguments
        elif isinstance(data, dict):
            try:
                scope = kwargs["scope"]
                ref = kwargs["ref"]
                schema_version = kwargs.get("schema_version", "1.0")
            except KeyError as e:
                raise ValueError("missing scope,ref or schema_version") from e

            # we need the schema so we can validate the data
            schema = schemas(scope, schema_version)

            # this allows two possible ways to send a dict
            # - send with scope and ref
            # - send the data only
            # we also validate against the schema to make sure
            # we are only storing what is defined on the schema
            try:
                obj = {}
                self.validate_data(schema, data[scope][ref], obj)
            except KeyError as e:
                obj = {}
                self.validate_data(schema, data, obj)

        else:
            # No dict or TreeNode? No support yet
            raise NotImplementedError

        # The base path for this object:
        # <ROOT_PATH>/<workspace_id>/<scope>/ref
        basepath = os.path.join(
            FilesystemPlugin._ROOT_PATH, workspace, scope, ref)

        # we check if we have already any version stored with
        # this tag
        try:
            _ = glob.glob(os.path.join(basepath, f"{tag}-*"))[0]
            raise ValueError("Version tag already exists")
        except IndexError:
            pass

        # The base path is the updated to have the timestamp a version tag
        # <ROOT_PATH>/<workspace_id>/<scope>/<ref>/<tag>-<epoch>-<random uuid>
        basepath = os.path.join(basepath,
                                f"{tag}-{datetime.now().timestamp()}-{uuid.uuid4()}")

        # This make sures the full path is always available
        os.makedirs(basepath, exist_ok=True)

        # We need to get all the relations first
        # In the future we will need to not allow for storing
        # data that refers to objects that are not archived
        relations_def = Model.get_relations_definition(scope)
        relations = set()
        Model._get_relations_list(relations_def, schema, obj, relations, 0)

        # TODO: enable validation for bad references
        # Uncomment this lines to enable validation against references
        # to elements in the global database

        # for relation in relations:
        #     if relation.find("__UNVERSIONED__") == -1:
        #         continue
        #     raise ValueError("Data contains invalid references")

        # store data
        obj_file = os.path.join(basepath, "data.json")
        with open(obj_file, 'w') as data_fp:
            json.dump({
                "schema_version": schema.version,
                scope: {
                    ref: obj
                }
            }, data_fp)

        # store relations cache
        relation_file = os.path.join(basepath, "relations.json")
        with open(relation_file, 'w') as data_fp:
            json.dump(list(relations), data_fp)

    def read(self, **kwargs):
        """
        load an object from the persistent layer
        """
        try:
            scope = kwargs["scope"]
            ref = kwargs["ref"]
            version = kwargs["version"]
            workspace = kwargs.get(
                "workspace", self._args["workspace"])
        except KeyError as e:
            raise KeyError("missing scope, ref or version") from e

        # The base path is composed by the scope and ref
        # <ROOT_PATH>/<workspace_id>/<scope>/<ref>/<tag>
        basepath = os.path.join(
            FilesystemPlugin._ROOT_PATH, workspace, scope, ref)

        # If we did not have to store the files on the filesystem using the
        # stupid pattern <tag>-<epoch>-<uuid> as proposed by Limor
        # this process would be much easier

        # First time we just check if we have any scope with that version in
        # our archive, otherwise we try to fetch it from a remote archive
        try:
            data_folder = glob.glob(os.path.join(basepath, f"{version}-*"))[0]
        except IndexError:
            # try and fetch the scope from a remote archive
            FilesystemPlugin.get_scope_from_upstream(
                os.path.join(workspace, scope, ref, version))

        # This time we MUST have one or otherwise it means we did not find any in
        # the remote archive
        try:
            data_folder = glob.glob(os.path.join(basepath, f"{version}-*"))[0]
        except IndexError:
            return None

        try:
            filename = os.path.join(data_folder, "data.json")
            with open(filename, 'r') as data_fp:
                return json.load(data_fp)
        except FileNotFoundError:
            return None

    def delete(self, data: object, **kwargs):
        """
        delete data in the persistent layer
        """
        if not issubclass(type(data), ScopeInstanceVersionNode):
            raise NotImplementedError

        raise NotImplementedError

    def rebuild_indexes(self, **kwargs):
        """
        force the database layer to rebuild
        all indexes, for now we do not implement this
        on the file system
        The reason behind it is beacuse data in the archive
        should always reference to existing data, therefore
        the relations created during the saving process
        should be more than enough
        """


Persistence.register_plugin("filesystem", FilesystemPlugin)
