"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Dict, Generic, List, Mapping, Optional, Tuple, TypeVar, Union
from dal.data.mixins import ChildrenCmpMixin, ValueCmpMixin


VT = TypeVar('VT', bound=Union["TreeNode", "ObjectNode", "PropertyNode"])


class TreeNode(ABC, Generic[VT]):
    """
    Implements an abstract tree node
    """

    def __init__(self):
        self._parent: Optional[VT] = None
        self._sorted = True
        self._attributes = {}

    @staticmethod
    def cached_attribute(method):
        """
        A decorator to set use the self.attributes as
        a cache, when using this decorator the property
        will be cached on the attributes of this node
        """

        def inner(self):
            if not issubclass(type(self), TreeNode):
                raise TypeError("Must be of type TreeNode")

            try:
                return self.attributes[method.__name__]
            except KeyError:
                self.attributes[method.__name__] = method()
                return self.attributes[method.__name__]
        return inner

    @staticmethod
    def _tree_node_sort(node):
        return node.value

    @property
    def attributes(self):
        """
        Schema custom attributes, this is a dict, and should
        be used to store important information in the beahviour
        when processing this node.

        One use case is on the schema tree there is an attribute
        value_on_key that informs the persistent layer that the
        value should also be present when creating the key for
        storing in redis.

        Another use case is the "is_hash", which is used for
        telling what schema objects are DictNodes.
        """
        return self._attributes

    @property
    def parent(self):
        """
        the object reference
        """
        return self._parent

    @property
    def depth(self) -> int:
        """
        return the depth of this node
        """

        if self._parent is None:
            return 0

        return self._parent.depth + 1

    def from_path(self, path):
        """
        get the tree node from a path
        """
        if self.path == path:
            return self

        for child in self.children:
            if (val := child.from_path(path)) is not None:
                return val

        return None

    def get_first_parent(self, node_type: str):
        """
        get the first parent of type node_type:
        """
        if self._parent is None:
            return None

        if self._parent.node_type == node_type:
            return self._parent

        return self._parent.get_first_parent(node_type)

    @property
    def sorted(self):
        """
        children list
        """
        return self._sorted

    @sorted.setter
    def sorted(self, value):
        """
        children list
        """
        self._sorted = value

    @property
    def is_root(self):
        """
        is_root_node
        """
        return self.parent is None

    @property
    @abstractmethod
    def children(self) -> List[VT]:
        """
        children list
        """

    @property
    @abstractmethod
    def count(self) -> int:
        """
        number of children
        """

    @property
    @abstractmethod
    def path(self):
        """
        get the tree path
        """

    @property
    @abstractmethod
    def node_type(self):
        """
        the node type
        """

    def to_path(self):
        """
        get a path representation of this Node
        """
        r = ""
        if self.node_type == "property":
            r = '{}\n'.format(str(self.path))

        for child in self.children:
            r += f"{child.to_path()}"

        return r

    def sort(self):
        """
        sort this tree node
        """
        if not self.sorted:
            return

        for child in self.children:
            child.sort()

        self.children.sort(key=TreeNode._tree_node_sort)

    def __str__(self):
        return self.to_path()


class ListNode(TreeNode[VT], ChildrenCmpMixin):
    """
    Implements a listed tree node
    """

    def __init__(self):
        self._children: List[VT] = []
        super().__init__()

    @property
    def children(self):
        return self._children

    @property
    def count(self):
        return len(self._children)

    def __setitem__(self, key, value):
        raise NotImplementedError

    def __getitem__(self, key: int):
        return self._children[key]

    def __iter__(self):
        return self._children.__iter__()

    def add_child(self, node: VT):
        """
        add child to this node
        """
        if node.parent is self:
            return

        if node.parent is not None:
            raise AttributeError("Remove child first")

        node._parent = self
        self._children.append(node)

    def remove_child(self, node: VT):
        """
        remove child to this node
        """
        if node.parent is not self:
            raise AttributeError("not my child")

        self._children.remove(node)
        node._parent = None


class DictNode(TreeNode[VT], ChildrenCmpMixin, Mapping[str, VT]):
    """
    Implements a dict tree node
    """

    def __init__(self):
        self._children: Dict[str, VT] = {}
        super().__init__()

    @property
    def children(self):
        return self._children.values()

    @property
    def count(self):
        return len(self._children)

    def contains(self, key: str):
        """
        check if dict contains key
        """
        return key in self._children.keys()

    def __setitem__(self, key, value):
        raise NotImplementedError

    def __getitem__(self, key: str):
        return self._children[key]

    def __iter__(self):
        return self._children.__iter__()

    def get(self, key: str, default: Optional[VT] = None):
        """
        return the value of the element with key
        """
        return self._children.get(key, default)

    def add_child(self, node: Union[Tuple[str, VT], VT]):
        """
        add a ne child to this node
        """
        if isinstance(node, tuple):
            try:
                key = node[0]
                node_to_add = node[1]
            except IndexError as e:
                raise AttributeError from e
        elif isinstance(node, (ObjectNode, PropertyNode)):
            key = node.name
            node_to_add = node
        else:
            raise AttributeError("node must be tuple or object/property")

        if node_to_add.parent is self:
            return

        if node_to_add.parent is not None:
            raise AttributeError("Remove child first")

        current_node = self._children.get(key, None)

        if current_node not in (None, node_to_add):
            raise AttributeError("key already taken")

        node_to_add._parent = self
        self._children[key] = node_to_add

    def remove_child(self, node):
        """
        remove child to this node
        """
        if isinstance(node, str):
            try:
                key = node
                node_to_del = self._children[key]
            except KeyError as e:
                raise ValueError from e
        elif isinstance(node, (ObjectNode, PropertyNode)):
            key = node.name
            node_to_del = node
        else:
            raise ValueError("node must be tuple or field")

        if node_to_del.parent is not self:
            raise ValueError("not my child")

        node_to_del._parent = None
        del self._children[key]

    def sort(self):
        if not self.sorted:
            return

        for child in self.children:
            child.sort()

        self._children = OrderedDict(sorted(self._children.items()))

    def items(self):
        """
        access to this dict item
        """
        return self._children.items()

    def keys(self):
        """
        access to this dict keys
        """
        return self._children.keys()

    def values(self):
        """
        acess to this dict values
        """
        return self._children.values()


