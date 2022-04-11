"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020
"""
import os
from movai_core_shared.exceptions import DoesNotExist, AlreadyExist
from .structures import Struct
from dal.movaidb import MovaiDB
import dal


class Scope(Struct):
    """
    A scope
    """
    permissions = ['create', 'read', 'update', 'delete']

    def __init__(self, scope, name, version, new=False, db='global'):
        self.__dict__['name'] = name
        self.__dict__['scope'] = scope

        # TODO
        # we then need to get this from database!!!!
        dal_dir = os.path.dirname(os.path.realpath(dal.__file__))
        schema_folder = f"file://{dal_dir}/validation/schema"
        template_struct = MovaiDB.API(url=schema_folder)[scope]
        self.__dict__['struct'] = template_struct

        struct = dict()
        struct[name] = template_struct['$name']
        super().__init__(scope, struct, {}, db)

        if new:
            if self.movaidb.exists_by_args(scope=scope, Name=name):
                raise AlreadyExist(
                    'This already exists. To edit dont send the "new" flag')
        else:
            if not self.movaidb.exists_by_args(scope=scope, Name=name):
                raise DoesNotExist(
                    '%s does not exist yet. If you wish to create please use "new=True"' % name)

    def calc_scope_update(self, old_dict, new_dict):
        """ Calc the objects differences and returns list with dict keys to delete/set """
        structure = self.__dict__.get('struct').get('$name')
        return MovaiDB().calc_scope_update(old_dict, new_dict, structure)

    def remove(self, force=True):
        """ Removes Scope """
        result = self.movaidb.unsafe_delete(
            {self.scope: {self.name: '**'}})
        return result

    def remove_partial(self, dict_key):
        """ Remove Scope key """
        result = self.movaidb.unsafe_delete(
            {self.scope: {self.name: dict_key}})
        return result

    def get_dict(self):
        """ Returns the full dictionary of the scope from db"""
        result = self.movaidb.get({self.scope: {self.name: '**'}})
        attrs, lists, hashs = self.get_attributes(self.struct)
        for list_name in lists:
            if list_name not in result[self.scope][self.name]:
                result[self.scope][self.name][list_name] = []
        for hash_name in hashs:
            if hash_name not in result[self.scope][self.name]:
                result[self.scope][self.name][hash_name] = {}

        for attr in attrs:
            if attr not in result[self.scope][self.name]:
                result[self.scope][self.name][attr] = ''

        return result

    def has_scope_permission(self, user, permission) -> bool:
        if not user.has_permission(self.scope, '{prefix}.{permission}'.format(prefix=self.name, permission=permission)):
            if not user.has_permission(self.scope, permission):
                return False
        return True

    def get_value(self, key: str, default: any = False) -> any:
        try:
            value = self.__getattribute__(key)
        except AttributeError:
            value = default

        return value

    @classmethod
    def get_all(cls, db='global'):
        names_list = []
        try:
            for elem in MovaiDB(db).search_by_args(cls.scope, Name='*')[0][cls.scope]:
                names_list.append(elem)
        except KeyError:
            pass  # when does not exist
        return names_list
