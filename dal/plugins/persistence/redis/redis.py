"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
import os
import pickle
import re
import json
import fnmatch
from redis.client import ConnectionPool, Redis
from redis.exceptions import ResponseError
from dal.plugins import Plugin
from dal.data import (Persistence, PersistencePlugin, SchemaPropertyNode,
                      SchemaNode, ScopeInstanceVersionNode, schemas)
from dal.scopes import TreeNode, ScopesTree
from movai.models import Model


__DRIVER_NAME__ = "Mov.ai Redis Plugin"
__DRIVER_VERSION__ = "0.0.2"


class RedisPlugin(PersistencePlugin):
    """
    This class implements the actual plugin that store on redis,
    maitaining compatibility with the V1, this means that when
    saving to the redis the key used for each attrinute will be
    composed of the following constrains:

    - When an attribute had the "value_on_key" flag it will be stored in the
    the key composition, otherwise it will be stored as a value
    - Composition pattern: <scope>:<id>[(,<attr>:<id>)*](,<attr>)+:(<value>)*
    """
    _REDIS_MASTER_HOST = os.getenv('REDIS_MASTER_HOST', "localhost")
    _REDIS_MASTER_PORT = os.getenv('REDIS_MASTER_PORT', "6379")
    _REDIS_SLAVE_HOST = os.getenv('REDIS_SLAVE_HOST', _REDIS_MASTER_HOST)
    _REDIS_SLAVE_PORT = os.getenv('REDIS_SLAVE_PORT', _REDIS_MASTER_PORT)

    _REDIS_MASTER_POOL = ConnectionPool(
        host=_REDIS_MASTER_HOST, port=_REDIS_MASTER_PORT, db=0)
    _REDIS_SLAVE_POOL = ConnectionPool(
        host=_REDIS_SLAVE_HOST, port=_REDIS_SLAVE_PORT, db=0)

    def decode_value(self, _value):
        '''Decodes a value from redis'''
        try:
            return _value.decode('utf-8')
        except UnicodeDecodeError:
            return pickle.loads(_value)

    def decode_hash(self, _hash):
        '''Decodes a full hash from redis'''
        decoded_hash = {}
        for key, val in _hash.items():  # decode 1 by 1
            try:
                decoded_hash[key.decode('utf-8')] = val.decode('utf-8')
            except UnicodeDecodeError:
                decoded_hash[key.decode('utf-8')] = pickle.loads(val)
        return decoded_hash

    def decode_list(self, _list):
        '''Decodes a full list from redis'''
        try:
            decoded_list = [elem.decode('utf-8') for elem in _list]
        except UnicodeDecodeError:
            decoded_list = [pickle.loads(elem) for elem in _list]
        return decoded_list

    def key_to_dict(self, schema: TreeNode, key: str, conn, data):
        """
        convert a key in the V1 specfication to a dictonary, also
        loads the value from the Redis database
        """

        keys = re.split("[:,]", key)

        if len(keys) < 3:
            raise ValueError("Invalid key")

        current_ptr = None
        old_ptr = data
        for idx in range(len(keys)-2):
            attr = keys[idx]
            try:
                _ = old_ptr[attr]
            except KeyError:
                old_ptr[attr] = {}

            current_ptr = old_ptr[attr]
            old_ptr = current_ptr
            idx += 1

        attr = keys[idx]
        if schema.attributes.get("value_on_key", False):
            current_ptr[attr] = keys[idx+1]
            return

        # A simple value?
        try:
            current_ptr[attr] = self.decode_value(conn.get(key))
            return
        except ResponseError:
            pass

        # A hash?
        try:
            current_ptr[attr] = self.decode_hash(conn.hgetall(key))
            return
        except ResponseError:
            pass

        # A list?
        try:
            current_ptr[attr] = self.decode_list(conn.lrange(key, 0, -1))
        except ResponseError:
            current_ptr[attr] = None

    def save_keys(self, schema: TreeNode, base: str, keys: list, conn: Redis, data: dict):
        """
        Save the object in the redis, according the V1 specifications
        """
        try:
            # if we are on a property node, store it on the database
            if isinstance(schema, SchemaPropertyNode):

                key = f"{base},{schema.name}:"
                value_on_key = schema.attributes.get("value_on_key", False)
                value = data[schema.name]

                # Add key to key set internal:<scope>:<ref>:keys
                if value_on_key:

                    # since we store the value in the key we need to verify if there
                    # is already a key with this name without the value
                    # if yes means we are changing the value so we need to remove
                    # the old key
                    try:
                        old_key = fnmatch.filter(
                            keys, f'{key}*')[0]
                        if old_key != f"{key}{value}":
                            conn.delete(old_key)
                        else:
                            # already there, don't remove after
                            keys.remove(old_key)

                    except (IndexError, TypeError):
                        pass

                    key = f"{key}{value}"
                    conn.set(key, pickle.dumps(value))
                    return

                # we always delete the key first
                conn.delete(key)
                try:
                    keys.remove(key)
                except ValueError:
                    # not there
                    pass

                if schema.attributes['type'] == dict:
                    for dkey, dvalue in value.items():
                        conn.hset(key, dkey, pickle.dumps(dvalue))
                    return

                if schema.attributes['type'] == list:
                    for lvalue in value:
                        conn.rpush(key, pickle.dumps(lvalue))
                    return

                conn.set(key, pickle.dumps(value))
                return

            # it's not a terminal element, compose the next
            # base key and process this node children
            base += f",{schema.name}:"

            if schema.attributes.get("is_hash", True):
                for name in data[schema.name].keys():
                    for child in schema.children:
                        self.save_keys(
                            child, f"{base}{name}", keys, conn, data[schema.name][name])
                return

            for child in schema.children:
                self.save_keys(child, base, keys, conn, data[schema.name])

        except KeyError:
            # data doesn't have the key/object in the schema
            # (at least) sometimes it's not a problem
            pass
        except AttributeError:

            # No schema! check in this node children if any
            for child in schema.children:
                self.save_keys(child, base, keys, conn, data)

    def delete_keys(self, schema: TreeNode, base: str, keys: list, conn: Redis, data: dict):
        """
        Delete some keys from the redis, according the V1 specifications
        """
        try:
            # if we are on a property node, store it on the database
            if isinstance(schema, SchemaPropertyNode):

                key = f"{base},{schema.name}:"
                value_on_key = schema.attributes.get("value_on_key", False)
                value = data[schema.name]

                # Add key to key set internal:<scope>:<ref>:keys
                if value_on_key:

                    # since we store the value in the key we need to verify if there
                    # is already a key with this name without the value
                    # if yes means we are changing the value so we need to remove
                    # the old key
                    key = f"{key}{value}"
                    value = None

                # key will not be deleted if does not exist
                if conn.delete(key) == 1:
                    print(f"deleted key:{key}")
                # else, key not deleted

                return

            # it's not a terminal element, compose the next
            # base key and process this node children
            base += f",{schema.name}:"

            if schema.attributes.get("is_hash", True):
                for name in data[schema.name].keys():
                    for child in schema.children:
                        to_delete = data[schema.name][name]
                        if isinstance(to_delete, dict):
                            self.delete_keys(
                                child, f"{base}{name}", keys, conn, to_delete)
                            continue
                        self.delete_all_keys(
                            child, f"{base}{name}", keys, conn)
                return

            for child in schema.children:
                self.delete_keys(child, base, keys, conn, data[schema.name])

        except (KeyError, AttributeError):

            # No schema! check in this node children if any
            for child in schema.children:
                self.delete_keys(child, base, keys, conn, data)

    def delete_all_keys(self, schema: TreeNode, base: str, keys: list, conn: Redis):
        """
        Delete the object from redis, according the V1 specifications
        """
        try:
            # if we are on a property node, store it on the database
            if isinstance(schema, SchemaPropertyNode):

                key = f"{base},{schema.name}:"
                value_on_key = schema.attributes.get("value_on_key", False)

                if value_on_key:
                    key = f"{key}*"

                saved_keys = fnmatch.filter(keys, key)

                if saved_keys:
                    key_count = conn.delete(*saved_keys)
                    print(f"deleted {key_count} of {len(saved_keys)} keys")
                    # for key in saved_keys:
                    #    print(f"delete key:{key.decode('utf-8')}")

                return

            # it's not a terminal element, compose the next
            # base key and process this node children
            base += f",{schema.name}:"

            if schema.attributes.get("is_hash", True):
                base = f"{base}*"

            for child in schema.children:
                self.delete_all_keys(child, base, keys, conn)

        except (KeyError, AttributeError):

            # No schema! check in this node children if any
            for child in schema.children:
                self.delete_all_keys(child, base, keys, conn)

    def load_keys(self, schema: TreeNode, base: str, keys: list, conn: Redis, out: dict):
        """
        Save the object in the redis, according the V1 specifications
        """
        try:
            # if we are on a property node, store it on the database
            if isinstance(schema, SchemaPropertyNode):

                key = f"{base},{schema.name}:"
                value_on_key = schema.attributes.get("value_on_key", False)

                if value_on_key:
                    key = f"{key}*"

                for match_key in fnmatch.filter(keys, key):
                    self.key_to_dict(schema, match_key, conn, out)

                return

            # it's not a terminal element, compose the next
            # base key and process this node children
            base += f",{schema.name}:"

            if schema.attributes.get("is_hash", True):
                base = f"{base}*"

            for child in schema.children:
                self.load_keys(child, base, keys, conn, out)

        except (KeyError, AttributeError):

            # No schema! check in this node children if any
            for child in schema.children:
                self.load_keys(child, base, keys, conn, out)

    def fetch_keys_iter(self, conn, scope: str, ref: str) -> list:
        """ Get keys using SCAN ITER command """
        # for now this method is not in use but benchmarks should be done
        # against the method fetch_keys
        return [s.decode() for s in conn.scan_iter(f'{scope}:{ref},*', count=10000)]

    def fetch_keys(self, conn, scope: str, ref: str) -> list:
        """ Get keys using KEYS command """
        return [s.decode() for s in conn.keys(f'{scope}:{ref},*')]

    def schema_to_key(self, schema: TreeNode):
        """
        Convert a schema to a redis key according to the standard
        """

        if isinstance(schema, SchemaNode) or schema is None:
            return ""

        if isinstance(schema, SchemaPropertyNode):

            if schema.attributes.get("value_on_key", False):
                return f"{self.schema_to_key(schema.parent)},{schema.name}:*"

            return f"{self.schema_to_key(schema.parent)},{schema.name}:"

        if schema.attributes.get("is_hash", False):
            return f"{self.schema_to_key(schema.parent)},{schema.name}:*"

        return f"{self.schema_to_key(schema.parent)},{schema.name}"

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
        return False

    def create_workspace(self, ref: str, **kwargs):
        """
        creates a new workspace, on the REDIS driver this is not supported
        by design
        """

    def delete_workspace(self, ref: str):
        """
        deletes a existing workspace
        """

    def list_workspaces(self):
        """
        list available workspaces, on the REDIS driver this is not supported
        by design
        """
        return []

    def list_scopes(self, **kwargs):
        """
        list all existing scopes
        This might need to be changed in the future, for now it
        search all keys in redis, we might need in the future
        to use a "caching" mechanism, probably a set that is updated
        everytime a a scope is added/delete
        """
        conn = Redis(connection_pool=RedisPlugin._REDIS_SLAVE_POOL)
        scopes = []
        processed = set()
        scope = kwargs.get("scope", "*")
        try:
            workspace = kwargs.get(
                "workspace", self._args["workspace"])
        except KeyError as e:
            raise ValueError("missing workspace") from e

        for key in conn.scan_iter(f"{scope}:*", count=50):
            tokens = re.split("[:,]", key.decode('utf-8'))
            try:
                scope = tokens[0]
                ref = tokens[1]
                if f"{scope}:{ref}" in processed:
                    continue

                processed.add(f"{scope}:{ref}")
                scopes.append({
                    "url": f"{workspace}/{scope}/{ref}",
                    "scope": scope,
                    "ref": ref
                })

            except IndexError:
                continue

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

        data = self.read(**kwargs)
        relations = self.get_related_objects(**kwargs)

        archive.writestr(f"{workspace}/{scope}/{ref}/{version}/data.json", json.dumps(data))
        archive.writestr(f"{workspace}/{scope}/{ref}/{version}/relation.json", json.dumps(list(relations)))

    def restore(self, **kwargs):
        """
        restore a scope/scopes from a zip file
        """
        try:
            scope = kwargs["scope"]
            ref = kwargs["ref"]
            workspace = kwargs.get(
                "workspace", self._args["workspace"])
            archive = kwargs["archive"]
        except KeyError as e:
            raise KeyError("missing scope, ref, version or archive") from e

        # just get the data since the relations are created
        # when we store a object in the database
        data_file = f"{workspace}/{scope}/{ref}/__UNVERSIONED__/data.json"

        try:
            # load data from the archive
            with archive.open(data_file) as data_fp:
                data = json.load(data_fp)
        except KeyError as e:
            raise FileNotFoundError("Scope not in archive") from e

        # write this object in the database
        self.write(data,scope=scope,ref=ref)

    def list_versions(self, **kwargs):
        """
        list all existing scopes
        """
        conn = Redis(connection_pool=RedisPlugin._REDIS_SLAVE_POOL)
        try:
            scope = kwargs["scope"]
            ref = kwargs["ref"]
            workspace = kwargs.get(
                "workspace", self._args["workspace"])
        except KeyError as e:
            raise ValueError("missing workspace, scope, or ref") from e

        conn.keys
        if len(list(conn.scan_iter(f"{scope}:{ref}*", count=50))) == 0:
            return []

        return [{
                "url": f"{workspace}/{scope}/{ref}",
                "tag": "__UNVERSIONED__",
                "date": ""}]

    def workspace_info(self, ref: str):
        """
        get information about a workspace
        """

    def get_related_objects(self, **kwargs):
        """
        Get a list of all related objects
        """
        model = kwargs.get("model", None)
        depth = kwargs.get("depth", 0)
        level = kwargs.get("level", 0)
        search_filter = kwargs.get("search_filter", None)

        if issubclass(type(model), ScopeInstanceVersionNode):
            scope = model.scope
            ref = model.ref
            schema = model.schema
        else:
            try:
                scope = kwargs["scope"]
                ref = kwargs["ref"]
                schema_version = kwargs.get("schema_version", "1.0")
                schema = schemas(scope, schema_version)
            except KeyError as e:
                raise ValueError("missing scope,ref,version or model") from e

        # We are reading so we connect to the slave instance
        conn = Redis(connection_pool=RedisPlugin._REDIS_SLAVE_POOL)
        out = set()

        # We first check if we have cached relations ( see rebuild_indexes )
        # if that's the case return the cached information
        if conn.exists(f"{scope}:{ref},relations:"):
            for relation in conn.lrange(f"{scope}:{ref},relations:", 0, -1):
                value = relation.decode('utf-8')

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

        # No cached relations we need to search for relations, depending on
        # the depth of the search this can be a costly operation
        for relation, target in Model.get_relations_definition(scope).items():

            # we get the attribute defined in the relations table
            # and compose a search pattern: <scope>:<ref>:<attr_schema>:
            attr_schema = schema.from_path(relation)
            pattern = f"{scope}:{ref}{self.schema_to_key(attr_schema)}"

            # we iterate over all keys found with the constructed
            # pattern, and process it in other to get the
            # object it references to
            for key in conn.scan_iter(pattern, count=50):

                # If the value is on key we get the value from the
                # last token of the string, otherwise we read
                # the value from the database
                if attr_schema.attributes.get("value_on_key", False):
                    try:
                        tokens = re.split("[:,]", key.decode('utf-8'))
                        value = tokens[-1]
                    except IndexError:
                        continue
                else:
                    try:
                        value = self.decode_value(
                            conn.get(key.decode('utf-8')))
                    except ResponseError:
                        continue

                target_workspace, target_scope, target_ref, target_version = ScopesTree.extract_reference(
                    value, scope = target["scope"])

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

                # If we want to go deeper in the relations, the deeper we search
                # the costly it gets, we should avoid deep searches
                if level < depth:
                    out.update(
                        Model.get_relations(
                            workspace=target_workspace, scope=target_scope,
                            ref=target_ref, version=target_version,
                            level=level+1, depth=depth, search_filter=search_filter))

        return out

    def write(self, data: object, **kwargs):
        """
        Stores the object on the persistent layer, for now we only support
        ScopeInstanceVersionNode, and python dict.

        if you pass a dict you must provide the following args:
            - scope
            - ref
            - schema_version

        Currently a dict must be in one of the following form:
        - { <scope> : { {ref} : { <data> } } }
        - { <data> }

        The data part must comply with the schema of the scope
        """
        conn = Redis(connection_pool=RedisPlugin._REDIS_MASTER_POOL)

        if issubclass(type(data), ScopeInstanceVersionNode):

            # Only unversioned objects can be stored on
            # redis
            if data.version == "__UNVERSIONED__":

                schema = data.schema
                scope = data.scope
                ref = data.ref

                # save this object in the database
                # when using a ScopeInstanceVersionNode, assume the data is complete,
                # that it's not partial, any other key in redis (related to this) is
                # unwanted
                redis_keys = self.fetch_keys(conn, scope, ref)
                self.save_keys(schema, f"{scope}:{ref}", redis_keys, conn, data.serialize())

                # store the schema version of this data
                conn.set(f"{scope}:{ref},_schema_version:",  schema.version)
                try:
                    redis_keys.remove(f"{scope}:{ref},_schema_version:")
                except ValueError:
                    # not there yet
                    pass

                # delete the old relations cache and update it
                conn.delete(f"{scope}:{ref},relations:")
                try:
                    redis_keys.remove(f"{scope}:{ref},relations:")
                except ValueError:
                    # not there yet
                    pass
                relations = self.get_related_objects(model=data)
                for relation in relations:
                    conn.rpush(f"{scope}:{ref},relations:", relation)

                # remove excessive keys
                if len(redis_keys) > 0:
                    conn.delete(*redis_keys)

                return None

            raise ValueError("Redis plugin do not support versions")

        if isinstance(data, dict):

            try:
                scope = kwargs["scope"]
                ref = kwargs["ref"]
                remove_extra = kwargs.get('remove_extra', False)
                schema_version = data.get("schema_version",kwargs.get("schema_version", "1.0"))
            except KeyError as e:
                raise ValueError("missing scope,ref or schema_version") from e

            # get the current schema for this object
            schema = schemas(scope, schema_version)

            try:
                obj = data[scope][ref]
            except KeyError as e:
                obj = data

            # save the object into the database
            redis_keys = self.fetch_keys(conn, scope, ref)
            self.save_keys(schema, f"{scope}:{ref}", redis_keys, conn, obj)

            # store the schema version of this data
            conn.set(f"{scope}:{ref},_schema_version:",  schema_version)
            try:
                redis_keys.remove(f"{scope}:{ref},_schema_version:")
            except ValueError:
                pass

            # delete the old relations cache and update it
            conn.delete(f"{scope}:{ref},relations:")
            relations = self.get_related_objects(
                scope=scope, ref=ref, schema_version=schema_version)
            for relation in relations:
                conn.rpush(f"{scope}:{ref},relations:", relation)
            try:
                redis_keys.remove(f"{scope}:{ref},relations:")
            except ValueError:
                pass

            if remove_extra and len(redis_keys) > 0:
                conn.delete(*redis_keys)

            return None

        raise NotImplementedError(f"Type not serializable: {type(data)}")

    def read(self, **kwargs):
        """
        load an object from the persistent layer, you must provide the
        following args
        - scope
        - ref
        The following argument is optional:
        - schema_version

        If the schema_version is not specified we will try to load it
        from redis, if it is missing the default will be 1.0
        """
        try:
            scope = kwargs["scope"]
            ref = kwargs["ref"]
        except KeyError as e:
            raise ValueError("missing scope or name") from e

        conn = Redis(connection_pool=RedisPlugin._REDIS_SLAVE_POOL)

        try:
            schema_version = kwargs["schema_version"]
        except KeyError:
            schema_version = conn.get(f"{scope}:{ref},_schema_version:")

        if schema_version is None:
            schema_version = "1.0"
        else:
            schema_version = schema_version.decode("utf-8")

        schema = schemas(scope, schema_version)
        data = {"schema_version": schema_version}
        self.load_keys(schema, f"{scope}:{ref}", self.fetch_keys(conn, scope, ref), conn, data)

        return data

    def delete(self, data: object = None, **kwargs):
        """
        delete an object from the persistent layer,
        you may provide a ScopeInstanceVersionNode or use the following args;
        - scope
        - ref
        - data
        And optional:
        - schema_version

        If the schema_version is not specified we will try to load it
        from redis, if it is missing the default will be 1.0

        If data is not a dict this will erase all keys defined in schema,
        otherwise it will only delete the passed structure
        """
        conn = Redis(connection_pool=RedisPlugin._REDIS_MASTER_POOL)

        if issubclass(type(data), ScopeInstanceVersionNode):

            if data.version == "__UNVERSIONED__":

                schema = data.schema
                scope = data.scope
                ref = data.ref
                data = data.serialize()

                self.delete_keys(schema, f"{scope}:{ref}", self.fetch_keys(conn, scope, ref), conn, data)
                # also delete schema version key
                conn.delete(f"{scope}:{ref},_schema_version:")
                conn.delete(f"{scope}:{ref},relations:")

                return

            raise ValueError("Redis plugin do not support versions")

        try:
            scope = kwargs["scope"]
            ref = kwargs["ref"]
        except KeyError as e:
            raise ValueError("missing scope or name") from e

        try:
            schema_version = kwargs["schema_version"]
        except KeyError:
            try:
                schema_version = conn.get(f"{scope}:{ref},_schema_version:").decode()
            except AttributeError:
                # got None from schema_version
                schema_version = "1.0"

        schema = schemas(scope, schema_version)
        if isinstance(data, dict):

            try:
                obj = data[scope][ref]
            except KeyError as e:
                obj = data

            self.delete_keys(schema, f"{scope}:{ref}", self.fetch_keys(conn, scope, ref), conn, obj)
            conn.delete(f"{scope}:{ref},_schema_version:")
            conn.delete(f"{scope}:{ref},relations:")
            return

        self.delete_all_keys(schema, f"{scope}:{ref}", self.fetch_keys(conn, scope, ref), conn)
        conn.delete(f"{scope}:{ref},_schema_version:")
        conn.delete(f"{scope}:{ref},relations:")

    def rebuild_indexes(self, **kwargs):
        """
        force the database layer to rebuild
        all indexes, this is a costly operation
        """
        conn = Redis(connection_pool=RedisPlugin._REDIS_MASTER_POOL)

        items = self.list_scopes()

        for item in items:
            scope = item['scope']
            ref = item['ref']
            # delete the old relations cache and update it
            conn.delete(f"{scope}:{ref},relations:")
            schema_version = conn.get(f"{scope}:{ref},_schema_version:")

            # If we do not a version it probably means
            # it's version 1.0
            if schema_version is None:
                schema_version = "1.0"
                # store the schema version of this data
                conn.set(f"{scope}:{ref},_schema_version:",  schema_version)
            else:
                schema_version = schema_version.decode("utf-8")

            relations = self.get_related_objects(
                scope=scope, ref=ref, schema_version=schema_version)
            for relation in relations:
                conn.rpush(f"{scope}:{ref},relations:", relation)


Persistence.register_plugin("redis", RedisPlugin)
