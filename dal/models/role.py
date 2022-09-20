"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Tiago Teixeira  (tiago.teixeira@mov.ai) - 2020

   Role Model (only of name)
"""
from typing import Dict

from movai_core_shared.exceptions import RoleAlreadyExist, RoleDoesNotExist
from movai_core_shared.envvars import DEFAULT_ROLE_NAME

from dal.scopes.scopestree import scopes
from dal.models.model import Model
from dal.models.aclobject import AclObject
from dal.models.remoteuser import RemoteUser
from dal.models.internaluser import InternalUser
from dal.classes.utils.acl import NewACLManager


class Role(Model):
    """Role Model (only of name)"""

    @classmethod
    def create(cls, name: str, resources: Dict) -> None:
        """create a new Role object in DB

        Args:
            name (str): The name of the Role
            resources (Dict): resources permissions map

        Raises:
            RoleAlreadyExist: in case a Role with that name already exist.
        """
        try:
            role = scopes().create(Role.__name__, name)
            role.Label = name
            role.update(resources)
            return role
        except ValueError:
            error_msg = "The requested Role already exist"
            cls.log.error(error_msg)
            raise RoleAlreadyExist(error_msg)

    @classmethod
    def create_default_role(cls):
        if not Role.is_exist(DEFAULT_ROLE_NAME):
            resources = NewACLManager.get_permissions()
            default_role = cls.create(DEFAULT_ROLE_NAME, resources)
        else:
            default_role = Role(DEFAULT_ROLE_NAME)
        return default_role

    def update(self, resources: Dict) -> None:
        """Update role data"""
        self.Resources = resources
        self.write()

    @classmethod
    def remove(cls, name: str) -> None:
        """Removes a Role from DB.

        Args:
            name (str): The name of the Role to remove

        Raises:
            RoleDoesNotExist: In case there is no Role with that name.
        """
        try:
            RemoteUser.remove_role_from_all_users(name)
            InternalUser.remove_role_from_all_users(name)
            AclObject.remove_roles_from_all_objects(name)
            role = Role(name)
            scopes().delete(role)
        except KeyError:
            error_msg = "The requested Role does not exist"
            cls.log.error(error_msg)
            raise RoleDoesNotExist(error_msg)

    @staticmethod
    def list_roles_names() -> list:
        """Retunns a list with all Roles exist in the system.

        Returns:
            list: containing the name of the current Roles.
        """
        roles_names = []
        for obj in scopes().list_scopes(scope="Role"):
            role_name = str(obj["ref"])
            roles_names.append(role_name)
        return roles_names


Model.register_model_class("Role", Role)
