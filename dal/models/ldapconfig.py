from movai_core_shared.envvars import LDAP_KEY_LENGTH
from movai_core_shared.core.securepassword import SecurePassword
from movai_core_shared.core.secure import generate_secret_string
from movai_core_shared.exceptions import (
    LdapConfigAlreadyExist,
    LdapConfigDoesNotExist,
    LdapConfigMissingParameter)

from dal.models.model import Model
from dal.scopes.scopestree import ScopesTree, scopes



class LdapConfig(Model):
    """This class represents an ldap configuration saved in the DB.
    The name of the configuratin will be the same as the domain"""
    mandatory_parameters = ('DomainName',
                            'PrimaryHost',
                            'PrimaryPort',
                            'Username',
                            'Password',
                            'UsersDN',
                            'GroupsDN')

    @classmethod
    def create(cls, ldap_parameters: dict) -> Model:
        """creates a new configuration entry in the DB, returns a reference object

        Args:
        ldap_parameters (dict) - a dictionary with the following keys:
            PrimaryHost (str): name or ip of server.
            PrimaryPort (int): port number.
            SecondaryHost (str): name or ip of server (str)
            SecondaryPort (int): port number.
            SSLVersion (str): use ssl definition\
                (for example: ssl.PROTOCOL_TLSv1_2).
            Username (str): the user who will be used to query LDAP server.
            Password (str): password for the user.
            DomainName (str): FQDN (like exmaple.com), this name will be used\
                to identify the config.
            UsersDN (str): the location in the LDAP tree to look for users\
                ("cn=users,dc=example,dc=com").
            GroupsDN (str): the location in the LDAP tree to look for groups.

        Raises:
            LdapConfigMissingParameter - if there critiacal parameter missing
                in the dictionary.
            ValueError - if 'domain_name' key does not exist
            AlreadyExist - if configuration name already in use.

        Returns:
            (LdapConfig): an object refence to the config on DB.
        """
        for parameter in cls.mandatory_parameters:
            if parameter not in ldap_parameters:
                error_msg = f"The key: \"{parameter}\" is missing in the "\
                            f"supplied dictionary"
                cls.log.error(error_msg)
                raise LdapConfigMissingParameter(error_msg)
        config_name = ldap_parameters['DomainName']
        try:
            config = scopes().create(scope=cls.__name__, ref=config_name)
            config.DomainName = ldap_parameters['DomainName']
            config.SecretKey = generate_secret_string(LDAP_KEY_LENGTH)
            config.set_attributes(ldap_parameters)
            config.last_validated = ''
            config.update_validation(False)
            cls.log.info(f"creating LdapConfig entry named {config_name}")
            return config
        except ValueError:
            error_msg = f"The Ldap configuration named {config_name}"\
                    " is already exist."
            cls.log.error(error_msg)
            raise LdapConfigAlreadyExist(error_msg)

    @classmethod
    def remove(cls, config_name: str) -> None:
        """This function removes a configuration from DB.

        Args:
            config_name (str): The name of the configuration.
        """
        config = cls.get_config_by_name(config_name)
        scopes().delete(config)
        cls.log.info(f"{cls.__name__}:{config_name} have been removed")

    def update(self, ldap_parameters: dict) -> None:
        """update an existing configuration entry in the DB.

        Args:
        ldap_parameters (dict) - a dictionary with the following keys:
            primary_host (str): name or ip of server.
            primary_port (int): port number.
            secondary_host (str): name or ip of server (str)
            secondary_port (int): port number.
            ssl_version (str): use ssl definition\
                (for example: ssl.PROTOCOL_TLSv1_2).
            username (str): the user who will be used to query LDAP server.
            password (str): password for the user.
            domain_name (str): FQDN (like exmaple.com), this name will be used\
                to identify the config.
            users_dn (str): the location in the LDAP tree to look for users\
                ("cn=users,dc=example,dc=com").
            groups_dn (str): the location in the LDAP tree to look for groups.

        Raises:
            ValueError - if 'domain_name' key does not exist.
            DoesNotExist - if configuration name not found in DB.
        """
        self.set_attributes(ldap_parameters)
        self.log.info(f"The LdapConfig:{self.ref} have been updated.")

    @classmethod
    def is_exist(cls, config_name: str) -> bool:
        """This funtion checks if an object with a specific name already exist.

        Args:
            object_name (_type_): The ref name of the object to check.

        Returns:
            bool: True if exist, False otherwise.
        """
        current_configs = []
        for config in scopes().list_scopes(scope=cls.__name__):
            current_configs.append(config['ref'])
        return config_name in current_configs

    @classmethod
    def get_config_by_name(cls, config_name) -> Model:
        """This function find an LdapConfig object with a predefined name.
        and raises an exception if it couldn't find one.
        Args:
            config_name (_type_): the name of the configuration, usually it's
                the same as the domain name.

        Raises:
            LdapConfigDoesNotExist: in case the configuration object couldn't
                be found.

        Returns:
            Model: An LdapConfig object
        """
        try:
            config = ScopesTree().from_path(config_name, scope='LdapConfig')
            return config
        except KeyError:
            error_msg = f"LdapConfig named {config_name} Does not exist"
            cls.log.warning(error_msg)
            raise LdapConfigDoesNotExist(error_msg)

    @classmethod
    def list_config_names(cls) -> list:
        """lists the names of the current object exist in the system.

        Returns:
            list: a list with the names of all available configurations.
        """
        configs = []
        for config in scopes().list_scopes(scope=cls.__name__):
            configs.append(config['ref'])
        cls.log.debug(f"current LdapConfig entries: {configs}")
        return configs

    def set_attributes(self, ldap_parameters: dict) -> None:
        """sets the parameters for config attributes

        Args:
            ldap_parameters (dict): a dictionary with the relevant values to
                set.
        """
        self.primary_host = ldap_parameters.get('PrimaryHost',
                                                self.primary_host)
        self.primary_port = ldap_parameters.get('PrimaryPort',
                                                self.primary_port)
        self.secondary_host = ldap_parameters.get('SecondaryHost',
                                                  self.secondary_host)
        self.secondary_port = ldap_parameters.get('SecondaryPort',
                                                  self.secondary_port)
        self.ssl_version = ldap_parameters.get('SSLVersion',
                                               self.ssl_version)
        self.username = ldap_parameters.get('Username', self.username)
        self.password = ldap_parameters.get('Password', self.password)
        self.users_dn = ldap_parameters.get('UsersDN', self.users_dn)
        self.groups_dn = ldap_parameters.get('GroupsDN', self.groups_dn)
        self.write()

    def convert_to_dict(self) -> dict:
        """convert the object to dictionary representation.

        Returns:
            (dict): a dictionary with fields as defined in scheme.        
        """
        config_info = {}
        config_info['PrimaryHost'] = self.PrimaryHost
        config_info['PrimaryPort'] = self.PrimaryPort
        config_info['SecondaryHost'] = self.SecondaryHost
        config_info['SecondaryPort'] = self.SecondaryPort
        config_info['SSLVersion'] = self.SSLVersion
        config_info['Username'] = self.Username
        config_info['DomainName'] = self.DomainName
        config_info['UsersDN'] = self.UsersDN
        config_info['GroupsDN'] = self.GroupsDN
        return config_info

    def update_validation(self, status: bool) -> None:
        """This function is called after configuration validation is executed.
        if the validation succeeds it updates the last_validated field with
        current time.

        Args:
            status (bool): The status of the configuration validation.
        """
        self.validation_status = status
        if status:
            self.last_validated = self._current_time()
        self.write()

    @property
    def primary_host(self) -> str:
        """property to represent primary host attribute.

        Returns:
            str: ip or host name of the primary host.
        """
        primary_host = str(self.PrimaryHost)
        return primary_host

    @primary_host.setter
    def primary_host(self, host: str) -> None:
        """setter property to set the primary host attribute.

        Args:
            host (str): name or ip of the primary host.

        Raises:
            ValueError: in case the argument is not in the correct type.
        """
        if not isinstance(host, str):
            raise ValueError("host argument must be of type str.")
        self.PrimaryHost = host

    @property
    def secondary_host(self) -> str:
        """property to represent secondary host attribute.

        Returns:
            str: ip or host name of the secondary host.
        """
        secondary_host = str(self.SecondaryHost)
        return secondary_host

    @secondary_host.setter
    def secondary_host(self, host: str) -> None:
        """setter property to set the secondary host attribute.

        Args:
            host (str): name or ip of the secondary host.

        Raises:
            ValueError: in case the argument is not in the correct type.
        """
        if not isinstance(host, str):
            raise ValueError("host argument must be of type str.")
        self.SecondaryHost = host

    @property
    def primary_port(self) -> int:
        """property to represent primary port attribute.

        Returns:
            int: ip or host name of the primary port.
        """
        primary_port = self.PrimaryPort
        return primary_port

    @primary_port.setter
    def primary_port(self, port: int) -> None:
        """setter property to set the primary port attribute.

        Args:
            port (int): port number.

        Raises:
            ValueError: in case the argument is not in the correct type.
        """
        if not isinstance(port, int):
            raise ValueError("port argument must be of type int.")
        self.PrimaryPort = port

    @property
    def secondary_port(self) -> int:
        """property to represent secondary port attribute.

        Returns:
            int: ip or host name of the secondary port.
        """
        secondary_port = self.SecondaryPort
        return secondary_port

    @secondary_port.setter
    def secondary_port(self, port: int) -> None:
        """setter property to set the secondary port attribute.

        Args:
            port (int): port number.

        Raises:
            ValueError: in case the argument is not in the correct type.
        """        
        if not isinstance(port, int):
            raise ValueError("port argument must be of type int.")
        self.SecondaryPort = port

    @property
    def ssl_version(self) -> int:
        """property to represent ssl version attribute.

        Returns:
            int: a number representing the version of ssl version
                as defined in ldap3 library.
        """
        ssl_version = self.SSLVersion
        return ssl_version

    @ssl_version.setter
    def ssl_version(self, version: int) -> None:
        """setter property to set the ssl version attribute.

        Args:
            version (int): the number representing the version of ssl.

        Raises:
            ValueError: in case the argument is not in the correct type.
        """
        if not isinstance(version, int):
            raise ValueError("version argument must be of type int.")
        self.SSLVersion = version

    @property
    def username(self) -> str:
        """property to represent username attribute.

        Returns:
            str: the name of the user to authenticate with LDAP
                servers.
        """
        username = str(self.Username)
        return username

    @username.setter
    def username(self, name: str) -> None:
        """setter property to set the username attribute.

        Args:
            name (str): the name of the user.

        Raises:
            ValueError: in case the argument is not in the correct type.
        """
        if not isinstance(name, str):
            raise ValueError("name argument must be of type str.")
        self.Username = name

    @property
    def password(self) -> str:
        """property to represent password attribute.

        Returns:
            str: the pasword of the user authenticate with LDAP
                servers.
        """
        password = ""
        secure = SecurePassword(self.SecretKey)
        if self.Password:
            password = secure.decrypt_password(self.Password)
        return password

    @password.setter
    def password(self, secret: str) -> None:
        """setter property to set the password attribute.

        Args:
            secret (str): the password to store.

        Raises:
            ValueError: in case the argument is not in the correct type.
        """        
        if not isinstance(secret, str):
            raise ValueError("secret argument must be of type str.")
        secure = SecurePassword(self.SecretKey)
        self.Password = secure.encrypt_password(secret)

    @property
    def domain_name(self) -> str:
        """property to represent domain name attribute.

        Returns:
            str: the name of the domain of the LDAP servers.
        """
        domain_name = str(self.DomainName)
        return domain_name

    @property
    def users_dn(self) -> str:
        """property to represent organizational unit to look for users
        inside LDAP servers.

        Returns:
            str: the disntinguished name of the organizational unit.
        """
        users_dn = str(self.UsersDN)
        return users_dn

    @users_dn.setter
    def users_dn(self, dn: str) -> None:
        """setter property to set the users organizational unit.

        Args:
            dn (str): the name of the organizational unit.

        Raises:
            ValueError: in case the argument is not in the correct type.
        """        
        if not isinstance(dn, str):
            raise ValueError("dn argument must be of type str.")
        self.UsersDN = dn

    @property
    def groups_dn(self) -> str:
        """property to represent organizational unit to look for groups
        inside LDAP servers.

        Returns:
            str: the disntinguished name of the organizational unit.
        """
        groups_dn = str(self.GroupsDN)
        return groups_dn

    @groups_dn.setter
    def groups_dn(self, dn: str) -> None:
        """setter property to set the groups organizational unit.

        Args:
            dn (str): the name of the organizational unit.

        Raises:
            ValueError: in case the argument is not in the correct type.
        """          
        if not isinstance(dn, str):
            raise ValueError("dn argument must be of type str.")
        self.GroupsDN = dn

    @property
    def validation_status(self) -> bool:
        """property to represent if the config was validated

        Returns:
            bool: True in case it was validated, False otherwise.
        """
        status = bool(self.ValidationStatus)
        return status 

    @validation_status.setter
    def validation_status(self, status: bool) -> None:
        """setter property to set the groups organizational unit.

        Args:
            status (bool): Status of the validation.

        Raises:
            ValueError: in case the argument is not in the correct type.
        """          
        if not isinstance(status, bool):
            raise ValueError("status argument must be of type bool.")
        self.ValidationStatus = status

    @property
    def last_validated(self) -> str:
        """property to represent organizational unit to look for groups
        inside LDAP servers.

        Returns:
            str: The last time a successful validation happened.
        """
        return str(self.LastValidated)

    @last_validated.setter
    def last_validated(self, validation_time: str) -> None:
        """setter property to set the groups organizational unit.

        Args:
            validation_time (str): The time when the configuration was last validated.

        Raises:
            ValueError: in case the argument is not in the correct type.
        """          
        if not isinstance(validation_time, str):
            raise ValueError("validation_time argument must be of type str.")
        self.LastValidated = validation_time

    @property
    def bind_username(self) -> str:
        """returns the bind user name in the user_name@domain_name format.

        Returns:
            str: the bind user name.
        """
        bind_username = f"{self.username}@{self.domain_name}"
        return bind_username

Model.register_model_class("LdapConfig", LdapConfig)
