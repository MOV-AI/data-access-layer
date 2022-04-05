"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires (alexandre.pires@mov.ai) - 2020
"""
from abc import ABC, abstractmethod
from .tree import ObjectNode, PropertyNode, TreeNode


class SerializableObject(ABC):
    """
    A serializable object should implement this inteface
    """
    @abstractmethod
    def serialize(self, **kwargs):
        """
        for internal use only, this method is not supposed to be called by the user
        """


class ObjectDeserializer(ABC):
    """
    A base data deserializer
    """

    @abstractmethod
    def deserialize(self, root: TreeNode, data: dict):
        """
        Abstract method to run the data deserializer
        """
        raise NotImplementedError


class ObjectSerializer(ABC):
    """
    A base data serializer
    """

    @abstractmethod
    def serialize(self, root: TreeNode):
        """
        Abstract method to run the data deserializer
        """
        raise NotImplementedError


class SimpleDeserializer(ObjectDeserializer):
    """
    Deserializer through a dict and convert to a tree
    """

    def deserialize(self, root: TreeNode, data: dict):
        """
        Abstract method to run the data deserializer
        """
        for key, value in data.items():

            if isinstance(value, dict):
                node = ObjectNode(key)
                SimpleDeserializer().deserialize(node, value)
            else:
                node = PropertyNode(key, value)

            root.add_child(node)


class SimpleSerializer(ObjectSerializer):
    """
    Serializer through a tree and convert to a dict
    """

    def serialize(self, root: TreeNode):
        """
        Abstract method to run the data serializer
        """
        data = {}
        for child in root.children:

            if issubclass(type(child), ObjectNode):
                key = child.name
                value = SimpleSerializer().serialize(child)
            elif issubclass(type(child), PropertyNode):
                key = child.name
                value = child.value
            else:
                continue

            data[key] = value

        return data
