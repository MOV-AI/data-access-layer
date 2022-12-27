"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Ofer Katz - 2022

   An interface class for accessing a time series DB
   Currently the class is just for accessing InfluxDB and therefore it is directly accessing the influxDB APIs
"""
from datetime import datetime
from influxdb import InfluxDBClient

from movai_core_shared.logger import Log
from movai_core_shared.consts import INFLUXDB_HOST, INFLUXDB_DB_NAMES

from .base_db_handler import BaseDBHandler

class TimeSeriesDbHandler(BaseDBHandler):
    """
    A class for handling adding a measurement to a tine-series DB
    Currently only InfluxDB is used and therefore no need for an additional abstraction layer
    """
    def __init__(self, db_names: list, connect=True):
        """
        Constractor
        Args:
            connect: Specify if the DB exist (reachable), mainly for debug purposes
        """
        super().__init__(self.__class__.__name__, "Influxdb", Log.get_logger(self.__class__.__name__))
        self._db_names = db_names
        self._db_clients = dict()
        self._db_exist = connect
        for db_name in self._db_names:
            self.register_db_client(db_name)

    def register_db_client(self, db_name: str):
        """
        Attempt to connect to the DB. Check if the db_name DB exist.
        If does not exist create it
        Args:
            db_name: The DB name that is required

        """
        if self._db_exist:
            if self._db_clients is not None and db_name in self._db_clients:
                self._logger.info(f'Client for db {db_name} was registered already!!!')
                return

            client = InfluxDBClient(host=INFLUXDB_HOST, database=db_name)
            try:
                # If Database does not exist create
                if db_name not in client.get_list_database():
                    client.create_database(db_name)
                #if not [db for db in client.get_list_database() if db["name"] == db_name]:
                #    client.create_database(db_name)

                self._db_clients[db_name] = client
                self._logger.info(f'Client for db {db_name} was registered')
            except Exception as e:
                self._logger.info(f'Failed to access InfluxDB in attempt to {db_name}')
                self._db_exist = False

    def insert_measurement(self, db_name: str, measurement: str, creation_time: float, tags: dict, data: dict):
        """
        Add the request measurement to the DB
        Args:
            request: The measurement to be added

        """
        if not self._db_exist:
            # Local time series DB was not set
            return

        if self._db_clients is not None and db_name in self._db_clients:
            metric_time = datetime.fromtimestamp(creation_time)
            measurement_data = [
                {
                    "measurement": measurement,
                    "tags": tags,
                    "time": metric_time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "fields": data
                }
            ]

            self._db_clients[db_name].write_points(measurement_data)
            self._logger.debug(f'writing measurement {measurement_data} to  {db_name} ')
        
    def query_db(self, db: str, query_clause: str):
        """
        Execute the provided query clause on the requested DB
        Args:
            db: the name of the time series database to query
            query_clause: The query to be executed on the provided time series DB

        """
        if not self._db_exist:
            # Time series DB was not set
            return None

        result = None
        if self._db_clients is not None and db in self._db_clients:
            result = self._db_clients[db].query(query_clause, epoch="s")

        return result

InfluxDBHandler = TimeSeriesDbHandler(INFLUXDB_DB_NAMES)