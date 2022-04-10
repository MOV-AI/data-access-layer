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
from dal.models import ACLManager
from movai_core_shared.envvars import (
    JWT_EXPIRATION_DELTA, JWT_REFRESH_EXPIRATION_DELTA,
    JWT_SECRET_KEY
)
from dal.scopes import scopes
from .model import Model
from movai_core_shared.logger import Log

# declare logger
logger = Log.get_logger('User')


class User(Model):
    """ The User Model """

    def __delattr__(self, key):
        # user class disables deleting a feature
        # implemented because of abstract methods
        raise NotImplementedError

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    @property
    def role(self) -> Union[Model, None]:
        """ get the role model """
        try:
            return scopes.from_path(self.Role, scope='Role')
        except KeyError:
            return None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._acl = None

    def set_acl(self):
        try:
            acl_manger = ACLManager(user=self)
            self._acl = acl_manger.get_acl()
        except Exception as e:
            logger.debug(e)

    @staticmethod
    def hash_password(password: str) -> str:
        """ Hash a password for safe keeping """
        salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
        pwdhash = binascii.hexlify(
            hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        )
        return (salt + pwdhash).decode('ascii')

    def verify_password(self, password: str) -> bool:
        """ Verify a password against an hash """

        if not self.Password:
            return password == ''

        salt = self.Password[:64].encode('utf-8')
        hashed = self.Password[64:].encode('utf-8')
        test_hash = binascii.hexlify(
            hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        )
        return hashed == test_hash

    def get_permission(self, resource_name: str) -> List:
        """ Get list of user permissions """
        try:
            return list(
                self._acl.which_permissions_all([self.Role], resource_name.capitalize())
            )
        except Exception as e:
            logger.debug(e)
            return list()

    def has_scope_permission(self, user, permission) -> bool:
        """
        check if user has scope permission
        """
        if not user.has_permission(self.scope, '{prefix}.{permission}'.format(prefix=self.name, permission=permission)):
            if not user.has_permission(self.scope, permission):
                return False
        return True

    def has_permission(self, resource_name: str, permission_name: str, skip_superuser: bool = False) -> bool:
        """ Check if user has permission """
        if not skip_superuser and self.Superuser:
            return True

        res_name = resource_name.capitalize()
        perm_name = permission_name.lower()

        # if resources is User
        if f"{self.ref}.read".lower() == permission_name:
            return True

        try:
            if self._acl is None:
                self.set_acl()
            return self._acl.check(self.Role, res_name, perm_name)
        except Exception as e:
            logger.debug(e)
            return False

    def user_permissions(self) -> Dict:
        """ Get dict of the user permissions """

        role = self.Role
        all_roles = ACLManager.get_roles()
        all_resources_permissions = ACLManager.get_permissions()

        resources_parsed_data = {}
        for resource, permissions in all_resources_permissions.items():

            has_role_resource = False
            if resource in all_roles.get(role, {}).get('Resources', {}):
                has_role_resource = all_roles[role]['Resources'][resource]

            user_permissions = []
            for perm in permissions:

                role_perm_value = has_role_resource and (
                        perm in has_role_resource)

                perm_value = self.has_permission(
                    resource_name=resource,
                    permission_name=perm,
                    skip_superuser=True
                )

                perm_dict = {
                    'permission': perm,
                    'value': perm_value
                }

                if has_role_resource:
                    perm_dict['inherited'] = role_perm_value

                user_permissions.append(perm_dict)

            resources_parsed_data[resource] = user_permissions

        return resources_parsed_data

    def create_id(self):
        """ Create hash id for user """
        fields = {  # set()
            'APIPermission',
            'Layout',
            'name',
            'Type',
            'Version',
            'WidgetPermission',
            'Application',
            'Applications'
        }

        user_dict = self.serialize()
        user_dict['name'] = self.ref
        to_delete = set.difference(fields, set(user_dict))

        for key in to_delete:
            if key in user_dict.keys():
                del user_dict[key]

        return user_dict

    def _token_gen(self, token_type: str):
        """ Generate or refresh authentication token """
        time_expiration = JWT_EXPIRATION_DELTA if token_type == 'token' else JWT_REFRESH_EXPIRATION_DELTA
        message = {
            'sub': token_type,
            'iat': int(datetime.now().timestamp()),
            'exp': int((datetime.now() + time_expiration).timestamp()),
            'username': self.ref,
            'message': self.create_id(),
        }

        token = jwt.encode(message, JWT_SECRET_KEY).decode('utf-8')
        return token

    def get_token(self):
        """ Generate authentication token """

        return self._token_gen('token')

    def get_refresh_token(self):
        """ Generate refresh token """

        return self._token_gen('refresh')

    @classmethod
    def verify_token(cls, token):
        """Validate if token is valid"""

        try:
            token_data = jwt.decode(token, JWT_SECRET_KEY, 'RS256')
            # ToDo check token data against other stuff.. user still exists, is active etc..
        except jwt.ExpiredSignatureError as e:
            raise ValueError('Signature expired.') from e
        except jwt.DecodeError as e:
            raise ValueError('JWT Error: Token could not be decoded.') from e
        except jwt.InvalidTokenError as e:
            raise ValueError('Invalid token.') from e

        return token_data

    @staticmethod
    def create(username: str, password: str) -> Model:
        """ Create a new user

            args:
                username (str)
                password (str)

            returns:
                obj (User)
        """
        obj = scopes().create('User', username)
        obj.Password = obj.hash_password(password)
        obj.write()

        return obj

    @staticmethod
    def reset(username: str, pw_current: str, pw_new: str, pw_newc: str, validate: bool = True) -> bool:
        """ Reset user password

            args:
                - pw_current (str): old password
                - pw_new (str): new password
                - pw_newc (str): confirm password
                - validate (bool): confirm current password before setting the new password
        """

        if pw_new != pw_newc:
            raise ValueError("Confirmation password doesn't match")

        try:
            user = scopes().User[username]
        except KeyError as e:
            raise ValueError("Could not update user password") from e

        if validate and not user.verify_password(pw_current):
            raise ValueError("Could not update user password")

        user.Password = user.hash_password(pw_new)
        user.write()

        return True


Model.register_model_class('User', User)
