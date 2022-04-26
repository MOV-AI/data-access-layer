"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
import re
from abc import ABC
from importlib import import_module
from dal.data.tree import TreeNode, ObjectNode, PropertyNode, CallableNode, DictNode
from dal.data.serialization import (
    ObjectDeserializer,
    ObjectSerializer,
    SerializableObject,
)
from dal.data.workspace import WorkspaceObject, WorkspaceNode
from dal.data.schema import schemas, SchemaPropertyNode, SchemaNode, SchemaObjectNode
from dal.data.persistence import Persistence, PersistentObject
from dal.data.version import VersionObject


class ScopeInstanceNode(DictNode, WorkspaceObject):
    """
    Implements a scope instance node, a scope is an mov.ai object
    a Callback, a Flow or a Node, an instance is the actual object
    that contains the data, each instance might have multiple versions
    """

    def __init__(self, ref):
        self._ref = ref
        super().__init__()

    @property
    def ref(self):
        """
        returns this instance reference
        """
        return self._ref

    @property
    def node_type(self):
        return "scope_instance"

    @property
    def path(self):
        """
        get the tree path
        """
        return self._ref if self.parent is None else f"{self.parent.path}/{self._ref}"

    @property
    def scope(self):
        """
        the scope name
        """
        scope = self.get_first_parent("scope")
        return None if scope is None else scope.scope

    @property
    def workspace(self):
        workspace = self.get_first_parent("workspace")
        return None if workspace is None else workspace.workspace


