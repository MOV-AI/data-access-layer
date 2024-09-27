"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Erez Zomer  (erez@mov.ai) - 2022
"""

from movai_core_shared.logger import Log
from movai_core_shared.common.time import current_time_string
from movai_core_shared.core.secure import generate_secret_string
from movai_core_shared.exceptions import SecretKeyAlreadyExist, SecretKeyDoesNotExist

from dal.movaidb import MovaiDB


class SecretKey:
    log = Log.get_logger(__name__)
    db = MovaiDB(db='global')
    type_name = 'SecretKey'
    secret_key_dict = {'KeyLength': '',
                       'Secret': '',
                       'LastUpdate': ''}

    @classmethod
    def _generate_dict(cls, length: int) -> dict:
        """generate a dictionary with all relevant keys for storing the secret
        key info in DB.

        Args:
            length (int): The length of the key.

        Returns:
            dict: The created dictionary.
        """
        cls.secret_key_dict["KeyLength"] = length
        cls.secret_key_dict["Secret"] = generate_secret_string(length)
        cls.secret_key_dict["LastUpdate"] = current_time_string()
        return cls.secret_key_dict

    @classmethod
    def is_exist(cls, fleet_name: str) -> bool:
        """checks if a specified key exist in DB.

        Args:
            fleet_name (str): The name of the fleet which owns the key.

        Returns:
            bool: True if exist, False otherwise.
        """
        secret = cls.db().get_value({cls.type_name: {fleet_name: {"Secret": ""}}})
        return secret is not None

    @classmethod
    def create(cls, fleet_name: str, length: int = 32) -> None:
        """creates a new key in the DB

        Args:
            fleet_name (str): The name of the fleet which owns the key.
            length (int, optional): The length of the key.. Defaults to 32.

        Returns:
            bool: True if succesfull, False otherwise.
        """
        if cls.is_exist(fleet_name):
            error_msg = f"The secret key {fleet_name} already exist."
            raise SecretKeyAlreadyExist(error_msg)
        cls.db().set({cls.type_name: {fleet_name: cls._generate_dict(length)}})

    @classmethod
    def remove(cls, fleet_name: str) -> None:
        """Removes a key from the DB.

        Args:
            fleet_name (str): The name of the fleet which owns the key.

        Returns:
            bool: True if succesfull, False otherwise.
        """
        if not cls.is_exist(fleet_name):
            error_msg = f"The secret key {fleet_name} does not exist."
            cls.log.error(error_msg)
            raise SecretKeyDoesNotExist(error_msg)
        cls.db().delete({cls.type_name: {fleet_name: cls.secret_key_dict}})

    @classmethod
    def update(cls, fleet_name: str, length: int = 32) -> None:
        """updates an existing key in the DB.

        Args:
            fleet_name (str): The name of the fleet which owns the key.
            length (int, optional): The length of the key.. Defaults to 32.

        Returns:
            bool: True if succesfull, False otherwise.
        """
        if not cls.is_exist(fleet_name):
            error_msg = f"The secret key {fleet_name} does not exist."
            cls.log.error(error_msg)
            raise SecretKeyDoesNotExist(error_msg)
        cls.db().set({cls.type_name: {fleet_name: cls._generate_dict(length)}})

    @classmethod
    def get_secret(cls, fleet_name: str) -> str:
        """returns the secret content.

        Args:
            fleet_name (str): The name of the fleet which owns the key.

        Returns:
            str: The secret.
        """
        if not cls.is_exist(fleet_name):
            error_msg = f"The secret key {fleet_name} does not exist."
            cls.log.error(error_msg)
            raise SecretKeyDoesNotExist(error_msg)
        secret = cls.db().get_value({cls.type_name: {fleet_name: {"Secret": ""}}})
        return secret
