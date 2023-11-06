from typing import List
from datetime import datetime

from movai_core_shared.logger import Log
from movai_core_shared.common.utils import create_principal_name
from movai_core_shared.exceptions import (
    AclObjectAlreadyExist,
    AclObjectDoesNotExist,
    AclObjectError,
    AclObjectIDMismatch,
    AclObjectInvalidAttribute)

from .base import MovaiBaseModel

MAX_ATTR_LENGTH = 100
LOGGER = Log.get_logger(__name__)

class AclObject(MovaiBaseModel):
    """This class represents an access list for remote users.
    Each record in the access list is actually a user that is allowed
    to login.
    The name of each record is in the form "account_name@domain_name".
    """
    DomainName: str
    AccountName: str
    CommonName: str
    ObjectType: str
    ID: str
    Roles: str
    ReadOnly: bool
    SuperUser: bool
    SendReport: bool

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
               send_report: bool = False) -> MovaiBaseModel:
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
            acl_object = cls(
                name = principal_name,
                DomainName = domain_name,
                AccountName = account_name,
                common_name = common_name,
                ObjectType = object_type,
                ID = identifier,
                Roles = roles,
                ReadOnly = read_only,
                SuperUser = super_user,
                SendReport = send_report
            )
             
            acl_object.save()
            return acl_object
        except ValueError:
            error_msg = f"The AclObject named {principal_name} "\
                        f"is already exist in DB"
            LOGGER.error(error_msg)
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
        principal_name = create_principal_name(domain_name, account_name)
        acl_object = cls(principal_name)
         
        if id == acl_object.ID:
            acl_object.delete()
            LOGGER.info(f"Successfully removed {cls.__name__}:"
                         f"{principal_name}")
        else:
            error_msg = f"Failed to remove {principal_name}, the "\
                f"supplied id does not match object's id"
            LOGGER.error(error_msg)
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
            self.save()
            LOGGER.info(f"Successfully updated {self.principal_name}")
        else:
            error_msg = f"Failed to update {self.principal_name}, the "\
                f"supplied id does not match object's id"
            LOGGER.warning(error_msg)
            raise AclObjectIDMismatch(error_msg)



    @classmethod
    def get_object_by_name(cls,
                           domain_name: str,
                           account_name: str) -> MovaiBaseModel:
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
            obj = cls(principal_name)
            return obj
        except KeyError:
            error_msg = f"Failed to find acl object {principal_name},"\
                        f" object does not exist"
            LOGGER.error(error_msg)
            raise AclObjectDoesNotExist(error_msg)

    @classmethod
    def list_domain_objects_account_names(cls, domain_name: str, object_type: str) -> list:
        """lists all the object of specific type in a specified domain.

        Args:
        domain_name (str): the name of the domain which the user belongs to.
        type (str): the type of the object (user or group)

        Returns:
            list: containing all the objects conforms to domain and type.
        """
        domain_objects_account_names = []
        for obj in AclObject.select():
            if domain_name == obj.domain_name and \
               object_type == obj.object_type:
                domain_objects_account_names.append(obj.account_name)
        LOGGER.debug(f"Current AclObjects defined in access list:" \
                     f"{domain_objects_account_names}")
        return domain_objects_account_names

    def display_info(self) -> None:
        """display all the user attributes as defined in AclObject scheme.
        """
        try:
            LOGGER.info(f"name: {self.name}")
            LOGGER.info(f"DomainName: {self.DomainName}")
            LOGGER.info(f"AccountName: {self.AccountName}")
            LOGGER.info(f"CommonName: {self.CommonName}")
            LOGGER.info(f"Type: {self.ObjectType}")
            LOGGER.info(f"ID: {self.ID}")
            LOGGER.info(f"Roles: {self.Roles}")
            LOGGER.info(f"ReadOnly: {self.ReadOnly}")
            LOGGER.info(f"SuperUser: {self.SuperUser}")
            LOGGER.info(f"SendReport: {self.SendReport}")
            LOGGER.info(f"LastUpdate: {self.LastUpdate}")
        except AttributeError as a:
            LOGGER.error(a)      

    @classmethod
    def is_exist(cls, domain_name: str, account_name) -> bool:
        """This funtion checks if an object with a specific name already exist.

        Args:
            object_name (_type_): The ref name of the object to check.

        Returns:
            bool: True if exist, False otherwise.
        """
        principal_name = create_principal_name(domain_name, account_name)
        return super().is_exist(principal_name)

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
        if len(name) > MAX_ATTR_LENGTH:
            raise ValueError(f"The name agrument must be less than "
                             f"{MAX_ATTR_LENGTH}")
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
        identifier = str(self.ID)
        return identifier

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
            LOGGER.error(error_msg)
            raise ValueError(error_msg)
        if len(roles) < min_roles_count:
            error_msg = f"A {self.object_type} must have at least one Role assigned."
            LOGGER.error(error_msg)
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

    def remove_role(self, role_name: str) -> bool:
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
            self.save()
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
        for obj in cls.select():
            if obj.remove_role(role_name):
                affected_objects.add(obj.name)
        return affected_objects


class AclUser(AclObject):

    @classmethod
    def create(cls, user: dict) -> AclObject:
        obj = super().create(**user, object_type="user")
        return obj

    @classmethod
    def list_user_names(cls, domain_name: str) -> list:
        """lists all the users in the specified domain.

        Args:
        domain_name (str): the name of the domain which the user belongs to.

        Returns:
            list: containing all the users in the domain.
        """
        return cls.list_domain_objects_account_names(domain_name, "user")


class AclGroup(AclObject):

    @classmethod
    def create(cls, group: dict) -> AclObject:
        obj = super().create(**group, object_type="group")
        return obj

    @classmethod
    def list_group_names(cls, domain_name: str) -> list:
        """lists all the groups in the specified domain.

        Args:
        domain_name (str): the name of the domain which the user belongs to.

        Returns:
            list: containing all the groups in the domain.
        """
        return cls.list_domain_objects_account_names(domain_name, "group")