class ScopeInstanceVersionNode(
    ObjectNode, VersionObject, WorkspaceObject, PersistentObject, ABC
):
    """
    This class represents a instance version, the instance version is the
    object that actually contains the data
    """

    __PROTECTED__ = [
        "_parent",
        "_sorted",
        "_attributes",
        "_name",
        "_children",
    ]

    def set_acl(self):
        pass

    @property
    def node_type(self):
        return "scope_version"

    @property
    def workspace(self):
        workspace = self.get_first_parent("workspace")
        return None if workspace is None else workspace.workspace

    @property
    def version(self):
        """
        The current version
        """
        return self.name

    @property
    def scope(self):
        """
        the scope name
        """
        scope = self.get_first_parent("scope")
        return None if scope is None else scope.scope

    @property
    def ref(self):
        """
        this object reference
        """
        instance = self.get_first_parent("scope_instance")
        return None if instance is None else instance.ref

    @property
    def schema_version(self):
        """
        the scope schema version
        """
        try:
            return self.attributes["schema_version"]
        except KeyError:
            return "1.0"

    @property
    def schema(self):
        """
        the scope schema
        """
        try:
            return self.attributes["schema"]
        except KeyError:
            return schemas(self.scope, self.schema_version)

    def write(self, **kwargs):
        """
        Write this object to the database
        """
        # We might want to change workspace
        workspace = kwargs.get("workspace", self.get_first_parent("workspace"))

        if workspace is None:
            raise AttributeError("No defined workspace")

        return workspace.write(self, **kwargs)

    def delete(self, **kwargs):
        """
        Write this object to the database
        """
        # We might want to change workspace
        workspace = kwargs.get("workspace", self.get_first_parent("workspace"))

        if workspace is None:
            raise AttributeError("No defined workspace")

        return workspace.delete(self, **kwargs)

    def serialize(self, **_):
        """
        serialize this Scope object
        """
        return ScopeAttributeSerializer(self.schema).serialize(self)

    def __setattr__(self, name: str, value: object):
        """
        We override the set attribute of python, this allow us
        to check if we are adding a property from the schema,
        in that case we need to make sure we set the propery
        tree structure, otherwise we just invoke the default
        python behaviour
        """

        try:
            # If we are not getting the the protected attrs it means that
            # might be trying to access a non existent attr, but one that's
            # defined in the schema, this will trigger a attribute error
            # so we can check the schema for this object
            if name not in ScopeInstanceVersionNode.__PROTECTED__:
                _ = super().__getattribute__(name)

            # this is to make sure __dict__ and other attrs are always
            # accessible, this protects against "max recursive calls reached"
            super().__setattr__(name, value)
            return
        except AttributeError:
            pass

        # now we check the current schema for this attribute, if not available
        # it we need to make call the default behaviour
        try:
            attr_schema = self.schema[name]
        except KeyError:
            super().__setattr__(name, value)
            return

        # Check if the attr is a property or object
        if isinstance(attr_schema, SchemaPropertyNode):
            attr = ScopePropertyNode(name, value)
            attr.attributes["schema"] = attr_schema
            self.add_child(attr)
        elif isinstance(attr_schema, SchemaObjectNode):

            if not isinstance(value, dict):
                raise ValueError("Invalid value must be a dict")

            # A dict
            if attr_schema.attributes.get("is_hash", False):
                attr = ScopeDictNode(name)
                for k, v in value.items():
                    attr_child = ScopeObjectNode(k)
                    attr_child.attributes["schema"] = attr_schema
                    for node_attr in attr_schema.children:
                        ScopeAttributeDeserializer._deserialize(
                            node_attr, attr_child, v
                        )
                    attr.add_child(attr_child)
                self.add_child((name, attr))
                return

            # a object
            attr = ScopeObjectNode(name)
            attr.attributes["schema"] = attr_schema

            for child in attr_schema.children:
                ScopeAttributeDeserializer._deserialize(child, attr, value)

            self.add_child(attr)

    def __getattribute__(self, name):

        try:
            attr = super().__getattribute__(name)
        except AttributeError:
            attr = super().__getattr__(name)
        if type(attr) == ScopePropertyNode:  # pylint: disable=unidiomatic-typecheck
            return attr.value
        # else
        return attr

    def __getattr__(self, name):
        try:
            attr_schema = self.schema[name]
        except KeyError as e:
            raise AttributeError from e

        if isinstance(attr_schema, SchemaPropertyNode):
            try:
                a_cls = ScopeNode.__PROPERTIES_MAP__[attr_schema.path]
                i_value = attr_schema.value()
            except KeyError:
                a_cls = ScopePropertyNode
                i_value = None
            print(a_cls, attr_schema.path)
            attr = a_cls(
                name, i_value
            )  # FIXME Properties should probably raise an exception or something
            attr.attributes["schema"] = attr_schema
            self.add_child(attr)
            # in case it gets overriden
            return getattr(self, name)

        if isinstance(attr_schema, SchemaObjectNode):

            # A dict
            if attr_schema.attributes.get("is_hash", False):
                attr = ScopeDictNode(name)
                attr.attributes["child_schema"] = attr_schema
                self.add_child((name, attr))
                return attr

            # a object
            a_cls = ScopeNode.__OBJECTS_MAP__.get(attr_schema.path, ScopeObjectNode)
            attr = a_cls(name)
            attr.attributes["schema"] = attr_schema
            self.add_child(attr)
            return attr

    def add(self, attr, key, **kwargs):
        """
        Add a new dict attribute, this function, maintains
        compatibility with the old API
        """
        attr = getattr(self, attr)
        if not issubclass(type(attr), DictNode):
            raise ValueError("Attribute not a dictionary")

        for k, v in kwargs.items():
            try:
                attr[key].__setattr__(k, v)
            except AttributeError:
                continue


