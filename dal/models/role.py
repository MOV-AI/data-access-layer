"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Tiago Teixeira  (tiago.teixeira@mov.ai) - 2020

   Role Model (only of name)
"""
from typing import Dict
from typing import List

from movai_core_shared.consts import (
    ADMIN_ROLE,
    OPERATOR_ROLE,
    DEPLOYER_ROLE,
    CREATE_PERMISSION,
    READ_PERMISSION,
    UPDATE_PERMISSION,
    DELETE_PERMISSION,
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

    _DEFAULT_RESOUCE_PERM = [
        CREATE_PERMISSION,
        READ_PERMISSION,
        UPDATE_PERMISSION,
        DELETE_PERMISSION,
    ]

    ADMIN_RESOURCES = NewACLManager.get_permissions()

    DEPLOYER_RESOURCES = {
        "AclObject": [READ_PERMISSION],
        "Annotation": _DEFAULT_RESOUCE_PERM,
        "Applications": [
            "AdminBoard",
            "FleetBoard",
            "mov-fe-app-ide",
            "mov-fe-app-launcher",
            "mov-fe-app-taskmanager",
        ],
        "Callback": _DEFAULT_RESOUCE_PERM,
        "Configuration": [READ_PERMISSION],
        "EmailsAlertsConfig": [READ_PERMISSION, UPDATE_PERMISSION],
        "EmailsAlertsRecipients": [READ_PERMISSION],
        "Flow": _DEFAULT_RESOUCE_PERM,
        "GraphicScene": _DEFAULT_RESOUCE_PERM,
        "InternalUser": [READ_PERMISSION],
        "Layout": _DEFAULT_RESOUCE_PERM,
        "Node": _DEFAULT_RESOUCE_PERM,
        "Package": _DEFAULT_RESOUCE_PERM,
        "Role": [READ_PERMISSION],
        "SharedDataEntry": _DEFAULT_RESOUCE_PERM,
        "SharedDataTemplate": _DEFAULT_RESOUCE_PERM,
        "TaskEntry": _DEFAULT_RESOUCE_PERM,
        "TaskTemplate": _DEFAULT_RESOUCE_PERM,
    }

    OPERATOR_RESOURCES = {
        "GraphicScene": [READ_PERMISSION],
        "Applications": ["FleetBoard", "mov-fe-app-launcher"],
    }

    @classmethod
    def create(cls, name: str, resources: Dict[str, List[str]]) -> "Role":
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
    def create_role(cls, role: str, resources: Dict[str, List[str]]):
        """Create role"""
        if not Role.is_exist(role):
            cls.create(role, resources)
        else:
            role_obj = Role(role)
            for key, item in resources.items():
                role_obj.Resources[key] = item
                role_obj.write()

    @classmethod
    def create_default_roles(cls):
        """Create default roles: Admin, Deployer, Operator"""
        cls.create_role(ADMIN_ROLE, cls.ADMIN_RESOURCES)
        cls.create_role(DEPLOYER_ROLE, cls.DEPLOYER_RESOURCES)
        cls.create_role(OPERATOR_ROLE, cls.OPERATOR_RESOURCES)

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
            RoleError: if the role cannot be deleted for some reason.
        """
        if name == DEFAULT_ROLE_NAME:
            raise RoleError(f"Deleting the {name} role is forbidden!")
        if RemoteUser.has_any_user_with_role(name) or InternalUser.has_any_user_with_role(name):
            raise RoleError(f"Role {name} is being used, cannot be deleted.")

        try:
            role = Role(name)
            scopes().delete(role)
        except KeyError:
            error_msg = "The requested Role does not exist"
            cls.log.error(error_msg)
            raise RoleDoesNotExist(error_msg)

        AclObject.remove_roles_from_all_objects(name)

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
