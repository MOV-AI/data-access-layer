"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
from os import path
from dal.plugins import PluginManager, Resource
from .tree import TreeNode, DictNode, ObjectNode, PropertyNode, CallableNode
from .serialization import ObjectDeserializer
from .version import VersionNode


class SchemaNode(DictNode):
    """
    Implements a schema node
    """

    def __init__(self, schema: str):
        super().__init__()
        self._schema = schema

    @property
    def node_type(self):
        return "schema"

    @property
    def version(self):
        """
        Return the current version
        """
        try:
            return self.parent.version
        except (TypeError, AttributeError) as e:
            raise ValueError("No version") from e
            

    @property
    def schema(self):
        """
        the schema name
        """
        return self._schema

    @property
    def path(self):
        """
        get the tree path
        """
        if self.parent is None:
            return self._schema

        return f"{self.parent.path}/{self._schema}"


    def validate(self, node: PropertyNode):
        """
        Validate a property Node against this schema
        """
        for child in self.children:
            if child.validate(node):
                return True

        return False


class SchemaVersionNode(VersionNode):
    """
    A version node of schemas
    """


class SchemaObjectNode(ObjectNode):
    """
    Implements a schema object node
    """

    def validate(self, node: PropertyNode):
        """
        Validate a property Node against this schema
        """
        for child in self.children:
            if child.validate(node):
                return True

        return False


class SchemaPropertyNode(PropertyNode):
    """
    Implements a property node
    """
    # Table that maps the default values
    DEFAULT_MAPPING = {
        str: "",
        int: 0,
        float: 0.0,
        dict: {},
        bool: False,
        object: None
    }

    def __init__(self, name: str, value_type: type):
        super().__init__(name, None)
        self.attributes["type"] = value_type

    @property
    def value(self):
        return self.attributes["type"]

    def validate(self, node: PropertyNode):
        """
        Validate a property Node against this schema
        """

        # TODO: We must verify also tbe full path of the node
        # meaning that we might have property with the same name
        # and eventually it will be validated by the wrong validator

        # TODO: Implement custom validators
        return self.name == node.name and isinstance(node.value, self.value)


class SchemasTree(CallableNode):
    """
    Implements a Schema Tree
    """

    @property
    def node_type(self):
        return "schemas"

    @property
    def path(self):
        """
        get the tree path
        """
        if self.parent is None:
            return "schemas"

        return f"{self.parent.path}/schemas"

    def __call__(self, name: str = None, version: str = "1.0"):
        try:
            return self._children[version] if name is None else self._children[version][name]
        except KeyError:
            pass

        schema_file = path.join(
            __SCHEMAS_URL__, version, f"{name}.json")

        if not Resource.exists(schema_file):
            raise FileNotFoundError(
                f"{__SCHEMAS_URL__}/{version}/{name}.json")

        try:
            version_tree = self._children[version]
        except KeyError:
            version_tree = SchemaVersionNode(version)
            self.add_child((version, version_tree))

        schema_data = Resource.read_json(schema_file)
        schema_node = SchemaNode(name)
        version_tree.add_child((name, schema_node))
        SchemaDeserializer(version).deserialize(schema_node, schema_data)

        return schema_node


class SchemaDeserializer(ObjectDeserializer, PluginManager):
    """
    Deserializer through a dict and convert to a tree
    """

    @classmethod
    def plugin_class(cls):
        """
        Get current class plugin
        """
        return "schema"

    __SCHEMAS_MAPPING__ = {
        "1.0": lambda r, s: SchemaDeserializer.get_plugin("version10").deserialize(r, s),
        "2.0": lambda r, s: SchemaDeserializer.get_plugin("version20").deserialize(r, s)
    }

    def __init__(self, version: str = "1.0"):
        self._version = version

    @property
    def version(self):
        """
        Get the version of this schema deserializer
        """
        return self._version

    def deserialize(self, root: TreeNode, data: dict):
        """
        Abstract method to run the data deserializer
        """
        try:
            SchemaDeserializer.__SCHEMAS_MAPPING__[self._version](root, data)
        except KeyError as e:
            raise FileExistsError("Schema does not exists") from e


dir_path = path.dirname(path.realpath(__file__))
__SCHEMAS_URL__ = f"file://{dir_path}/../validation/schema"

# The schemas tree should only be one instance,
# most probably we should implement the singleton pattern
# for now we just we do not expose the class on __init__.py
# and we just expose this created instance
schemas = SchemasTree()