class ScopeDictNode(DictNode, SerializableObject):
    """
    Implements a scope instance node, a scope is an mov.ai object
    a Callback, a Flow or a Node, an instance is the actual object
    that contains the data
    """

    def __init__(self, name):
        self._name = name
        super().__init__()

    @property
    def scope(self):
        """
        the scope name
        """
        scope = self.get_first_parent("scope")
        if scope is None:
            raise AttributeError("No scope workspace")
        return scope.scope

    @property
    def name(self):
        """
        return attribute name
        """
        return self._name

    @property
    def node_type(self):
        return "scope_dict"

    @property
    def schema(self):
        """
        the scope schema
        """
        try:
            return self.attributes["child_schema"]
        except KeyError:
            scope_instance = self.get_first_parent("scope_instance")
            return None if scope_instance is None else scope_instance.schema

    @property
    def path(self):
        """
        get the tree path
        """
        return self._name if self.parent is None else f"{self.parent.path}/{self._name}"

    # default __getitem__

    def serialize(self, **kwargs):
        """
        serialize this Scope object
        """
        result = {}
        for key, obj in self._children.items():
            result[key] = obj.serialize()
        return result

    def delete(self, key):
        """
        Removes an element from this dict
        """
        self.remove_child(key)

    def __delitem__(self, key):
        """Removes an element from this dict"""
        self.remove_child(key)

    def create(self, key: str, data: dict = None) -> ObjectNode:
        """
        Create a new entry for `key` with an optional initial value
        as dict, serialized into an ScopeObjectNode.
        Returns the newly created attribute
        """
        attr = ScopeObjectNode(key)
        schema = self.schema
        attr.attributes["schema"] = schema
        self.add_child(attr)
        try:
            for data_key in data:
                try:
                    ScopeAttributeDeserializer._deserialize(
                        schema[data_key], attr, data
                    )
                except KeyError:
                    # not defined on schema, ignore
                    pass
        except AttributeError as e:
            # looks like data is not `dict`
            raise TypeError(
                "Can't deserialize given object (should be an `dict`)"
            ) from e
        except TypeError:
            # data is `None`
            pass
        return attr

    def __setitem__(self, key: str, data: dict) -> None:
        """
        Set an item on this object.
        If this object already has the desired key, will DELETE the old one.
        """
        try:
            old = self._children[key]
            self.delete(key)
        except KeyError:
            # doesn't exist
            old = None
        try:
            self.create(key, data)
        except Exception:  # pylint: disable=broad-except
            # if something goes wrong, revert
            if old is not None:
                self._children[key] = old
            raise


