"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Tiago Teixeira  (tiago.teixeira@mov.ai) - 2020

   Role Model (only of name)
"""
from typing import Dict

from movai_core_shared.consts import (
    ADMIN_ROLE,
    OPERATOR_ROLE,
    DEPLOYER_ROLE,
    READ_PERMISSION,
    UPDATE_PERMISSION,
)
from movai_core_shared.envvars import DEFAULT_ROLE_NAME
from movai_core_shared.exceptions import RoleAlreadyExist, RoleDoesNotExist, RoleError


from dal.models.scopestree import scopes
from dal.models.model import Model
from dal.models.aclobject import AclObject
from dal.models.remoteuser import RemoteUser
from dal.models.internaluser import InternalUser
from dal.models.acl import NewACLManager


class Role(Model):
    """Role Model (only of name)"""

    @classmethod
    def create(cls, name: str, resources: Dict):
        """create a new Role object in DB

        Args:
            name (str): The name of the Role
            resources (Dict): resources permissions map
        Returns:
            Role: The created Role object

        Raises:
            RoleAlreadyExist: in case a Role with that name already exist.
        """
        try:
            role = scopes().create(Role.__name__, name)
            role.Label = name
            role.Resources = resources
            role.write()
            return role
        except ValueError:
            error_msg = "The requested Role already exist"
            cls.log.error(error_msg)
            raise RoleAlreadyExist(error_msg)

    @classmethod
    def create_admin_role(cls):
        """
        creates default admin Role
        """
        resources = NewACLManager.get_permissions()
        if not Role.is_exist(ADMIN_ROLE):
            admin_role = cls.create(ADMIN_ROLE, resources)
        else:
            admin_role = Role(ADMIN_ROLE)
            for key, item in resources.items():
                admin_role.Resources[key] = item
                admin_role.write()

        return admin_role

    @classmethod
    def create_operator_role(cls):
        """
        creates default operator Role
        """
        resources = {
            "EmailsAlertsConfig": [READ_PERMISSION],
            "EmailsAlertsRecipients": [READ_PERMISSION, UPDATE_PERMISSION],
            "Configuration": [READ_PERMISSION],
        }
        resources["Applications"] = ["FleetBoard", "mov-fe-app-launcher"]
        if not Role.is_exist(OPERATOR_ROLE):
            operator_role = cls.create(OPERATOR_ROLE, resources)
        else:
            operator_role = Role(OPERATOR_ROLE)
            for key, item in resources.items():
                operator_role.Resources[key] = item
                operator_role.write()

        return operator_role

    @classmethod
    def create_deployer_role(cls):
        """
        creates default deployer role
        """
        resources = {
            "EmailsAlertsConfig": [READ_PERMISSION, UPDATE_PERMISSION],
            "EmailsAlertsRecipients": [READ_PERMISSION],
            "Configuration": [READ_PERMISSION],
            "InternalUser": [READ_PERMISSION],
            "Role": [READ_PERMISSION],
            "AclObject": [READ_PERMISSION],
        }
        resources["Applications"] = [
            item["ref"] for item in scopes().list_scopes(scope="Application")
        ]
        if not Role.is_exist(DEPLOYER_ROLE):
            deployer_role = cls.create(DEPLOYER_ROLE, resources)
        else:
            deployer_role = Role(DEPLOYER_ROLE)
            for key, item in resources.items():
                deployer_role.Resources[key] = item
                deployer_role.write()

        return deployer_role

    @classmethod
    def create_default_roles(cls):
        """
        will create the default Roles for system
        Admin, Deployer, Operator
        """
        cls.create_admin_role()
        cls.create_deployer_role()
        cls.create_operator_role()

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
        if name == DEFAULT_ROLE_NAME:
            raise RoleError(f"Deleting the {name} role is forbidden!")
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
