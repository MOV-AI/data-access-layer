from typing import List
from datetime import datetime
from movai_core_shared.utils.principal_name import create_principal_name
from movai_core_shared.exceptions import (
    AclObjectAlreadyExist,
    AclObjectDoesNotExist,
    AclObjectError,
    AclObjectIDMismatch,
    AclObjectInvalidAttribute)

from .model import Model
from .scopestree import ScopesTree, scopes


class AclObject(Model):
    """This class represents an access list for remote users.
    Each record in the access list is actually a user that is allowed
    to login.
    The name of each record is in the form "account_name@domain_name".
    """
    max_attr_length = 100
    mandatory_parameters = {'DomainName',
                            'AccountName',
                            'CommonName',
                            'ID',
                            'Roles'}

    @classmethod
    def create(cls,
               domain_name: str,
               account_name: str,
               common_name: str,
               object_type: str,
               identifier: str,
               roles: list,
               read_only: bool = False,
               super_user: bool = False,
               send_report: bool = False) -> Model:
        """creates a new user entry in the access list, if one already exists it
        update the current record and returns a refernece to it.

        Args:
        domain_name (str): the name of the domain which the user belongs to.
        roles - a list of roles to associate the user with.
        super_user - denotes if the user has super user permissions.
        read_only - denotes if the user has a read only access.

        Raises:
            AclObjectAlreadyExist - if an object with the same name already
                exist in DB.

        Returns:
            (AclObject): An AclObject object.
        """
        try:
            principal_name = create_principal_name(domain_name, account_name)
            acl_object = scopes().create(scope='AclObject', ref=principal_name)
            acl_object.DomainName = domain_name
            acl_object.AccountName = account_name
            acl_object.common_name = common_name
            acl_object.ObjectType = object_type
            acl_object.ID = identifier
            acl_object.Roles = roles
            acl_object.ReadOnly = read_only
            acl_object.SuperUser = super_user
            acl_object.SendReport = send_report
            acl_object._update_time()
            acl_object.write()
            return acl_object
        except ValueError:
            error_msg = f"The AclObject named {principal_name} "\
                        f"is already exist in DB"
            cls.log.error(error_msg)
            raise AclObjectAlreadyExist(error_msg)

    @classmethod
    def remove(cls, domain_name: str, account_name: str, id: str):
        """removes an AclObject recored from access list

        Args:
        domain_name (str): the name of the domain which the user belongs to.
        account_name (str): the account name of the user to remove.

        Returns:
            bool: True if user got removed, False if user was not found.
        """
        obj = cls.get_object_by_name(domain_name, account_name)
        if id == obj.ID:
            scopes().delete(obj)
            cls.log.info(f"Successfully removed {cls.__name__}:"
                         f"{obj.principal_name}")
        else:
            error_msg = f"Failed to remove {obj.principal_name}, the "\
                f"supplied id does not match object's id"
            cls.log.error(error_msg)
            raise AclObjectIDMismatch(error_msg)

    def update(self, obj_dict: dict) -> None:
        """This function sets attributes for an AclObject

        Args:
            roles (str): the roles of the object
            read_only (bool, optional): specify if the object has read only
                permissions. Defaults to False.
            super_user (bool, optional): specify if the object has super user
                permissions. Defaults to False.
            send_report (bool, optional): specify if the object can send
                reports. Defaults to False.

        Raises:
            AclObjectIDMismatch - if AclObject update has failed.
        """
        if obj_dict['ID'] == self.ID:
            self.common_name = obj_dict.get('CommonName', self.common_name)
            self.roles = obj_dict.get('Roles', self.roles)
            self.read_only = obj_dict.get('ReadOnly', self.read_only)
            self.super_user = obj_dict.get('SuperUser', self.super_user)
            self.send_report = obj_dict.get('SendReport', self.send_report)
            self._update_time()
            self.write()
            self.log.info(f"Successfully updated {self.principal_name}")
        else:
            error_msg = f"Failed to update {self.principal_name}, the "\
                f"supplied id does not match object's id"
            self.log.warning(error_msg)
            raise AclObjectIDMismatch(error_msg)

    def _update_time(self) -> None:
        self.LastUpdate = int(datetime.now().timestamp())

    @classmethod
    def get_account_name(cls, principal_name: str) -> str:
        """extract account name from principal name.

        Args:
        principal_name (str): the name in the form "account_name@domain_name".

        Returns:
            str: the account name (e.g: "johns")
        """
        if '@' in principal_name:
            account_name = principal_name.split('@')[0]
            return account_name
        else:
            cls.log.error("principlal name doesn't contain the seperator"
                         "character @")

    @classmethod
    def get_domain_name(cls, principal_name: str) -> str:
        """extract domain name from principal.

        Args:
        principal_name (str): the name in the form "account_name@domain_name".

        Returns:
            str: the domain name (e.g: "example.com")
        """
        if '@' in principal_name:
            domain_name = principal_name.split('@')[1]
            return domain_name
        else:
            cls.log.error("principlal name doesn't contain the seperator"
                         "character @")

    @classmethod
    def get_object_by_name(cls,
                           domain_name: str,
                           account_name: str) -> Model:
        """Looks for an AclObject record with the specified name and returns
        a reference of it.

        Args:
        domain_name (str): the name of the domain which the object belongs to.
        account_name (str): the name of the AclObject to get a reference for.

        Returns:
            AclGRoup: an object represents the the AclObject record, None
            otherwise.
        """
        principal_name = create_principal_name(domain_name, account_name)
        try:
            obj = ScopesTree().from_path(principal_name, scope='AclObject')
            return obj
        except KeyError:
            error_msg = f"Failed to find acl object {principal_name},"\
                        f" object does not exist"
            cls.log.error(error_msg)
            raise AclObjectDoesNotExist(error_msg)

    @classmethod
    def list_object_names(cls, domain_name: str, object_type: str) -> list:
        """lists all the object of specific type in a specified domain.

        Args:
        domain_name (str): the name of the domain which the user belongs to.
        type (str): the type of the object (user or group)

        Returns:
            list: containing all the objects conforms to domain and type.
        """
        allowed_objects_names = []
        for obj in scopes().list_scopes(scope='AclObject'):
            account_name = AclObject.get_account_name(obj['ref'])
            acl_obj = AclObject.get_object_by_name(domain_name, account_name)
            if domain_name == acl_obj.domain_name and \
               object_type == acl_obj.object_type:
                allowed_objects_names.append(account_name)
        cls.log.debug(f"Current AclObjects defined in access list:"
                     f"{allowed_objects_names}")
        return allowed_objects_names

    def display_info(self) -> None:
        """display all the user attributes as defined in AclObject scheme.
        """
        try:
            self.log.info(f"ref: {self.ref}")
            self.log.info(f"DomainName: {self.DomainName}")
            self.log.info(f"AccountName: {self.AccountName}")
            self.log.info(f"CommonName: {self.CommonName}")
            self.log.info(f"Type: {self.Type}")
            self.log.info(f"ID: {self.ID}")
            self.log.info(f"Roles: {self.Roles}")
            self.log.info(f"ReadOnly: {self.ReadOnly}")
            self.log.info(f"SuperUser: {self.SuperUser}")
            self.log.info(f"SendReport: {self.SendReport}")
            self.log.info(f"LastUpdate: {self.LastUpdate}")
        except AttributeError as a:
            self.log.error(a)

    def convert_object_to_dict(self) -> dict:
        """display all the user attributes as defined in AclObject scheme.
        """
        object_info = {}
        try:
            object_info["name"] = self.ref
            object_info["domain_name"] = self.DomainName
            object_info["account_name"] = self.AccountName
            object_info["common_name"] = self.CommonName
            object_info["type"] = self.Type
            object_info["id"] = self.ID
            object_info["roles"] = self.Roles
            object_info["read_only"] = self.ReadOnly
            object_info["super_user"] = self.SuperUser
            object_info["send_report"] = self.SendReport
            object_info["last_update"] = self.LastUpdate
            return object_info
        except AttributeError as a:
            error_msg = f"{a} attribute is not defined in AclObject scheme"
            self.log.error(error_msg)
            raise AclObjectInvalidAttribute(error_msg)

    @classmethod
    def _is_exist(cls, principal_name: str) -> bool:
        """This funtion checks if an object with a specific name already exist.

        Args:
            object_name (_type_): The ref name of the object to check.

        Returns:
            bool: True if exist, False otherwise.
        """
        current_objects = []
        for obj in scopes().list_scopes(scope='AclObject'):
            current_objects.append(obj['ref'])
        return principal_name in current_objects

    @classmethod
    def is_exist(cls, domain_name: str, account_name) -> bool:
        """This funtion checks if an object with a specific name already exist.

        Args:
            object_name (_type_): The ref name of the object to check.

        Returns:
            bool: True if exist, False otherwise.
        """
        principal_name = create_principal_name(domain_name, account_name)
        return cls._is_exist(principal_name)

    @classmethod
    def check_parameters(cls, obj_dict: dict):
        """This functions validates that a dictionary contain all required fields
        to create an AclObject.

        Args:
            obj_dict (dict): the dictionary containing all the parameters.

        Raises:
            AclObjectError: if one of the required parameters is missing.
        """
        for parameter in cls.mandatory_parameters:
            if parameter not in obj_dict:
                error_msg = f"The key: \"{parameter}\" is missing in the "\
                            f"supplied dictionary"
                cls.log.error(error_msg)
                raise AclObjectError(error_msg)

    @property
    def principal_name(self) -> str:
        """build principal name -> "account_name@domain_name

        Args:
        domain_name (str): the name of the domain which the user belongs to.
        account_name (str): the account name of the user.

        Returns:
            str: the name in the form account_name@domain_name
        """
        principal_name = self.account_name + '@' + self.domain_name
        return principal_name

    @property
    def domain_name(self) -> str:
        """returns the domain name of AclObject.

        Returns:
            (str): the domain name (e.g: "example.com")
        """
        domain_name = str(self.DomainName)
        return domain_name

    @property
    def account_name(self) -> str:
        """returns the account name of AclObject.

        Returns:
            (str): the account name (e.g: "johns")
        """
        account_name = str(self.AccountName)
        return account_name

    @property
    def common_name(self) -> str:
        """returns the common name of AclObject.

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
            raise ValueError(f"The name agrument must be less than "
                             f"{self.max_attr_length}")
        self.CommonName = name

    @property
    def object_type(self) -> str:
        """returns the object type of AclObject.

        Returns:
            (str): the object type (e.g: user)
        """
        object_type = str(self.ObjectType)
        return object_type

    @property
    def identifier(self) -> str:
        """returns the identifier of the AclObject.

        Returns:
            (str): the identifier (e.g: "s-234-34563...")
        """
        Identifier = str(self.ID)
        return Identifier

    @property
    def roles(self) -> List[str]:
        """This funtion returns the corresponding role of the user.

        Returns:
            List[Model, None]: a Role object or None if it not found.
        """
        roles = []
        try:
            for role in self.Roles:
                roles.append(str(role))
            return roles
        except KeyError:
            return None

    @roles.setter
    def roles(self, roles: list) -> None:
        """sets the value of the roles property.

        Raises:
            ValueError: if supplied argument is not in the correct type.
        """
        min_roles_count = 1
        if not isinstance(roles, list):
            error_msg = "The roles agrument type must be a list."
            self.log.error(error_msg)
            raise ValueError(error_msg)
        if len(roles) < min_roles_count:
            error_msg = f"A {self.object_type} must have at least one Role assigned."
            self.log.error(error_msg)
            raise ValueError(error_msg)
        self.Roles = roles

    @property
    def read_only(self) -> bool:
        """returns the read only flag of the AclObject.

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
        """returns the send report flag of the AclObject.

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

    def remove_role(self, role_name: str) -> None:
        """Removes a Role from a specific object

        Args:
            role_name (str): The name of the role to remove.
        """
        role_exist = False
        tmp_roles = self.Roles
        if role_name in tmp_roles:
            role_exist = True
            tmp_roles.remove(role_name)
            self.roles = tmp_roles
        self.write()
        return role_exist

    @classmethod
    def remove_roles_from_all_objects(cls, role_name: str) -> set:
        """Looks for AclObjects with the specified Role, if it finds any
        it removes the role from their attributes.

        Args:
            role_name (str): The name of the Role to remove.

        Returns:
            set: containg all the objects affected by the change.
        """
        affected_objects = set()
        for obj_name in cls.list_objects_names():
            obj = cls(obj_name)
            if obj.remove_role(role_name):
                affected_objects.add(obj.ref)
        return affected_objects


class AclUser(AclObject):

    @classmethod
    def create(cls, user: dict) -> AclObject:
        cls.check_parameters(user)
        obj = super().create(user['DomainName'],
                             user['AccountName'],
                             user['CommonName'],
                             "user",
                             user['ID'],
                             user['Roles'],
                             user['ReadOnly'],
                             user['SuperUser'],
                             user['SendReport'])
        return obj

    @classmethod
    def list_user_names(cls, domain_name: str) -> list:
        """lists all the users in the specified domain.

        Args:
        domain_name (str): the name of the domain which the user belongs to.

        Returns:
            list: containing all the users in the domain.
        """
        return cls.list_object_names(domain_name, "user")


class AclGroup(AclObject):

    @classmethod
    def create(cls, group: dict) -> AclObject:
        cls.check_parameters(group)
        obj = super().create(group['DomainName'],
                             group['AccountName'],
                             group['CommonName'],
                             "group",
                             group['ID'],
                             group['Roles'],
                             group['ReadOnly'],
                             group['SuperUser'],
                             group['SendReport'])
        return obj

    @classmethod
    def list_group_names(cls, domain_name: str) -> list:
        """lists all the groups in the specified domain.

        Args:
        domain_name (str): the name of the domain which the user belongs to.

        Returns:
            list: containing all the groups in the domain.
        """
        return cls.list_object_names(domain_name, "group")


Model.register_model_class("AclObject", AclObject)