class ScopeObjectNode(ObjectNode, SerializableObject, ABC):
    """
    Implements a scope instance node, a scope is an mov.ai object
    a Callback, a Flow or a Node, an instance is the actual object
    that contains the data
    """

    __PROTECTED__ = [
        "_parent",
        "_sorted",
        "_attributes",
        "_name",
        "_children",
    ]

    @property
    def scope(self):
        """
        the scope name
        """
        scope = self.get_first_parent("scope")
        return None if scope is None else scope.scope

    @property
    def schema(self):
        """
        the scope schema
        """
        try:
            return self.attributes["schema"]
        except KeyError:
            scope_instance = self.get_first_parent("scope_instance")
            return None if scope_instance is None else scope_instance.schema

    def __setattr__(self, name: str, value: object):

        try:
            if name not in ScopeObjectNode.__PROTECTED__:
                _ = super().__getattribute__(name)
            super().__setattr__(name, value)
            return
        except AttributeError:
            pass

        try:
            attr_schema = self.schema[name]
        except KeyError as e:
            raise AttributeError from e

        if isinstance(attr_schema, SchemaPropertyNode):
            attr = ScopePropertyNode(name, value)
            attr.attributes["schema"] = attr_schema
            self.add_child(attr)
        elif isinstance(attr_schema, SchemaObjectNode):

            if not isinstance(value, dict):
                raise ValueError("Invalid value must be a dict")

            # A dict
            if attr_schema.attributes.get("is_hash", False):
                attr = ScopeDictNode(name)
                for k, v in value.items():
                    attr_child = ScopeObjectNode(k)
                    attr_child.attributes["schema"] = attr_schema
                    for node_attr in attr_schema.children:
                        ScopeAttributeDeserializer._deserialize(
                            node_attr, attr_child, v
                        )
                    attr.add_child(attr_child)
                self.add_child((name, attr))
                return

            # a object
            attr = ScopeObjectNode(name)
            attr.attributes["schema"] = attr_schema

            for child in attr_schema.children:
                ScopeAttributeDeserializer._deserialize(child, attr, value)

            self.add_child(attr)

    def __getattribute__(self, name):

        try:
            attr = super().__getattribute__(name)
        except AttributeError:
            attr = super().__getattr__(name)
        if type(attr) == ScopePropertyNode:  # pylint: disable=unidiomatic-typecheck
            return attr.value
        # else
        return attr

    def __getattr__(self, name):
        try:
            attr_schema = self.schema[name]
        except KeyError as e:
            raise AttributeError from e

        if isinstance(attr_schema, SchemaPropertyNode):
            try:
                a_cls = ScopeNode.__PROPERTIES_MAP__[attr_schema.path]
                i_value = attr_schema.value()
            except KeyError:
                a_cls = ScopePropertyNode
                i_value = None
            attr = a_cls(
                name, i_value
            )  # FIXME Properties should probably raise an exception or something
            attr.attributes["schema"] = attr_schema
            self.add_child(attr)
            # in case it gets overriden later
            return getattr(self, name)

        if isinstance(attr_schema, SchemaObjectNode):

            # A dict
            if attr_schema.attributes.get("is_hash", False):
                attr = ScopeDictNode(name)
                attr.attributes["child_schema"] = attr_schema
                self.add_child((name, attr))
                return attr

            # a object
            a_cls = ScopeNode.__OBJECTS_MAP__.get(attr_schema.path, ScopeObjectNode)
            attr = a_cls(name)
            attr.attributes["schema"] = attr_schema
            self.add_child(attr)
            return attr

    def serialize(self, **kwargs):
        """
        serialize this Scope object
        """
        return ScopeAttributeSerializer(self.schema).serialize(self)


class ScopePropertyNode(PropertyNode, SerializableObject):
    """
    Represents a property node in a scope tree
    """

    @property
    def scope(self):
        """
        the scope name
        """
        scope = self.get_first_parent("scope")
        return None if scope is None else scope.scope

    @property
    def schema(self):
        """
        the scope schema
        """
        try:
            return self.attributes["schema"]
        except KeyError:
            scope_instance = self.get_first_parent("scope_instance")
            return None if scope_instance is None else scope_instance.schema

    def serialize(self, **kwargs):
        """
        serialize this Scope object
        """
        return ScopeAttributeSerializer(self.schema).serialize(self)


