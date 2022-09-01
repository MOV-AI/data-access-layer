"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020
"""
from dal.scopes.scope import Scope

class Role(Scope):

    scope = 'Role'

    def __init__(self, name, version='latest', new=False, db='global'):
        super().__init__(scope="Role", name=name, version=version, new=new, db=db)

    def create_permission(self, resource: str, permission: str) -> bool:
        """ Create new role permission """
        try:
            resource = resource.lower().capitalize()
            permission = permission.lower()

            # Check if Resource exists...
            if resource not in self.Resources:
                raise ValueError("Resource does not exists.")

            new_resources = self.Resources[resource]
            self.Resources[resource] = new_resources.append(permission)
            self.Resources.update(self.Resources)

        except Exception as e:
            return False

        return True

    def delete_permission(self, resource: str, permission: str) -> bool:
        """ Delete role permission """
        try:
            resource = resource.lower().capitalize()
            permission = permission.lower()

            # Check if Resource exists...
            if resource not in self.Resources:
                raise ValueError("Resource does not exists.")

            perms = []
            for perm in set(self.Resources[resource]):
                if perm != permission:
                    perms.append(perm)

            self.Resources[resource] = perms
            self.Resources.update(self.Resources)

        except Exception as e:
            return False

        return True

    @classmethod
    def create(cls, *, name: str, resources: dict) -> bool:
        """ Create a new role """
        try:
            name = name.lower()
            new_role = Role(name, new=True)
            new_role.Label = name
            new_role.Resources.update({
                'User': resources.get('User', []),
                'Flow': resources.get('Flow', []),
                'Callbacks': resources.get('Callbacks', []),
                'Applications': resources.get('Applications', []),
            })
        except Exception as e:
            return False

        return True

    @classmethod
    def update(cls, *, name: str, resources: dict) -> bool:
        """ Reset role data """
        try:
            name = name.lower()
            role = Role(name)
            role.Label = name
            role.Resources.update({
                'User': resources.get('User', []),
                'Flow': resources.get('Flow', []),
                'Callbacks': resources.get('Callbacks', []),
                'Applications': resources.get('Applications', []),
            })
        except Exception as e:
            return False

        return True
