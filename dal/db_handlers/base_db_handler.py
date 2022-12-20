"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Erez Zomer - 2022
"""
from logging import Logger

from movai_core_shared.exceptions import DBHandlerException
from movai_core_shared.logger import Log


class BaseDBHandler(object):
    """This class is a base class for db handlers.
    """
    def __init__(self, handler_name: str, db_type: str, logger: Logger) -> None:
        """constructor

        Args:
            handler_name (str): The name of the handler.
            db_type (str): The type of db handler (redis, influxdb...)
            logger (_type_): A logger object

        Raises:
            Exception: _description_
            Exception: _description_
        """
        if handler_name is None or handler_name == '':
            raise DBHandlerException("DBHandler must have a qualified name.")
        if db_type is None or db_type == '':
            raise DBHandlerException("DBHandler must have a qualified type.")
        self._db_name = None
        self._name = handler_name
        self._type = db_type
        if isinstance(logger, Logger):
            self._logger = logger
        else:
            self._logger = Log.get_logger(self._name)

    def set_db_name(self, db_name: str) -> None:
        """Sets the db name for the handler.

        Args:
            db_name (str): The name of the db.
        """
        self._db_name = db_name

    def get_handler_db_name(self) -> str:
        """Returns the db name of the handler.

        Returns:
            str: The db name
        """
        return self._db_name