class ScopeNode(DictNode, WorkspaceObject):
    """
    Implements a scope node, a scope is an mov.ai object
    for instance a Callback, a Flow or a Node
    """

    __SCOPES_MAP__ = {}
    __PROPERTIES_MAP__ = {}
    __OBJECTS_MAP__ = {}

    @staticmethod
    def register_scope_class(scope: str, cls: type):
        """
        Override a scope class, this will overried the class
        used to create a ScopeInstanceVersionNode
        """
        if not issubclass(cls, ScopeInstanceVersionNode):
            raise ValueError("Model must be of type ScopeInstanceVersionNode")

        ScopeNode.__SCOPES_MAP__[scope] = cls

    @staticmethod
    def register_scope_property(schema_path: str, cls: type):
        """
        Override a scope class, this will overried the class
        used to create a ScopeInstanceVersionNode
        """
        if not issubclass(cls, ScopePropertyNode):
            raise ValueError("Model must be of type ScopePropertyNode")

        ScopeNode.__PROPERTIES_MAP__[schema_path] = cls

    @staticmethod
    def register_scope_object(schema_path: str, cls: type):
        """
        Override a scope class, this will overried the class
        used to create a ScopeInstanceVersionNode
        """
        if not issubclass(cls, ScopeObjectNode):
            raise ValueError("Model must be of type ScopeObjectNode")

        ScopeNode.__OBJECTS_MAP__[schema_path] = cls

    def __init__(self, scope: str):
        super().__init__()
        self._scope = scope

    @property
    def node_type(self):
        return "scope"

    @property
    def scope(self):
        """
        the scope name
        """
        return self._scope

    @property
    def path(self):
        """
        get the tree path
        """
        if self.parent is None:
            return self._scope

        return f"{self.parent.path}/{self._scope}"

    @property
    def workspace(self):
        workspace = self.get_first_parent("workspace")
        if workspace is None:
            raise AttributeError("No defined workspace")
        return workspace.workspace

    def __getitem__(self, key):

        if isinstance(key, tuple):
            version = key[1]
            key = key[0]
        else:
            version = "__UNVERSIONED__"

        workspace = self.get_first_parent("workspace")

        if workspace is None:
            raise ValueError("No defined workspace")

        # there are plugins that do not support versions therefore we
        # must check this befora
        if not workspace.plugin.versioning and version != "__UNVERSIONED__":
            raise ValueError("Workspace plugin do not support versioning")

        # First we get our instance, if it does not exists create a new
        # one
        try:
            scope_instance = super().__getitem__(key)
        except KeyError:
            scope_instance = ScopeInstanceNode(key)
            self.add_child((key, scope_instance))

        # now we try to return the requested version, if that isn't possible
        # we try to load it from the physical layer
        try:
            return scope_instance[version]
        except KeyError:
            pass

        # We load the data from the persistent layer, if it's not
        # found we might be creating a new one, therefor we overide
        # the version to "__UNVERSIONED__"
        try:
            data = workspace.plugin.read(scope=self._scope, ref=key, version=version)
            schema_version = data.get("schema_version", "1.0")
            data = data.get(self._scope, {})
        except (FileNotFoundError, AttributeError) as e:
            raise KeyError("Scope does not exist") from e

        if not data:
            raise KeyError(f"{self._scope}/{key}/{version} does not exist")

        # Make sure we have the builtin models loaded
        # TODO: load from the database will allow users to create
        # their own models
        try:
            # Try to load model from our library if not already loaded
            if self._scope not in ScopeNode.__SCOPES_MAP__:
                import_module("dal.models")

        except ModuleNotFoundError:
            pass

        # If the model was correctly loaded it will be in the
        # models map
        try:
            scope_class = ScopeNode.__SCOPES_MAP__[self._scope]
        except KeyError:
            scope_class = ScopeInstanceVersionNode

        # Deserialize object tree from the received data
        # force load of schema
        schemas(self._scope, schema_version)
        # FIXME hammered (2 lines)
        scope_instance_version = object.__new__(scope_class)  # scope_class(version)
        scope_instance_version.__init__(version)
        scope_instance_version.attributes["schema_version"] = schema_version
        scope_instance.add_child((version, scope_instance_version))

        scope_instance_version.attributes["schema"] = schemas(
            self._scope, scope_instance_version.schema_version
        )

        for _, v in data.items():
            ScopeAttributeDeserializer(scope_instance_version.schema).deserialize(
                scope_instance_version, v
            )

        scope_instance_version.set_acl()
        return scope_instance_version


