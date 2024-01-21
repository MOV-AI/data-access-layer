"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2023
   - Erez Zomer (erez@mov.ai) - 2023
"""
from typing import Dict, List

from movai_core_shared.exceptions import RoleAlreadyExist, RoleDoesNotExist, RoleError
from movai_core_shared.consts import (
    ADMIN_ROLE,
    OPERATOR_ROLE,
    DEPLOYER_ROLE,
    READ_PERMISSION,
    UPDATE_PERMISSION,
)
from movai_core_shared.envvars import DEFAULT_ROLE_NAME

from dal.models.acl import NewACLManager
from dal.models.aclobject import AclObject
from dal.models.internaluser import InternalUser
from dal.scopes.application import Application
from dal.new_models.base import MovaiBaseModel


class Role(MovaiBaseModel):
    """A class that implements the Role model."""

    Resources: Dict[str, List[str]] = {}

    def __init___(self, *args, **kwargs) -> None:
        super().__init__(*args, project="Roles", **kwargs)

    @classmethod
    def _original_keys(cls) -> list:
        """keys that are originally defined part of the model

        Returns:
            List[str]: list including the original keys
        """
        return super()._original_keys() + ["Resources"]

    @classmethod
    def create(cls, name: str, resources: Dict) -> "Role":
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
            role = cls(name)
            role.Label = name
            role.Resources = resources
            role.save(project="Roles")
            return role
        except ValueError:
            error_msg = "The requested Role already exist"
            self._logger.error(error_msg)
            raise RoleAlreadyExist(error_msg)

    @classmethod
    def create_admin_role(cls):
        """
        creates default admin Role
        """
        admin_role = cls.create(ADMIN_ROLE, NewACLManager.get_permissions())

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
            "Applications": ["FleetBoard", "mov-fe-app-launcher"],
        }
        operator_role = cls.create(OPERATOR_ROLE, resources)

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
        resources["Applications"] = [app.name for app in Application.get_model_objects()]

        deployer_role = cls.create(DEPLOYER_ROLE, resources)

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
        self.save(project="Roles")

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
            # TODO check this
            # RemoteUser.remove_role_from_all_users(name)
            InternalUser.remove_role_from_all_users(name)
            AclObject.remove_roles_from_all_objects(name)
            role = Role(name, project="Roles")
            role.delete()
        except KeyError:
            error_msg = "The requested Role does not exist"
            self._logger.error(error_msg)
            raise RoleDoesNotExist(error_msg)

    @staticmethod
    def list_roles_names() -> list:
        """Retunns a list with all Roles exist in the system.

        Returns:
            list: containing the name of the current Roles.
        """

        return [id for _, id, _ in Role.get_model_names(project="Roles")]
