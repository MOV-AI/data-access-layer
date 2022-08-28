"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Erez Zomer  (erez@mov.ai) - 2022
"""

from dal.models.baseuser import BaseUser
from dal.models.user import User
from .model import Model
from movai_core_shared.core.securepassword import SecurePassword
from movai_core_shared.envvars import DEFAULT_ROLE_NAME
from movai_core_shared.consts import INTERNAL_DOMAIN
from movai_core_shared.exceptions import (
    PasswordError,
    PasswordComplexityError)


class InternalUser(BaseUser):
    """This class represents the user object as record in the DB,
    it handles all operations required for user: authentication,
    token generation and so.
    """
    secure = SecurePassword()
    min_password_length = 8

    @classmethod
    def create(cls,
               account_name: str,
               password: str,
               roles: list,
               common_name: str = '',
               email: str = '',
               super_user: bool = False,
               read_only: bool = False,
               send_report: bool = False) -> BaseUser:

        """Creates a new internal user

        args:
            account_name (str): the name of the user to create
                (can not be empty).
            password (str): the password for the corresponding user
                (can not be empty).

        returns:
            obj (User): the user object created.
        """
        if password == "":
            error_msg = "password is invalid"
            cls.log.error(error_msg)
            raise ValueError(error_msg)

        user = super().create(domain_name=INTERNAL_DOMAIN,
                              account_name=account_name,
                              common_name=common_name,
                              user_type="INTERNAL",
                              roles=roles,
                              email=email,
                              super_user=super_user,
                              read_only=read_only,
                              send_report=send_report)
        try:
            user._validate_password_complexity(password)
            user.hash_password(password)
            user.write()
            return user
        except PasswordError as error:
            user.delete()
            raise error

    @classmethod
    def convert_user(cls, old_user: User) -> Model:
        """This function convert users from the old User type to the new 
        InternalUser format.

        Args:
            old_user (User): The user to convert

        Returns:
            Model: The newly created user.
        """
        new_user_email = str(old_user.Email or '')
        new_user_role = str(old_user.Role or DEFAULT_ROLE_NAME)
        new_user = super().create(domain_name=INTERNAL_DOMAIN,
                                  account_name=old_user.ref,
                                  common_name=old_user.ref,
                                  user_type="INTERNAL",
                                  roles=[new_user_role],
                                  email=new_user_email,
                                  super_user=bool(old_user.Superuser),
                                  read_only=False,
                                  send_report=bool(old_user.SendReport))
        new_user.Password = old_user.Password
        new_user.write()
        
    @classmethod
    def remove(cls, account_name: str) -> None:
        """removes an BaseUser record from DB

        Args:
        domain_name (str): the name of the domain which the user belongs to.
        account_name (str): the account name of the user to remove.
        """
        super().remove(INTERNAL_DOMAIN, account_name)

    @property
    def password(self) -> bytes:
        """returns the value of the password attribute.
        """
        return self.Password

    @password.setter
    def password(self, secret: str) -> None:
        """sets the value of the password attribute.
        """
        self.Password = secret

    def hash_password(self, password: str) -> None:
        """This function uses sha256 algorithm to store a password in
        a secured way.

        Args:
            password (str): the password to hash.

        Returns:
            str: the hash of the password
        """
        self.password = self.secure.create_salted_hash(password)

    def _validate_password_has_changed(self,
                                       current_password: str,
                                       new_password: str) -> None:
        """validates that both passwords match

        Args:
            new_password (str): the new password to set.
            confirm_password (str): confirmation of the password.

        Raises:
            PasswordError: if the password do not match.
        """
        if current_password == new_password:
            error_msg = "new password must not match current password"
            raise PasswordError(error_msg)

    def _validate_confirmation_password(self,
                                        new_password: str,
                                        confirm_password: str) -> None:
        """validates that both passwords match

        Args:
            new_password (str): the new password to set.
            confirm_password (str): confirmation of the password.

        Raises:
            PasswordError: if the password do not match.
        """
        if new_password != confirm_password:
            error_msg = "Confirmation password doesn't match new password"
            raise PasswordError(error_msg)
    
    def _validate_password_complexity(self, password: str) -> None:
        """checks the password against complexity settings.

        Args:
            password (str): the password to check.

        Raises:
            PasswordComplexityError: _if password has failed complexity check.
        """
        if len(password) < self.min_password_length:
            error_msg = "Password must be at least 8 characters long."
            raise PasswordComplexityError(error_msg)

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
        if not isinstance(password, str):
            error_msg = "password must be a string"
            self.log.error(error_msg)
            raise ValueError(error_msg)

        if not self.Password:
            error_msg = "failed to verify password"
            raise PasswordError(error_msg)

        return self.secure.verify_password(password, self.Password)

    def reset_password(self,
                       new_password: str,
                       confirm_password: str) -> None:
        """Resets a user password without requiring current password.

        Args:
        new_password (str): the new password to set for the user.
        confirm_password (str): confirm new password.

        Exceptions:
        ValueError - if supplied password aren't of the correct type (string).
        PasswordError - if new password and confirmed password do not match.
        PasswordComplexityError - if new password does not comply complexity
            requirements.

        Returns:
            (bool): True if password reset succeeded.
        """
        if not isinstance(new_password, str) and\
           not isinstance(confirm_password, str):
            error_msg = "password must be a string"
            self.log.error(error_msg)
            raise ValueError(error_msg)
        self._validate_confirmation_password(new_password, confirm_password)
        self._validate_password_complexity(new_password)
        self.hash_password(new_password)
        self.write()

    def change_password(self,
                        current_password: str,
                        new_password: str,
                        confirm_password: str) -> None:
        """Changes a user password

        Args:
        current_password (str): old password.
        new_password (str): new password.
        confirm_password (str): confirm password.

        Exceptions:
        ValueError - if supplied password aren't in the correct type (string).
        PasswordError - if current password could not be verified.
        PasswordError - if new password and confirmed password do not match.
        PasswordComplexityError - if new password does not comply complexity
            requirements.

        Returns:
            (bool): True if password reset succeeded.
        """
        if not isinstance(current_password, str):
            error_msg = "password must be a string"
            self.log.error(error_msg)
            raise ValueError(error_msg)

        if not self.verify_password(current_password):
            error_msg = "Current password validation failed. "\
                        "Could not change user password"
            self.log.error(error_msg)
            raise PasswordError(error_msg)

        self._validate_password_has_changed(current_password, new_password)
        self.reset_password(new_password, confirm_password)


Model.register_model_class("InternalUser", InternalUser)
