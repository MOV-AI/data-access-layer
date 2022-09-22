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

from movai_core_shared.envvars import REST_SCOPES
from movai_core_shared.logger import Log
from .scopestree import scopes


class ACLManager:
    """
    Acl class to manage users and roles permissions
    """

    log = Log.get_logger("ACLManager")
    _DEFAULT_PERMISSIONS = ["create", "read", "update", "delete"]
    _EXECUTE_PERMISSIONS = _DEFAULT_PERMISSIONS + ["execute"]
    _USER_PERMISSIONS = _DEFAULT_PERMISSIONS + ["reset"]
    _SPECIAL_PERMISSIONS_MAP = {
        "Application": _EXECUTE_PERMISSIONS,
        "Callback": _EXECUTE_PERMISSIONS,
        "User": ["read"],
        "InternalUser": _USER_PERMISSIONS,
    }

    def __init__(self, user):
        self.user = user

    def get_acl(self) -> object:
        """Setup ACL for the current user role and user resources"""
        acl = Acl()
        try:
            role = scopes.from_path(self.user.Role, scope="Role")
        except Exception as e:
            self.log.warning("Invalid User Role: {}".format(str(e)))
            return acl

        user_resources = self.user.Resources

        # Setup user role resources
        for (resource_key, resource_value) in role.Resources.items():
            acl.grants(
                {
                    role.ref: {
                        resource_key: resource_value if resource_value else [],
                    },
                }
            )

        # Setup user resources
        for (resource_key, resource_value) in user_resources.items():

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
                resources_permissions[scope] = ACLManager._SPECIAL_PERMISSIONS_MAP[
                    scope
                ]
            except KeyError:
                resources_permissions[scope] = ACLManager._DEFAULT_PERMISSIONS

        # Applications
        resources_permissions["Applications"] = [
            item["ref"] for item in scopes().list_scopes(scope="Application")
        ]

        return resources_permissions

    @staticmethod
    def get_roles() -> Dict:
        """Returns dict with available roles.

        Returns:
            Dict: a dict with all availabe roles in the system.
        """
        # FIXME this may be not the way they intend to use
        return scopes().Role


class NewACLManager(ACLManager):
    def __init__(self, user):
        """This function initializes the object.

        Args:
            user (BaseUser): the user to manage permissions for.
        """
        self.user = user

    def get_acl(self) -> Acl:
        """Setup ACL for the current user role.

        Returns:
            Acl: the object which holds the access list for the user.
        """
        acl = Acl()
        try:
            for role_name in self.user.roles:
                role_obj = ScopesTree().from_path(role_name, scope="Role")

                # Setup user role resources
                for (resource_key, resource_value) in role_obj.Resources.items():
                    acl.grants({role_name: {resource_key: resource_value}})
        except Exception as e:
            self.log.warning("Invalid User Role: {}".format(str(e)))
            return acl

        return acl

    @staticmethod
    def get_resources() -> List:
        """:returns list with available resources"""

        resources = ACLManager.get_resources()
        resources.extend(
            ["Role", "InternalUser", "RemoteUser", "AclObject", "LdapConfig"]
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
                resources_permissions[scope] = NewACLManager._SPECIAL_PERMISSIONS_MAP[
                    scope
                ]
            except KeyError:
                resources_permissions[scope] = NewACLManager._DEFAULT_PERMISSIONS

        # Applications
        resources_permissions["Applications"] = [
            item["ref"] for item in scopes().list_scopes(scope="Application")
        ]

        return resources_permissions