class ScopeWorkspace(WorkspaceNode):
    """
    This class represents a workspace with scopes
    """

    @property
    def path(self):
        """
        get the tree path
        """
        return self._workspace

    def unload(self, **kwargs):
        """
        Unload the cached data on this workspace
        """
        try:
            scope = kwargs["scope"]
            ref = kwargs["ref"]
            version = kwargs.get("version", "__UNVERSIONED__")
        except KeyError as e:
            raise ValueError("missing scope or ref") from e

        try:
            self._children[scope]._children[ref].remove_child(version)
        except KeyError as e:
            raise ValueError("Scope not loaded") from e

    def unload_all(self):
        """
        Unload all the cached data in this workspace
        """
        for scope in self._children.values():
            scope._children.clear()

    def __getattr__(self, name):
        try:
            return self.__dict__["_children"][name]
        except KeyError:
            scope_node = ScopeNode(name)
            self.add_child((name, scope_node))
            return scope_node

    def list_scopes(self, **kwargs):
        """
        List all scopes in this workspace
        pass `scope` parameter to filter by scope, default '*' (all)
        """
        return self.plugin.list_scopes(workspace=self.workspace, **kwargs)

    def list_versions(self, scope: str, ref: str):
        """
        List all versions of a specific scope
        """
        return self.plugin.list_versions(workspace=self.workspace, scope=scope, ref=ref)

    def create(
        self, scope: str, ref: str, version="__UNVERSIONED__", overwrite: bool = False
    ):
        """
        create a new scope
        """
        if self.readonly:
            raise ValueError("Read-only workspace")

        # Get the current scope we will be working on
        scope_node = getattr(self, scope)
        try:
            # we already have this version in this workspace
            scope_instance_version = scope_node[ref, version]
            if not overwrite:
                raise ValueError("Scope version already exists")

            raise NotImplementedError("Overwriting not implemented yet")
        except KeyError:
            pass

        # Make sure we load the built-in models
        # TODO: load from the database will allow users to create
        # their own models
        try:
            # Try to load model from our library if not already loaded
            if scope not in ScopeNode.__SCOPES_MAP__:
                import_module("dal.models")
        except ModuleNotFoundError:
            pass

        # If the model was correctly loaded it will be in the
        # models map
        try:
            scope_class = ScopeNode.__SCOPES_MAP__[scope]
        except KeyError:
            scope_class = ScopeInstanceVersionNode

        # get the current scope we will be working, it should
        # have been created when we were looking for the
        # scope version in the code above
        scope_instance = DictNode.__getitem__(scope_node, ref)

        # Create a new version for this scope
        scope_instance_version = object.__new__(scope_class)  # (version)
        scope_instance_version.__init__(version)
        scope_instance.add_child((version, scope_instance_version))
        scope_instance_version.attributes["schema"] = schemas(
            scope, scope_instance_version.schema_version
        )

        return scope_instance_version

    def delete(self, data: object, **kwargs):
        """
        Override the default delete method to also
        unload the document from this scopes tree
        """
        super().delete(data=data, **kwargs)
        try:
            scope = data.scope
            ref = data.ref
        except AttributeError:
            try:
                scope = kwargs["scope"]
                ref = kwargs["ref"]
            except KeyError as e:
                raise ValueError("Missing `scope` and/or `ref` argument") from e

        # else, we got it
        try:
            self.unload(scope=scope, ref=ref)
        except ValueError:
            # not loaded
            pass

    def rebuild_indexes(self):
        """
        force indexes rebuild inside the workspace
        """
        try:
            self._plugin.rebuild_indexes()
        except AttributeError as e:
            raise AttributeError("Plugin not defined") from e


