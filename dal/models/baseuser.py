"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Erez Zomer  (erez@mov.ai) - 2022
"""
from __future__ import annotations

from typing import Dict, List, Set, cast
from datetime import datetime

from movai_core_shared.common.utils import create_principal_name
from movai_core_shared.exceptions import (
    InvalidStructure,
    UserAlreadyExist,
    UserDoesNotExist,
    UserPermissionsError,
)
from movai_core_shared.consts import EXECUTE_PERMISSION

from dal.models.scopestree import ScopesTree, scopes
from dal.models.model import Model
from dal.models.acl import NewACLManager
from dal.scopes.application import Application
from dal.models.acl import ResourceType, ApplicationsType


class BaseUser(Model):
    """The BaseUser is the base class for user methods, so that
    RemoteUser and InternalUser can share the same interface.
    """

    max_attr_length = 100
    update_keys = {
        "CommonName",
        "Roles",
        "Email",
        "SuperUser",
        "ReadOnly",
        "SendReport",
    }

    def __init__(self, *args, **kwargs):
        """initilizes the class"""
        super().__init__(*args, **kwargs)
        self._acl = None

    @classmethod
    def create(
        cls,
        domain_name: str,
        account_name: str,
        common_name: str,
        user_type: str,
        roles: list,
        email: str = "",
        super_user: bool = False,
        read_only: bool = False,
        send_report: bool = False,
    ) -> Model:
        """Create a new BaseUser

        Args:
            domain (Str): the name of the domain the base user represents.
            username (str): the name of the base user to create.
            common_name: (str): a display name for the new user.
            type: (str): the type of user (INTERNAL, LDAP, PAM).
            roles: (list): list of roles which are associated with the user.
            email: (str): the email address of the user.
            super_user (bool): a flag which represents if the user
                is super user.
            read_only (bool): a flag which represents if the user has
                read only permissions.
            send_report (bool): a flag which represents if the user is allowed
                to send reports.

        Raises:
            ValueError: if domain_name or account_name aren't of type str.
            ValueError: if account_name is empty string.
            ValueError: if supplied roles are not in a list format.

        returns:
            (BaseUser): a refererance to the BaseUser object that was
            created.
        """
        if not isinstance(domain_name, str) or not isinstance(account_name, str):
            error_msg = "credentials are in unknown format"
            cls.log.error(error_msg)
            raise ValueError(error_msg)
        if account_name == "":
            error_msg = "account_name is invalid"
            cls.log.error(error_msg)
            raise ValueError(error_msg)
        if not isinstance(roles, list):
            error_msg = "roles are not in a list format"
            cls.log.error(error_msg)
            raise ValueError(error_msg)
        if cls.is_exist(domain_name, account_name):
            error_msg = f"The requested user {account_name}@{domain_name} " "already exist"
            raise UserAlreadyExist(error_msg)

        principal_name = create_principal_name(domain_name, account_name)
        user = scopes().create(scope=cls.__name__, ref=principal_name)
        user.domain_name = domain_name
        user.account_name = account_name
        user.common_name = common_name
        user.user_type = user_type
        user.roles = roles
        user.email = email
        user.super_user = super_user
        user.read_only = read_only
        user.send_report = send_report
        user.write()
        msg = f"Successfully created new {cls.__name__} named:" f"{principal_name}"
        cls.log.info(msg)
        return user

    @classmethod
    def remove(cls, domain_name: str, account_name: str) -> None:
        """removes a User record from DB

        Args:
        domain_name (str): the name of the domain which the user belongs to.
        account_name (str): the account name of the user to remove.

        Returns:
            (bool): True if user got removed, False if user was not found.
        """
        principal_name = create_principal_name(domain_name, account_name)
        user = cls.get_user_by_principal_name(principal_name)
        account_name = user.account_name
        scopes().delete(user)
        cls.log.info(f"User named {account_name} has been removed")

    def update(self, user_params: dict):
        """This function updates a corresponding object's attributes.

        Args:
            user_params (dict): a dictionary with the required fields that
                needs an update.

        Raises:
            InvalidStructure: in case non of fields sent are part of the
                InternalUser model.
        """
        if not any(key in user_params.keys() for key in self.update_keys):
            error_msg = f"Json fields aren't found in " f"{self.__class__.__name__} attributes."
            self.log.warning(error_msg)
            raise InvalidStructure(error_msg)
        self.common_name = user_params.get("CommonName", self.common_name)
        self.roles = user_params.get("Roles", self.roles)
        self.email = user_params.get("Email", self.email)
        self.super_user = user_params.get("SuperUser", self.super_user)
        self.read_only = user_params.get("ReadOnly", self.read_only)
        self.send_report = user_params.get("SendReport", self.send_report)
        self.write()

    @property
    def principal_name(self) -> str:
        """build principal name -> "account_name@domain_name

        Args:
        domain_name (str): the name of the domain which the user belongs to.
        account_name (str): the account name of the user.

        Returns:
            str: the name in the form account_name@domain_name
        """
        principal_name = self.account_name + "@" + self.domain_name
        return principal_name

    @property
    def domain_name(self) -> str:
        """returns the domain name of base user.

        Returns:
            (str): the domain name (e.g: "example.com")
        """
        domain_name = str(self.DomainName)
        return domain_name

    @domain_name.setter
    def domain_name(self, name) -> None:
        """returns the domain name of base user.

        Raises:
            (ValueError): if name arg is not a string.
        """
        if not isinstance(name, str):
            raise ValueError("The name agrument must be a string")
        self.DomainName = name

    @property
    def account_name(self) -> str:
        """returns the account name of base user.

        Returns:
            (str): the account name (e.g: "johns")
        """
        account_name = str(self.AccountName)
        return account_name

    @account_name.setter
    def account_name(self, name: str) -> None:
        """sets the account name of base user.

        Raises:
            (ValueError): if name arg is not a string.
        """
        if not isinstance(name, str):
            raise ValueError("The name agrument must be a string")
        self.AccountName = name

    @property
    def common_name(self) -> str:
        """returns the common name of base user.

        Returns:
            (str): the common name (e.g: "John Smith")
        """
        common_name = str(self.CommonName)
        return common_name

    @common_name.setter
    def common_name(self, name: str) -> None:
        """sets the value of the common_name property.

        Raises:
            ValueError: if supplied argument is not in the correct type.
        """
        if not isinstance(name, str):
            raise ValueError("The name agrument must be a string")
        if len(name) > self.max_attr_length:
            raise ValueError(f"The name agrument must be less than " f"{self.max_attr_length}")
        self.CommonName = name

    @property
    def user_type(self) -> str:
        """returns the type of the base user.

        Returns:
            (str): the type (LDAP, PAM)
        """
        user_type = str(self.UserType)
        return user_type

    @user_type.setter
    def user_type(self, user_type) -> None:
        """returns the type of the base user.

        Raises:
            ValueError: if supplied argument is not in the correct type.
        """
        if not isinstance(user_type, str):
            raise ValueError("The name agrument must be a string")
        self.UserType = user_type

    @property
    def email(self) -> str:
        """returns the email of the base user.

        Returns:
            (str): the email address (e.g: "johns@example.com")
        """
        email = str(self.Email)
        return email

    @email.setter
    def email(self, address: str) -> None:
        """sets the value of the email property.

        Raises:
            ValueError: if supplied argument is not in the correct type.
        """
        if not isinstance(address, str):
            raise ValueError("The address agrument must be a string")
        if len(address) > self.max_attr_length:
            raise ValueError(f"The address agrument must be less " f"than {self.max_attr_length}")
        self.Email = address

    @property
    def roles(self) -> List[str]:
        """This funtion returns the corresponding role of the user.

        Returns:
            Union[Model, None]: a Role object or None if it not found.
        """
        roles = []
        if self.Roles is None:
            return None
        try:
            for role in self.Roles:
                roles.append(str(role))
            return roles
        except KeyError:
            return None

    @roles.setter
    def roles(self, roles: list) -> None:
        """sets the value of the email property.

        Raises:
            ValueError: if supplied argument is not in the correct type.
        """
        min_roles_count = 1
        if not isinstance(roles, list):
            error_msg = "The roles agrument type must be a list"
            self.log.error(error_msg)
            raise ValueError(error_msg)
        if len(roles) > self.max_attr_length and len(roles) > min_roles_count:
            error_msg = (
                f"The roles agrument must be greater than"
                f" {min_roles_count} and less than "
                f"{self.max_attr_length}"
            )
            self.log.error(error_msg)
            raise ValueError(error_msg)
        self.Roles = roles

    @property
    def read_only(self) -> bool:
        """returns the read only flag of the base user.

        Returns:
            (bool): the read only flag.
        """
        return bool(self.ReadOnly)

    @read_only.setter
    def read_only(self, value: bool) -> None:
        """sets the value of the read_only property.

        Args:
            value (bool): sets the value of the flag.

        Raises:
            ValueError: if supplied argument is not in the correct type.
        """
        if not isinstance(value, bool):
            raise ValueError("The flag agrument must be of type bool")
        self.ReadOnly = value

    @property
    def super_user(self) -> bool:
        """returns the super user flag of the user.

        Returns:
            (bool): the super user flag.
        """
        return bool(self.SuperUser)

    @super_user.setter
    def super_user(self, value: bool) -> None:
        """sets the value of the super_user property.

        Args:
            value (bool): sets the value of the flag.

        Raises:
            ValueError: if supplied argument is not in the correct type.
        """
        if not isinstance(value, bool):
            raise ValueError("The flag agrument must be of type bool")
        self.SuperUser = value

    @property
    def send_report(self) -> bool:
        """returns the send report flag of the base user.

        Returns:
            (bool): the send report flag.
        """
        return bool(self.SendReport)

    @send_report.setter
    def send_report(self, value: bool) -> None:
        """sets the value of the send_report property.

        Args:
            value (bool): sets the value of the flag.

        Raises:
            ValueError: if supplied argument is not in the correct type.
        """
        if not isinstance(value, bool):
            raise ValueError("The flag agrument must be of type bool")
        self.SendReport = value

    @property
    def last_update(self) -> float:
        """returns the last time object was updated in UTM.

        Returns:
            (timedelta): the last time object was updated in UTM.
        """
        return float(self.LastUpdate)

    @classmethod
    def list_users(cls, domain_name: str) -> List[str]:
        """lists all the base user fora specified domain

        Args:
        domain_name (str): the name of the domain which the user belongs to.

        Returns:
            (list): containing all the BaseUser defined in the system for the\
                requested domain.
        """
        users_names = []
        for scope in scopes().list_scopes(scope=cls.__name__):
            principal_name = str(scope["ref"])
            user = cls.get_user_by_principal_name(principal_name)
            if domain_name == user.domain_name:
                users_names.append(user.account_name)
        cls.log.debug(f"current list of BaseUser records found in the system: {users_names}")
        return users_names

    @classmethod
    def has_any_user_with_role(cls, role_name: str) -> bool:
        """Checks if role is applied to any user

        Args:
        role_name (str): the name of the role being searched.

        Returns:
            (bool): whether any user has the role.
        """
        for scope in scopes().list_scopes(scope=cls.__name__):
            principal_name = str(scope["ref"])
            user = cls.get_user_by_principal_name(principal_name)
            if role_name in user.roles:
                return True
        return False

    @classmethod
    def is_exist(cls, domain_name: str, account_name: str):
        """checks if an object with the specified domain and account name
        already exists.

        Args:
            domain_name (str): the domain name of the user
            account_name (str): the account name of the user

        Returns:
            bool: True if exists, False otherwise.
        """
        return account_name in cls.list_users(domain_name)

    @classmethod
    def get_user_by_principal_name(cls, principal_name: str) -> BaseUser:
        """returns a reference of a User, if not exist returns None

        Args:
        principal_name (str): account@domain format.


        Returns:
            (Model) - the user record with the corresponding account_name
        """
        try:
            user = ScopesTree().from_path(principal_name, scope=cls.__name__)
            return user
        except KeyError:
            msg = f"Failed to find {cls.__name__} named: {principal_name}"
            cls.log.error(msg)
            raise UserDoesNotExist(msg)

    @classmethod
    def get_user_by_name(cls, domain_name: str, account_name: str) -> BaseUser:
        """returns a reference of a User, if not exist returns None

        Args:
        domain_name (str): the name of the domain which the user belongs to.
        account_name (str): the account name of the user.


        Returns:
            (Model) - the user record with the corresponding account_name
        """
        principal_name = create_principal_name(domain_name, account_name)
        return cls.get_user_by_principal_name(principal_name)

    def remove_role(self, role_name: str) -> None:
        """Removes a Role from a specific object

        Args:
            role_name (str): The name of the role to remove.
        """
        self.log.info(f"removing role {role_name} from user {self.ref}")
        tmp_roles = self.roles
        tmp_roles.remove(role_name)
        self.roles = tmp_roles
        self.write()

    @classmethod
    def remove_role_from_all_users(cls, role_name: str) -> Set[str]:
        """Looks for users with the specified Role, if it finds any
        it removes the role from their attributes.

        Args:
            role_name (str): The name of the Role to remove.

        Returns:
            set: containg all the users affected by the change.
        """
        affected_users = set()
        for username in cls.list_objects_names():
            user = cls(username)
            if role_name in user.roles:
                user.remove_role(role_name)
                affected_users.add(username)
        return affected_users

    @staticmethod
    def _current_time() -> float:
        """returns the current time in timestamp format.

        Returns:
            float: a float representing the time delta.
        """
        return int(datetime.now().timestamp())

    def set_acl(self):
        """sets the AClManager as an internal attribute."""
        try:
            acl_manger = NewACLManager(user=self)
            self._acl = acl_manger.get_acl()
        except UserPermissionsError as e:
            self.log.debug(e)

    def get_effective_permissions(self) -> Dict[str, List[str]]:
        if self._acl is None:
            raise Exception("ACL is not set")
        permissions = cast(Dict[str, Set[str]], self._acl.which_any(self.roles))
        converted: Dict[str, List[str]] = {}
        for resource in permissions:
            converted[resource] = list(permissions[resource])
        return converted

    def has_scope_permission(self, user, permission) -> bool:
        """
        check if user has scope permission
        """
        if not user.has_permission(self.scope, f"{self.name}.{permission}"):
            if not user.has_permission(self.scope, permission):
                return False
        return True

    def has_permission(
        self, resource_name: str, permission_name: str, skip_superuser: bool = False
    ) -> bool:
        """Check user permission to a specific resource.

        Args:
            resource_name (str): The name of the resource (capitalize as class
                name e.g: Flow, RemoteUser...)
            permission_name (str): the name of the permission (example: read,
                update)
            skip_superuser (bool, optional): waether to ignore the superuser
                attribute or not. Defaults to False.

        Returns:
            bool: True if the user has permission, False otherwise.
        """
        if not skip_superuser and self.super_user:
            return True

        try:
            self.set_acl()
            for role_name in self.roles:
                if self._acl.check(role_name, resource_name, permission_name):
                    return True
            return False
        except Exception as e:
            self.log.debug(e)
            return False

    def has_permission_callback_execute(self, callback_name: str) -> bool:
        """Check if user has permission to execute a callback.

        TODO Added because frontend apps execute callbacks, remove after migration to endpoints

        """
        if self.has_permission(ResourceType.Callback.value, EXECUTE_PERMISSION):
            return True

        # allow to run callbacks from allowed applications
        for app_name in [app.value for app in ApplicationsType]:
            if self.has_permission(ResourceType.Applications.value, app_name):
                ca = Application(name=app_name)
                if ca.Callbacks and callback_name in ca.Callbacks:
                    return True

        return False
