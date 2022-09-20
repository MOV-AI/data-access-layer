"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020
"""
import binascii
import hashlib
import json
import os
from datetime import datetime
import jwt

from dal.scopes.scope import Scope
from dal.classes.utils.acl import ACLManager
from backend.core.vault import (
    JWT_ACCESS_EXPIRATION_DELTA,
    JWT_REFRESH_EXPIRATION_DELTA,
    JWT_SECRET_KEY,
)

global acl


class User(Scope):
    """User class"""

    scope = "User"

    def __init__(self, name, version="latest", new=False, db="global"):
        super().__init__(scope="User", name=name, version=version, new=new, db=db)

        global acl
        acl_manager = ACLManager(user=self)
        try:
            acl = acl_manager.get_acl()
        except Exception as e:
            pass

    def hash_password(self, password):
        """Hash a password for storing"""
        salt = hashlib.sha256(os.urandom(60)).hexdigest().encode("ascii")
        pwdhash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        pwdhash = binascii.hexlify(pwdhash)
        return (salt + pwdhash).decode("ascii")

    def verify_password(self, provided_password):
        """Verify a stored password against one provided by user"""

        # user does not have a password yet
        if not self.Password:
            return provided_password == ""

        salt = self.Password[:64]
        stored_password = self.Password[64:]
        pwdhash = hashlib.pbkdf2_hmac(
            "sha256", provided_password.encode("utf-8"), salt.encode("ascii"), 100000
        )
        pwdhash = binascii.hexlify(pwdhash).decode("ascii")

        return pwdhash == stored_password

    def get_permissions(self, resource_name: str) -> list:
        """Returns list of user permissions"""
        result = {}
        try:
            global acl
            resource_name = resource_name.lower().capitalize()
            result = acl.which_permissions_all([self.Role], resource_name)
        except Exception as e:
            pass

        return list(result)

    def has_permission(
        self, resource_name: str, permission_name: str, skip_superuser: bool = False
    ) -> bool:
        """Returns permission check"""
        if not skip_superuser and self.Superuser:
            return True

        resource_name = resource_name.lower().capitalize()
        permission_name = permission_name.lower()

        # If request User == ScopeUser then has permission to Read
        if f"{self.name}.read".lower() == permission_name:
            return True

        try:
            global acl
            result = acl.check(self.Role, resource_name, permission_name)
        except Exception:
            result = False

        return result

    def user_permissions(self) -> dict:

        data = {
            "role": self.get_value(key="Role"),
            "all_roles": ACLManager.get_roles(),
            "all_resources_permissions": ACLManager.get_permissions(),
        }

        resources_parsed_data = {}
        for resource, permissions in data["all_resources_permissions"].items():

            role = data["role"]

            has_role_resource = False
            if (
                resource
                in data.get("all_roles", {}).get(role, {}).get("Resources", {}).keys()
            ):
                has_role_resource = data["all_roles"][role]["Resources"][resource]

            user_permissions = []
            for perm in permissions:

                role_perm_value = has_role_resource and (perm in has_role_resource)

                perm_value = self.has_permission(
                    resource_name=resource, permission_name=perm, skip_superuser=True
                )

                perm_dict = {"permission": perm, "value": perm_value}

                if has_role_resource:
                    perm_dict["inherited"] = role_perm_value

                user_permissions.append(perm_dict)

            resources_parsed_data[resource] = user_permissions

        return resources_parsed_data

    def get_supports(self):
        # to_return = []
        # node = Node('server4')
        # for (key, ports) in node.PortsInst.items():
        #     if ports.Template == "MovAI/WidgetAio":
        #         to_return.append(key)
        return []

    def create_id(self):
        """Create"""
        fields = [
            "APIPermission",
            "Layout",
            "name",
            "Type",
            "Version",
            "WidgetPermission",
            "Application",
            "Applications",
        ]

        user_id = json.loads(json.dumps(self.get_dict()[self.scope][self.name]))
        user_id["name"] = self.name
        aux = list(user_id)

        for key in aux:
            if not key in fields:
                del user_id[key]

        user_id["supports"] = self.get_supports()

        return user_id

    def get_token(self):
        """Generate authentication token"""

        message = {
            "sub": "token",
            "iat": int(datetime.now().timestamp()),
            "exp": int((datetime.now() + JWT_ACCESS_EXPIRATION_DELTA).timestamp()),
            "username": self.name,
            "message": self.create_id(),
        }

        token = jwt.encode(message, JWT_SECRET_KEY).decode("utf-8")
        return token

    def get_refresh_token(self):
        """Generate refresh token"""

        message = {
            "sub": "refresh",
            "iat": int(datetime.now().timestamp()),
            "exp": int((datetime.now() + JWT_REFRESH_EXPIRATION_DELTA).timestamp()),
            "username": self.name,
            "message": self.create_id(),
        }

        token = jwt.encode(message, JWT_SECRET_KEY).decode("utf-8")
        return token

    @classmethod
    def verify_token(cls, token):
        """Validate if token is valid"""

        try:
            token_data = jwt.decode(token, JWT_SECRET_KEY, "RS256")
            # ToDo check token data against other stuff.. user still exists, is active etc..
        except jwt.ExpiredSignatureError:
            raise ValueError("Signature expired.")
        except jwt.DecodeError:
            raise ValueError("JWT Error: Token could not be decoded.")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token.")

        return token_data

    @classmethod
    def create(cls, username: str, password: str) -> bool:
        """Create a new user

        args:
            username (str)
            password (str)

        returns:
            obj (User)
        """
        obj = User(username, new=True)
        obj.Label = username
        obj.Password = obj.hash_password(password)

        return obj

    @classmethod
    def reset(
        cls,
        *,
        username: str,
        current_pass: str = None,
        new_pass: str,
        confirm_pass: str,
        validate_current_pass: bool = True,
    ) -> bool:
        """Reset user password

        args:
            - current_pass (str): old password
            - new_pass (str): new password
            - confirm_pass (str): confirm password
            - validate_current_password (bool): confirm current password before setting the new password
        """

        if new_pass != confirm_pass:
            raise ValueError("Confirm password does not match")

        obj = User(username)

        if validate_current_pass and not obj.verify_password(current_pass):
            raise ValueError("Current password is incorrect.")

        obj.Password = obj.hash_password(new_pass)

        return True