class ScopesTree(CallableNode):
    """
    A scopes tree is an interface to access the stored
    data in mov.ai
    """

    # split pattern 1: <workspace>/<scope>/(<ref>/<ref>/..)/<version>
    __REFERENCE_REGEX_1__ = r"^([a-zA-Z0-9-_.]+)/([a-zA-Z0-9_.]+)/([a-zA-Z0-9_.-]+[/a-zA-Z0-9_.-]*)/([a-zA-Z0-9_.]+)$"

    # split pattern 2: <workspace>/<scope>/<ref>/<version>
    __REFERENCE_REGEX_2__ = (
        r"^([a-zA-Z0-9-_.]+)/([a-zA-Z0-9_.]+)/([a-zA-Z0-9_.-]+)/([/a-zA-Z0-9_.]+)$"
    )

    # split pattern 3: <workspace>/<scope>/<ref>
    __REFERENCE_REGEX_3__ = r"^([a-zA-Z0-9-_.]+)/([a-zA-Z0-9_.]+)/([a-zA-Z0-9_.-]+)$"

    @staticmethod
    def extract_reference(path, **kwargs):
        """
        Convert a path into workspace, scope, ref, version
        """
        try:
            # split pattern 1: <workspace>/<scope>/(<ref>/<ref>/..)/<version>
            workspace, scope, ref, version = re.findall(
                ScopesTree.__REFERENCE_REGEX_1__, path
            )[0]
            return (
                kwargs.get("workspace", workspace),
                kwargs.get("scope", scope),
                ref,
                kwargs.get("version", version),
            )
        except IndexError:
            pass

        try:
            # split pattern 2: <workspace>/<scope>/<ref>/<version>
            workspace, scope, ref, version = re.findall(
                ScopesTree.__REFERENCE_REGEX_2__, path
            )[0]
            return (
                kwargs.get("workspace", workspace),
                kwargs.get("scope", scope),
                ref,
                kwargs.get("version", version),
            )
        except IndexError:
            pass

        try:
            # split pattern 3: <workspace>/<scope>/<ref>/<version>
            workspace, scope, ref = re.findall(ScopesTree.__REFERENCE_REGEX_3__, path)[
                0
            ]
            return (
                kwargs.get("workspace", workspace),
                kwargs.get("scope", scope),
                ref,
                kwargs.get("version", "__UNVERSIONED__"),
            )
        except IndexError:
            # path is just a ref
            return (
                kwargs.get("workspace", "global"),
                kwargs["scope"],
                path,
                kwargs.get("version", "__UNVERSIONED__"),
            )

    @property
    def node_type(self):
        return "scopes"

    @property
    def path(self):
        """
        get the tree path
        """
        if self.parent is None:
            return "scopes"

        return f"{self.parent.path}/scopes"

    def read_from_path(self, path: str, **kwargs):
        """
        Read a document from a specified path
        """
        try:
            workspace, scope, ref, version = ScopesTree.extract_reference(
                path, **kwargs
            )
            return self(workspace=workspace).read(scope=scope, ref=ref, version=version)
        except KeyError as e:
            raise ValueError("Invalid path") from e

    def from_path(self, path: str, **kwargs):
        """
        Read a document from a specified path
        """
        try:
            workspace, scope, ref, version = ScopesTree.extract_reference(
                path, **kwargs
            )
            return getattr(self(workspace=workspace), scope)[ref, version]
        except IndexError as e:
            raise ValueError("Invalid path") from e

    def backup(self, path: str, **kwargs):
        """
        Read a document from a specified path
        """
        try:
            workspace, scope, ref, version = ScopesTree.extract_reference(
                path, **kwargs
            )
            return self(workspace=workspace).backup(
                scope=scope, ref=ref, version=version, **kwargs
            )
        except KeyError as e:
            raise ValueError("Invalid path") from e

    def restore(self, path: str, **kwargs):
        """
        Read a document from a specified path
        """
        try:
            workspace, scope, ref, version = ScopesTree.extract_reference(
                path, **kwargs
            )
            return self(workspace=workspace).restore(
                scope=scope, ref=ref, version=version, **kwargs
            )
        except KeyError as e:
            raise ValueError("Invalid path") from e

    def __call__(self, workspace: str = "global", create: bool = False):
        """
        this access the workspaces on this scope tree, if the workspace is not loaded yet,
        it will be automatically loaded, for now we just support one workspace (global) in redis,
        the other workspaces will be automatically mapped to use the filesystem plugin
        """
        try:
            return self._children[workspace]
        except KeyError:
            if workspace == "global":
                plugin = Persistence.get_plugin_class("redis")(workspace="global")
            else:
                plugin = Persistence.get_plugin_class("filesystem")(workspace=workspace)

            workspace_node = ScopeWorkspace(workspace, plugin)
            self.add_child((workspace, workspace_node))
            return workspace_node