class ObjectNode(TreeNode[VT], ChildrenCmpMixin):
    """
    Implements a object node
    """

    def __init__(self, name: str):
        super().__init__()
        self._name = name
        self._children: Dict[str, VT] = {}

    @property
    def node_type(self):
        return "object"

    @property
    def name(self):
        """
        the object name
        """
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def path(self):
        """
        get the tree path
        """
        if self.parent is None:
            return self._name

        return f'{self.parent.path}/{self._name}'

    @property
    def children(self):
        return self._children.values()

    @property
    def count(self):
        return len(self._children)

    def __setitem__(self, key, value):
        raise NotImplementedError

    def __delattr__(self, key):
        raise NotImplementedError

    def __getitem__(self, key):
        return self._children[key]

    def __iter__(self):
        return self._children.__iter__()

    def add_child(self, node: Union[Tuple[str, VT], VT]):
        """
        add a child node to the node
        """
        if isinstance(node, tuple):
            try:
                key = node[0]
                node_to_add = node[1]
            except IndexError as e:
                raise AttributeError from e
        elif isinstance(node, (ObjectNode, PropertyNode)):
            key = node.name
            node_to_add = node
        else:
            raise AttributeError("node must be tuple or object/property")

        if node_to_add.parent is self:
            return

        if node_to_add.parent is not None:
            raise AttributeError("Remove child first")

        node_to_add._parent = self
        self._children[key] = node_to_add

    def remove_child(self, node: Union[str, VT]):
        """
        remove child in the node
        """
        if isinstance(node, str):
            try:
                key = node
                node_to_del = self._children[key]
            except KeyError as e:
                raise ValueError from e
        elif isinstance(node, (ObjectNode, PropertyNode)):
            key = node.name
            node_to_del = node
        else:
            raise ValueError("node must be tuple or field")

        if node_to_del.parent is not self:
            raise ValueError("not my child")

        node_to_del._parent = None
        del self._children[key]

    def sort(self):
        if not self.sorted:
            return

        for child in self.children:
            child.sort()

        self._children = OrderedDict(
            sorted(self._children.items()))

    def __setattr__(self, name: str, value: object):

        try:
            node = self.__dict__["_children"][name]
            if not isinstance(node, PropertyNode):
                raise NotImplementedError
            node.value = value
        except KeyError:
            super().__setattr__(name, value)

    def __getattr__(self, name):
        try:
            return self._children[name]
        except KeyError as e:
            raise AttributeError from e

class PropertyNode(TreeNode, ValueCmpMixin):
    """
    Implements a property node
    """

    def __init__(self, name: str, value: str):
        super().__init__()
        self._name = name
        self._value = value

    @property
    def node_type(self):
        return "property"

    @property
    def name(self):
        """
        the property name
        """
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def value(self):
        """
        return the current value
        """
        return self._value

    @value.setter
    def value(self, value):
        # FIXME this should validate (also, for some reason it isn't)
        #if not isinstance(value, self.value_type):
        #    raise ValueError
        self._value = value

    @property
    def value_type(self):
        """
        return the type of the current value
        """
        return type(self._value)

    @property
    def path(self):
        """
        get the tree path
        """
        if self.parent is None:
            return f"{self._name}"

        return f'{self.parent.path}/{self.name}'

    @property
    def children(self):
        return []

    @property
    def count(self):
        return 0


class CallableNode(DictNode):
    """
    Implements an attribute tree node
    """

    def __init__(self):
        self.__dict__["_children"] = {}
        super().__init__()

    @property
    def children(self):
        """
        children list
        """
        return self.__dict__["_children"].values()

    @property
    def count(self):
        """
        number of children
        """
        return len(self.__dict__["_children"])

    def __iter__(self):
        return self.__dict__["_children"].__iter__()

    def __setattr__(self, name: str, value: object):
        try:
            # try to access attribute, case exists, set value
            _ = self.__dict__["_children"][name]
            raise NotImplementedError
        except KeyError:
            super().__setattr__(name, value)

    def __getattr__(self, name):
        try:
            return self._children[name]
        except KeyError as e:
            raise AttributeError(name) from e

    def sort(self):
        if not self.sorted:
            return

        for child in self.children:
            child.sort()

        self.__dict__["_children"] = OrderedDict(
            sorted(self.__dict__["_children"].items()))

    def __call__(self, key: str):
        return self._children[key]
