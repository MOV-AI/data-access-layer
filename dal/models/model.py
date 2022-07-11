"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
from abc import ABC
from importlib import import_module
from dal.scopes.scopestree import (
    ScopeInstanceVersionNode, ScopesTree,
    ScopeNode, scopes)
from dal.data import TreeNode, SchemaPropertyNode
from dal.archive import Archive


class Model(ScopeInstanceVersionNode, ABC):
    """
    The base class of a model in mov.ai, a model is an
    entity with 2 parts defined, the attributes are
    through a schema and methods are python classes
    implementation.

    This class support relations, for that the model
    class must provide a class attribute called
    __RELATIONS__, this attribute is a dictonary with
    the following structure:
    {
        "schemas/<schema version>/<scope>/<attr>" : {
            "schema_version" : <target schema version>,
            "scope" : <target scope>
        }
    }
    """

    __FORWARD_RELATIONS__ = {}

    def __new__(cls, ref_or_path: str, workspace: str = 'global', version: str = '__UNVERSIONED__'):
        return scopes.from_path(ref_or_path, scope=cls.__name__, workspace=workspace, version=version)

    def __init__(self, *args, **kwargs):
        # FIXME workaround not pretty
        try:
            # if it has already been initialized, ignore it
            object.__getattribute__(self, '_parent')
        except AttributeError:
            super().__init__(*args, **kwargs)

    def set_acl(self):
        pass

    @staticmethod
    def _get_relations_list(relations: dict, schema: TreeNode, data: dict, out: set, level: int, depth: int = 0,
                            search_filter: list = None):
        """
        This method is a last resort to search for data relations,
        if the driver fails to return this relations
        this will search recursively throught the data on the objects
        It's always preferable to implement on the persistent driver a
        way to cache relation to make it much
        quick to access this information, use this method as last resources
        """
        try:

            if isinstance(schema, SchemaPropertyNode):

                try:
                    # the relation must exists in the relations dict
                    schema_scope = relations[schema.path]["scope"]
                except KeyError:
                    return

                # get the workspace, scope, ref, version
                workspace, scope, ref, version = ScopesTree.extract_reference(
                    data[schema.name], scope=schema_scope)

                # We add the found related object in the list
                # if we passed a search filter we check if scope
                # is in the list, otherwise the list will be
                # None and trigger a TypeError
                try:
                    if scope in search_filter:
                        out.add(f"{workspace}/{scope}/{ref}/{version}")
                except TypeError:
                    out.add(f"{workspace}/{scope}/{ref}/{version}")

                # If we want to go deeper in the relations, the deeper we search
                # the costly it gets, we should avoid deep searches
                if level < depth:
                    obj = getattr(
                        scopes(workspace=workspace),
                        scope
                    )[ref, version]
                    try:
                        Model._get_relations_list(
                            type(obj).__RELATIONS__, obj.schema, obj.serialize(),
                            out, level + 1, depth, search_filter)
                    except AttributeError:
                        pass
                return

            # it's not a terminal element, keep going deeper in the schema
            if schema.attributes.get("is_hash", True):
                for name in data[schema.name].keys():
                    for child in schema.children:
                        Model._get_relations_list(relations,
                                                  child, data[schema.name][name],
                                                  out, level, depth, search_filter)
                return

            # I don't think we have cases where we reach this code, never the less
            # we need to assume that this might happen
            for child in schema.children:
                Model._get_relations_list(
                    relations, child, data[schema.name], out, level, depth)

        except (KeyError, AttributeError):

            # No schema! check in this node children if any
            for child in schema.children:
                Model._get_relations_list(
                    relations, child, data, out, level, depth)

    @staticmethod
    def register_model_class(scope: str, cls: type):
        """
        Register a model class, this allows for the user to register
        custom models for scopes
        """
        if issubclass(cls, Model):
            try:
                for k, v in cls.__RELATIONS__.items():
                    try:
                        target_scope = v["scope"]
                    except KeyError:
                        continue

                    try:
                        ref_map = Model.__FORWARD_RELATIONS__[target_scope]
                    except KeyError:
                        ref_map = set()
                        Model.__FORWARD_RELATIONS__[target_scope] = ref_map

                    ref_map.add(k)
            except AttributeError:
                pass

        ScopeNode.register_scope_class(scope, cls)

    @staticmethod
    def get_relations_definition(scope: str):
        """
        Return the relations for a scope
        """
        try:
            # Try to load model from our library if not already loaded
            if scope not in ScopeNode.__SCOPES_MAP__:
                import_module("dal.models")
        except ModuleNotFoundError:
            pass

        try:
            cls = ScopeNode.__SCOPES_MAP__[scope]
            return cls.__RELATIONS__
        except (AttributeError, KeyError):
            return {}

    @staticmethod
    def get_forward_relations_definition(scope: str):
        """
        Return the relations for a scope
        """
        try:
            # Try to load model from our library if not already loaded
            if scope not in ScopeNode.__SCOPES_MAP__:
                import_module("dal.models")
        except ModuleNotFoundError:
            pass

        try:
            return Model.__FORWARD_RELATIONS__[scope]
        except KeyError:
            return None

    @staticmethod
    def get_relations(**kwargs):
        """
        Get all related objects for the specified scope, the method first try
        to request the physical layer for this list, if it fails then fallback
        to the default one with is much more expensive and should be avoided
        """
        model = kwargs.get("model", None)
        depth = kwargs.get("depth", 0)
        level = kwargs.get("level", 0)
        search_filter = kwargs.get("search_filter", None)

        if issubclass(type(model), Model):
            workspace = model.workspace
            scope = model.scope
            ref = model.ref
            version = model.version
        else:
            try:
                workspace = kwargs["workspace"]
                scope = kwargs["scope"]
                ref = kwargs["ref"]
                version = kwargs["version"]
            except KeyError as e:
                raise ValueError("missing scope,ref,version or model") from e

        # First we check for the relations in the persisten driver
        workspace = scopes(workspace=workspace)
        relations = workspace.plugin.get_related_objects(**kwargs)

        if isinstance(relations, set):
            return relations

        # Fallback to the default method, depending how deep we are searching
        # it might be critical
        out = set()
        obj = getattr(workspace, scope)[ref, version]
        try:
            Model._get_relations_list(
                type(obj).__RELATIONS__, obj.schema, obj.serialize(), out, level, depth, search_filter)
        except AttributeError:
            pass
        return out

    def relations(self, depth=0, search_filter=None):
        """
        return the current model relations, the method first try to request the
        physical layer for this list, if it fails then fallback to the default
        one with is much more expensive and should be avoided
        """
        return Model.get_relations(model=self, depth=depth, search_filter=search_filter)