class ScopeAttributeDeserializer(ObjectDeserializer):
    """
    Deserializer through a dict and convert to a tree
    """

    def __init__(self, schema: TreeNode):
        self._schema = schema

    @staticmethod
    def _deserialize(schema: TreeNode, root: TreeNode, data: dict):
        """
        Deserialize a dict according to the defined schema, during
        the deserialization the attribute is associated with the
        related schema
        """
        if issubclass(type(schema), SchemaNode):
            for child in schema.children:
                ScopeAttributeDeserializer._deserialize(child, root, data)
            return

        # A property is simple to add, just add the property node with
        # the name and the stored value
        if issubclass(type(schema), SchemaPropertyNode):
            # check if we have a model for this schema
            try:
                attr_class = ScopeNode.__PROPERTIES_MAP__[schema.path]
            except KeyError:
                attr_class = ScopePropertyNode
            try:
                node = attr_class(schema.name, data[schema.name])
                node.attributes["schema"] = schema
                root.add_child(node)
            except KeyError:
                pass
            return

        # An object in our schemas may be a dict or a object, the only thing
        # ifferent between object and dict on the schema defination is when
        # have the "is_hash" flag, in that case means that the property is
        # a dictionary that holds more than one object
        if issubclass(type(schema), SchemaObjectNode):

            # A dict
            if schema.attributes.get("is_hash", False):
                try:
                    node = ScopeDictNode(schema.name)
                    node_data = data[schema.name]
                    node_attrs = schema.children
                    node.attributes["child_schema"] = schema

                    # check if we have a model for this schema
                    try:
                        attr_class = ScopeNode.__OBJECTS_MAP__[schema.path]
                    except KeyError:
                        attr_class = ScopeObjectNode

                    for key, value in node_data.items():
                        try:
                            attr = attr_class(key)
                            attr.attributes["schema"] = schema
                            for node_attr in node_attrs:
                                ScopeAttributeDeserializer._deserialize(
                                    node_attr, attr, value
                                )
                            node.add_child(attr)
                        except KeyError:
                            pass
                    root.add_child((schema.name, node))
                    return
                except KeyError:
                    return

            # a object
            try:
                node = ScopeObjectNode(schema.name)
                node.attributes["schema"] = schema
                node_data = data[schema.name]

                for child in schema.children:
                    ScopeAttributeDeserializer._deserialize(child, node, node_data)

                root.add_child(node)
            except KeyError:
                return

        raise ValueError("invalid schema definition")

    @property
    def schema(self):
        """
        Get the schema for this attribute
        """
        return self._schema

    def deserialize(self, root: TreeNode, data: dict):
        """
        Abstract method to run the data deserializer
        """
        ScopeAttributeDeserializer._deserialize(self._schema, root, data)


class ScopeAttributeSerializer(ObjectSerializer):
    """
    Deserializer through a dict and convert to a tree
    """

    def __init__(self, schema: TreeNode):
        self._schema = schema

    @property
    def schema(self):
        """
        Get the schema for this attribute
        """
        return self._schema

    def serialize(self, root: TreeNode):
        """
        Abstract method to run the data serializer
        """
        if issubclass(type(root), ScopePropertyNode):
            if not self._schema.validate(root):
                return None
            return {root.name: root.value}

        data = {}
        for child in root.children:

            key = child.name
            if issubclass(type(child), (ScopeObjectNode, ScopeDictNode)):
                value = ScopeAttributeSerializer(self._schema).serialize(child)
            elif issubclass(type(child), ScopePropertyNode):
                value = child.value
            else:
                continue

            data[key] = value

        return data


# The scopes tree should only be one instance,
# most probably we should implement the singleton pattern
# for now we just we do not expose the class on __init__.py
# and we just expose this created instance
scopes = ScopesTree()
