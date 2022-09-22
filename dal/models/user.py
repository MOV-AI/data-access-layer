"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Dor Marcous  (Dor@mov.ai) - 2021

   User Model
"""

import hashlib
import os
import binascii
from typing import List, Dict, Union
from datetime import datetime
import jwt

from movai_core_shared.exceptions import UserDoesNotExist

from dal.models.scopestree import ScopesTree, scopes
from dal.models.model import Model
from dal.models.acl import ACLManager

from dal.data.shared.vault import (
    JWT_ACCESS_EXPIRATION_DELTA,
    JWT_REFRESH_EXPIRATION_DELTA,
    JWT_SECRET_KEY,
)


class User(Model):
    """This class represents the user object as record in the DB,
    it handles all operations required for user: authentication,
    token generation and so..
    """

    def __delattr__(self, key):
        # user class disables deleting a feature
        # implemented because of abstract methods
        raise NotImplementedError

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    @property
    def role(self) -> Union[Model, None]:
        """This funtion returns the corresponding role of the user.

        Returns:
            Union[Model, None]: a Role object or None if it not found.
        """
        try:
            return scopes.from_path(self.Role, scope="Role")
        except KeyError:
            return None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._acl = None

    def set_acl(self):
        """sets the AClManager as an internal attribute."""
        try:
            acl_manger = ACLManager(user=self)
            self._acl = acl_manger.get_acl()
        except Exception as e:
            self.log.debug(e)

    @staticmethod
    def hash_password(password: str) -> str:
        """This function uses sha256 algorithm to store a
        password secured.

        Args:
            password (str): the password to hash.

        Returns:
            str: the hash of the password
        """
        salt = hashlib.sha256(os.urandom(60)).hexdigest().encode("ascii")
        pwdhash = binascii.hexlify(
            hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        )
        return (salt + pwdhash).decode("ascii")

    def verify_password(self, password: str) -> bool:
        """Verify a password against an hash

        Args:
            password (str): the password of the user.

        Raises:
            ValueError: if Password attribute is not defined on the user
                object.

        Returns:
            bool: True if password validation succeeds, False otherwise.
        """

        if not self.Password:
            error_msg = "failed to verify password"
            raise ValueError(error_msg)

        salt = self.Password[:64].encode("utf-8")
        hashed = self.Password[64:].encode("utf-8")
        test_hash = binascii.hexlify(
            hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        )
        return hashed == test_hash

    def get_permission(self, resource_name: str) -> List:
        """This function returns a list of resource permissions for a the user.

        Args:
            resource_name (str): the name of the resource which permissions
                are requested.

        Returns:
            List: a list of a given permission for this resource.
        """
        try:
            return list(
                self._acl.which_permissions_all([self.Role], resource_name.capitalize())
            )
        except Exception as e:
            self.log.debug(e)
            return list()

    def has_scope_permission(self, user, permission) -> bool:
        """
        check if user has scope permission
        """
        if not user.has_permission(
            self.scope,
            "{prefix}.{permission}".format(prefix=self.name, permission=permission),
        ):
            if not user.has_permission(self.scope, permission):
                return False
        return True

    def has_permission(
        self, resource_name: str, permission_name: str, skip_superuser: bool = False
    ) -> bool:
        """Check if user has permission"""
        if not skip_superuser and self.Superuser:
            return True

        res_name = resource_name.capitalize()
        perm_name = permission_name.lower()

        if f"{self.ref}.read".lower() == permission_name:
            return True

        try:
            if self._acl is None:
                self.set_acl()
            return self._acl.check(self.Role, res_name, perm_name)
        except Exception as e:
            self.log.debug(e)
            return False

    def user_permissions(self) -> Dict:
        """Get dict of the user permissions"""

        role = self.Role
        all_roles = ACLManager.get_roles()
        all_resources_permissions = ACLManager.get_permissions()

        resources_parsed_data = {}
        for resource, permissions in all_resources_permissions.items():

            has_role_resource = False
            if resource in all_roles.get(role, {}).get("Resources", {}):
                has_role_resource = all_roles[role]["Resources"][resource]

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

    def create_id(self):
        """Create hash id for user"""
        fields = {  # set()
            "APIPermission",
            "Layout",
            "name",
            "Type",
            "Version",
            "WidgetPermission",
            "Application",
            "Applications",
        }

        user_dict = self.serialize()
        user_dict["name"] = self.ref
        to_delete = set.difference(fields, set(user_dict))

        for key in to_delete:
            if key in user_dict.keys():
                del user_dict[key]

        return user_dict

    def _token_gen(self, token_type: str):
        """Generate or refresh authentication token"""
        time_expiration = (
            JWT_ACCESS_EXPIRATION_DELTA
            if token_type == "token"
            else JWT_REFRESH_EXPIRATION_DELTA
        )
        message = {
            "sub": token_type,
            "iat": int(datetime.now().timestamp()),
            "exp": int((datetime.now() + time_expiration).timestamp()),
            "username": self.ref,
            "message": self.create_id(),
        }

        token = jwt.encode(message, JWT_SECRET_KEY).decode("utf-8")
        return token

    def get_token(self):
        """Generate authentication token"""

        return self._token_gen("token")

    def get_refresh_token(self):
        """Generate refresh token"""

        return self._token_gen("refresh")

    @classmethod
    def verify_token(cls, token):
        """This function validates that the token sent by client us valid for
        the corresponding user.

        Args:
            token ([type]): the token to verify

        Raises:
            ValueError: if token has expired
            ValueError: if decoding has failed.
            ValueError: if the token is invalid.

        Returns:
            [type]: the token data after being decoded.
        """

        try:
            token_data = jwt.decode(token, JWT_SECRET_KEY, "RS256")
            # ToDo check token data against other stuff.. user still exists, is active etc..
        except jwt.ExpiredSignatureError as e:
            raise ValueError("Signature expired.") from e
        except jwt.DecodeError as e:
            raise ValueError("JWT Error: Token could not be decoded.") from e
        except jwt.InvalidTokenError as e:
            raise ValueError("Invalid token.") from e

        return token_data

    @classmethod
    def create(cls, username: str, password: str) -> Model:
        """Creates a new user

        args:
            username (str): the name of the user to create (can not be empty)
            password (str): the password for the corresponding user
                (can not be empty).

        returns:
            obj (User): the user object created.
        """
        if not isinstance(username, str) or not isinstance(password, str):
            error_msg = "credentials are in unknown format"
            cls.log.error(error_msg)
            raise ValueError(error_msg)
        if username == "":
            error_msg = "username is invalid"
            cls.log.error(error_msg)
            raise ValueError(error_msg)
        if username == "":
            error_msg = "password is invalid"
            cls.log.error(error_msg)
            raise ValueError(error_msg)

        obj = scopes().create("User", username)
        obj.Password = obj.hash_password(password)
        obj.write()

        return obj

    @classmethod
    def reset(
        cls,
        username: str,
        pw_current: str,
        pw_new: str,
        pw_newc: str,
        validate: bool = True,
    ) -> bool:
        """Resets a user password

        Args:
        pw_current (str): old password.
        pw_new (str): new password.
        pw_newc (str): confirm password.
        validate (bool): confirm current password before setting the
            new password.

        Exceptions:
        ValueError - if new password and confirmed password do not mathc.
        ValueError - if new password is an empty string.
        ValueError - if user does not exist.

        Returns:
            (bool): True if password reset succeeded, False otherwise.
        """

        if pw_new != pw_newc:
            error_msg = "Confirmation password doesn't match"
            cls.log.error(error_msg)
            raise ValueError(error_msg)

        if pw_new == "":
            error_msg = "New password is not valid"
            cls.log.error(error_msg)
            raise ValueError(error_msg)

        try:
            user = scopes().User[username]
        except KeyError as e:
            error_msg = f"user: {username} not exist, password reset failed"
            cls.log.error(error_msg)
            raise ValueError(error_msg) from e

        if validate and not user.verify_password(pw_current):
            error_msg = "Current password validation failed, Could not update"
            " user password"
            cls.log.error(error_msg)
            raise ValueError(error_msg)

        user.Password = user.hash_password(pw_new)
        user.write()

        return True

    @classmethod
    def get_user_by_name(cls, username: str) -> Model:
        """returns a reference of a User, if not exist returns None

        Args:
        username - the name of the User to get a reference for

        Returns:
            (User) - the user record with the corresponding username
        """
        try:
            user = ScopesTree().from_path(username, scope="User")
            return user
        except KeyError:
            error_msg = f"user {username} does not exist"
            cls.log.error(error_msg)
            raise UserDoesNotExist(error_msg)


Model.register_model_class("User", User)
