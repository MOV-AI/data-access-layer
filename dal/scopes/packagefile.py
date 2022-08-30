"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Tiago Teixeira  (tiago.teixeira@mov.ai) - 2020

   Package's Files SubModels
"""

import hashlib

from dal.scopes import (ScopeObjectNode, ScopePropertyNode, ScopeNode, PropertyNode)

class PackageFileValue(ScopePropertyNode):
    """ Submodel for Package/File/Value

        will update File's Checksum on set
    """

    @PropertyNode.value.setter
    def value(self, value):
        self._value = value
        # update checksum
        try:
            csum = hashlib.md5(value.encode())
        except AttributeError:
            # bytes has no attribute encode
            csum = hashlib.md5(value)
        self.parent._children['Checksum'].attributes['Checksum'] = csum.hexdigest()

class PackageFileChecksum(ScopePropertyNode):
    """ Submodel for Package/File/Checksum

        Doesn't allow setting it directly
    """

    @property
    def value(self):
        return self.attributes.get('Checksum', self._value)

    @value.setter
    def value(self, value):
        # raising an exception may break backward compatibility
        pass



class PackageFile(ScopeObjectNode):
    """ Submodel for Package/File

        needed to get the actual value from Checksum/File properties
    """

    def __getattribute__(self, name):
        try:
            attr = super().__getattribute__(name)
        except AttributeError:
            attr = super().__getattr__(name)
        if isinstance(attr, (PackageFileChecksum, PackageFileValue)):
            return attr.value
        # else
        return attr

ScopeNode.register_scope_object('schemas/1.0/Package/File', PackageFile)
ScopeNode.register_scope_property('schemas/1.0/Package/File/Value', PackageFileValue)
ScopeNode.register_scope_property('schemas/1.0/Package/File/Checksum', PackageFileChecksum)
