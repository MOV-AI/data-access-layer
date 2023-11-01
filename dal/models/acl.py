"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Telmo Martinho (telmo.martinho@mov.ai) - 2020
"""

from typing import List, Dict

from miracle import Acl

from movai_core_shared.consts import (
    READ_PERMISSION,
    UPDATE_PERMISSION,
    CREATE_PERMISSION,
    DELETE_PERMISSION,
    EXECUTE_PERMISSION,
    RESET_PERMISSION,
)
from movai_core_shared.envvars import REST_SCOPES
from movai_core_shared.logger import Log
from dal.models.scopestree import scopes
import dal.new_models


def Role():
    import dal.new_models.role
    return dal.new_models.role.Role


class ACLManager:
    """
    Acl class to manage users and roles permissions
    """

    log = Log.get_logger("ACLManager")
    _DEFAULT_PERMISSIONS = [CREATE_PERMISSION, READ_PERMISSION, UPDATE_PERMISSION, DELETE_PERMISSION]
    _EXECUTE_PERMISSIONS = _DEFAULT_PERMISSIONS + [EXECUTE_PERMISSION]
    _USER_PERMISSIONS = _DEFAULT_PERMISSIONS + [RESET_PERMISSION]
    _SPECIAL_PERMISSIONS_MAP = {
        "Application": _EXECUTE_PERMISSIONS,
        "Callback": _EXECUTE_PERMISSIONS,
        "User": ["read"],
        "InternalUser": _USER_PERMISSIONS,
        "EmailsAlertsConfig": [READ_PERMISSION, UPDATE_PERMISSION],
        "EmailsAlertsRecipients": [READ_PERMISSION, UPDATE_PERMISSION],
    }

    def __init__(self, user):
        """This function initializes the object.

        Args:
            user (BaseUser): the user to manage permissions for.
        """
        self.user = user

    def get_acl(self) -> object:
        """Setup ACL for the current user role and user resources"""
        acl = Acl()
        try:
            role = Role()(self.user.Roles)
        except Exception as e:
            self.log.warning("Invalid User Role: {}".format(str(e)))
            return acl

        user_resources = self.user.Resources

        # Setup user role resources
        for resource_key, resource_value in role.Resources.items():
            acl.grants(
                {
                    role.ref: {
                        resource_key: resource_value if resource_value else [],
                    },
                }
            )

        # Setup user resources
        for resource_key, resource_value in user_resources.items():
            if resource_key[:1] == "-":
                acl.revoke_all(role.ref, resource_key[1:])
                continue

            for perm in resource_value:
                if perm[:1] == "-":
                    acl.revoke(role.ref, resource_key, perm[1:])
                elif perm[:1] == "+":
                    acl.grant(role.ref, resource_key, perm[1:])
                else:
                    acl.grant(role.ref, resource_key, perm)

        return acl

    @staticmethod
    def get_resources() -> List:
        """:returns list with available resources"""

        resources = REST_SCOPES.strip("()").split("|")

        # FIXME find a way to list scopes

        # Append 'Applications' resource
        resources.append("Applications")

        return resources

    @staticmethod
    def get_permissions() -> Dict:
        """:returns dict with available resources & permissions"""

        resources = ACLManager.get_resources()
        resources_permissions = {}
        # Scopes
        for scope in resources:
            try:
                resources_permissions[scope] = ACLManager._SPECIAL_PERMISSIONS_MAP[scope]
            except KeyError:
                resources_permissions[scope] = ACLManager._DEFAULT_PERMISSIONS

        # Applications
        resources_permissions["Applications"] = [
            item for _, item, _ in dal.new_models.Application.model_fetch_ids()
        ]

        return resources_permissions

    @staticmethod
    def get_roles() -> Dict:
        """Returns dict with available roles.

        Returns:
            Dict: a dict with all availabe roles in the system.
        """
        return {role.name: role.model_dump() for role in Role().select(project="Roles")}


class NewACLManager(ACLManager):
    """This class is Replacing ACLManger for BaseUser objects."""

    def get_acl(self) -> Acl:
        """Setup ACL for the current user role.

        Returns:
            Acl: the object which holds the access list for the user.
        """
        acl = Acl()
        try:
            for role_name in self.user.Roles:
                role_obj = Role()(role_name)
                for resource_key, resource_value in role_obj.Resources.items():
                    acl.grants({role_name: {resource_key: resource_value}})
        except AttributeError as e:
            self.log.warning(str(e))
        except Exception as e:
            self.log.warning("Invalid User Role: {}".format(str(e)))
            return acl

        return acl

    @staticmethod
    def get_resources() -> List:
        """:returns list with available resources"""

        resources = ACLManager.get_resources()
        resources.extend(
            [
                "Role",
                "InternalUser",
                "RemoteUser",
                "AclObject",
                "LdapConfig",
                "EmailsAlertsConfig",
                "EmailsAlertsRecipients",
            ]
        )
        return resources

    @staticmethod
    def get_permissions() -> Dict:
        """:returns dict with available resources & permissions"""

        resources = NewACLManager.get_resources()
        resources_permissions = {}
        # Scopes
        for scope in resources:
            try:
                resources_permissions[scope] = NewACLManager._SPECIAL_PERMISSIONS_MAP[scope]
            except KeyError:
                resources_permissions[scope] = NewACLManager._DEFAULT_PERMISSIONS

        # Applications
        resources_permissions["Applications"] = [
            item for _, item, _ in dal.new_models.Application.model_fetch_ids()
        ]

        return resources_permissions
