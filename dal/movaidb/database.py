"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020
   - Moawiya Mograbi (moawiya@mov.ai) - 2022
"""

import asyncio
from os import getenv, path
from re import split
import redis
from deepdiff import DeepDiff
import pickle
import aioredis
from redis.client import Pipeline
from typing import Any, Tuple
from dal.classes import Singleton
from dal.plugins import Resource
from movai_core_shared.logger import Log
from movai_core_shared.exceptions import InvalidStructure
LOGGER = Log.get_logger("dal.mov.ai")
dir_path = path.dirname(path.realpath(__file__))
__SCHEMAS_URL__ = f"file://{dir_path}/../validation/schema"


class AioRedisClient(metaclass=Singleton):
    """
    A Singleton class implementing AioRedis API.
    """
    _databases = {}
    loop = asyncio.get_event_loop()

    @classmethod
    def _register_databases(cls):
        if not cls._databases:
            cls._databases = {
                "db_slave": {
                    'name': 'db_slave',
                    'host': MovaiDB.REDIS_SLAVE_HOST,
                    'port': MovaiDB.REDIS_SLAVE_PORT,
                    'mode': None,
                    'enabled': True
                },
                "db_local": {
                    'name': 'db_local',
                    'host': MovaiDB.REDIS_LOCAL_HOST,
                    'port': MovaiDB.REDIS_LOCAL_PORT,
                    'mode': None,
                    'enabled': True
                },
                "slave_pubsub": {
                    'name': 'slave_pubsub',
                    'host': MovaiDB.REDIS_SLAVE_HOST,
                    'port': MovaiDB.REDIS_SLAVE_PORT,
                    'mode': 'SUB',
                    'enabled': True
                },
                "local_pubsub": {
                    'name': 'local_pubsub',
                    'host': MovaiDB.REDIS_LOCAL_HOST,
                    'port': MovaiDB.REDIS_LOCAL_PORT,
                    'mode': 'SUB',
                    'enabled': True
                },
                "db_global": {
                    'name': 'db_global',
                    'host': MovaiDB.REDIS_MASTER_HOST,
                    'port': MovaiDB.REDIS_MASTER_PORT,
                    'mode': None,
                    'enabled': False
                }
            }

    async def shutdown(self):
        """shutdown connections
        """
        for _, conn in type(self)._databases.items():
            conn.close()
        tasks = [getattr(self, db_name).wait_closed()
                 for db_name in type(self)._databases.keys()]
        await asyncio.gather(*tasks, return_exceptions=True)

    @classmethod
    async def get_client(cls):
        """will return class singleton instance

        Returns:
            AioRedisClient: object of class AioRedisClient
        """
        cls._register_databases()
        instance = cls()
        await instance._init_databases()
        return instance

    async def _init_databases(self):
        """will initialize connection pools
        """
        for conn_name, conn_config in type(self)._databases.items():
            conn_enabled = conn_config.get("enabled", False)
            _conn = None
            if conn_enabled:
                _conn = getattr(self, conn_name, None)
                if not _conn or _conn.closed:
                    try:
                        address = (conn_config["host"], conn_config["port"])
                        if conn_config.get("mode") == "SUB":
                            _conn = await aioredis.create_pool(
                                        address, minsize=1, maxsize=100)
                        else:
                            _conn = await aioredis.create_redis_pool(
                                address, minsize=2, maxsize=100, timeout=1)
                    except Exception as e:
                        LOGGER.error(e)
            setattr(self, conn_name, _conn)

    @classmethod
    def enable_db(cls, db_name):
        """will enable the given db name

        Args:
            db_name (str): database name
        """
        cls._register_databases()
        cls._databases[db_name]['enabled'] = True


class Redis(metaclass=Singleton):
    """
    A Singleton class implementing Redis API.
    """

    def __init__(self):
        self.master_pool = redis.ConnectionPool(
                                            host=MovaiDB.REDIS_MASTER_HOST,
                                            port=MovaiDB.REDIS_MASTER_PORT,
                                            db=0)
        self.slave_pool = redis.ConnectionPool(
                                            host=MovaiDB.REDIS_SLAVE_HOST,
                                            port=MovaiDB.REDIS_SLAVE_PORT,
                                            db=0)
        self.local_pool = redis.ConnectionPool(
                                            host=MovaiDB.REDIS_LOCAL_HOST,
                                            port=MovaiDB.REDIS_LOCAL_PORT,
                                            db=0)

        self.thread = None

    @property
    def db_global(self) -> redis.Redis:
        return redis.Redis(connection_pool=self.master_pool,
                           decode_responses=False)

    @property
    def db_slave(self) -> redis.Redis:
        return redis.Redis(connection_pool=self.slave_pool,
                           decode_responses=False)

    @property
    def db_local(self) -> redis.Redis:
        return redis.Redis(connection_pool=self.local_pool,
                           decode_responses=False)

    @property
    def slave_pubsub(self) -> redis.client.PubSub:
        return self.db_slave.pubsub()

    def local_pubsub(self) -> redis.client.PubSub:
        return self.db_local.pubsub()


class MovaiDB:
    """Main MovaiDB"""

    class API(dict):
        """
        # Represents the API template dict. Can be Imported or saved into Redis
        """

        __API__ = {}

        def __init__(self, version: str = 'latest',
                     url: str = __SCHEMAS_URL__):
            super(type(self), self).__init__()
            # We force the version of the schemas to the deprecated version
            version = "1.0"
            self.__url = path.join(url, version)
            self.__version = version
            if version not in type(self).__API__:
                # load builtins schemas
                current_path = path.join(url, version)
                type(self).__API__[version] = {
                    path.splitext(schema_file)[0]:
                        Resource.read_json(
                            path.join(current_path, schema_file))["schema"]
                    for schema_file in Resource.list_resources(current_path)
                    if schema_file.endswith(".json")}

        @property
        def version(self):
            """ Current version """
            return self.__version

        @property
        def url(self):
            """ Base uri """
            return self.__url

        def __setitem__(self, key, value):
            raise NotImplementedError

        def __getitem__(self, key):
            return type(self).__API__[self.__version][key]

        def __iter__(self):
            return type(self).__API__[self.__version].__iter__

        def __repr__(self):
            return type(self).__API__[self.__version].__repr__()

        def __str__(self):
            return type(self).__API__[self.__version].__str__()

        def keys(self):
            return type(self).__API__[self.__version].keys()

        def values(self):
            return type(self).__API__[self.__version].values()

        @classmethod
        def get_schema(cls, version, name):
            """
            return scope schema for the specifed version
            """
            try:
                return cls(version=version).get_api()[name]
            except KeyError:
                return {}

        def get_api(self):
            """
            return the current API
            """
            return type(self).__API__[self.__version]

    db_dict = {
        "global": {
            "db_read": "db_slave",
            "db_write": "db_global",
            "pubsub": "slave_pubsub"
        },
        "local": {
            "db_read": "db_local",
            "db_write": "db_local",
            "pubsub": "local_pubsub"
        }
    }

    REDIS_MASTER_HOST = getenv("REDIS_MASTER_HOST", "redis-master")
    REDIS_MASTER_PORT = int(getenv("REDIS_MASTER_PORT", 6379))
    REDIS_SLAVE_PORT = int(getenv("REDIS_SLAVE_PORT", REDIS_MASTER_PORT))
    REDIS_LOCAL_HOST = getenv("REDIS_LOCAL_HOST", "redis-local")
    REDIS_LOCAL_PORT = int(getenv("REDIS_LOCAL_PORT", 6379))
    REDIS_SLAVE_HOST = getenv("REDIS_SLAVE_HOST", REDIS_MASTER_HOST)

    def __init__(self, db: str = 'global', _api_version: str = 'latest',
                 *, loop=None, databases=None) -> None:
        self.db_read: redis.Redis = None
        self.db_write: redis.Redis = None
        self.pubsub: redis.client.PubSub = None

        self.movaidb = databases or type(self).Redis()
        for attribute, val in self.db_dict[db].items():
            setattr(self, attribute, getattr(self.movaidb, val))

        schema_folder = "file://DAL/dataaccesslayer/dal/validation/schema"
        if _api_version == 'latest':

            self.api_struct = MovaiDB.API(url=schema_folder).get_api()
        else:
            # we then need to get this from database!!!!
            self.api_struct = MovaiDB.API(version=_api_version, url=schema_folder).get_api()
        self.api_star = self.template_to_star(self.api_struct)
        # self.validator = Validator(db).val

        self.loop = loop
        if not self.loop:
            try:
                self.loop = asyncio.get_event_loop()
            except Exception:
                self.loop = asyncio.new_event_loop()

    def search(self, _input: dict) -> list:
        """
        Search redis for a certain structure, returns a list of matching
        keys Meant to be used by other functions in this class
        """
        patterns = [k for k, _, _ in self.dict_to_keys(_input, validate=False)]
        keys = list()
        for p in patterns:
            for elem in self.db_read.scan_iter(p, count=1000):
                keys.append(elem.decode('utf-8'))
        keys.sort(key=str.lower)

        return keys

    def find(self, _input: dict) -> dict:
        """
        Search redis for a certain structure, returns a dict
        with matching result
        """
        keys_list = self.search(_input)
        return self.keys_to_dict([(key, '') for key in keys_list])

    def search_wild(self, _input: dict, only_pattern=False) -> list:
        """
        Accepts a not full structure to search and returns a
        list of matching keys
        """

        def generate_key(_input, symbol, scan_key=''):
            for key, value in _input.items():
                if isinstance(value, dict):
                    scan_key += key + symbol
                    symbol = ':' if symbol == ',' else ','
                    scan_key = generate_key(value, symbol, scan_key)
                else:
                    if only_pattern:
                        scan_key += key
                        continue
                    if value == '*':
                        scan_key += key + value
                    elif value == '**':
                        scan_key += key + symbol + '*'
                    else:
                        scan_key += key + ':' + value
            return scan_key

        scan_key = generate_key(_input, ':')
        if only_pattern:
            return scan_key

        # get db keys that match scan_key
        keys = [elem.decode('utf-8')
                for elem in self.db_read.scan_iter(scan_key, count=1000)]
        keys.sort(key=str.lower)
        return keys

    def get2(self, _input: dict) -> list:
        keys = self.search_wild(_input)
        scan_values = [(keys[idx], '') for idx, _ in enumerate(keys)]
        return self.keys_to_dict(scan_values)

    def get_value(self, _input: dict, search=True) -> Any:
        if search:  # value might be on the key so we need a search
            keys = self.search(_input)
        else:
            keys = [self.dict_to_keys(_input)[0][0]]

        for key in keys:
            if key[-1] != ':':  # value is in key
                return key.rsplit(':', 1)[-1]
            value = self.db_read.get(key)
            if value:
                value = self.decode_value(value)
            return value

    def decode_value(self, _value):
        '''Decodes a value from redis'''
        try:
            decoded_value = _value.decode('utf-8')
        except UnicodeDecodeError:
            try:
                decoded_value = pickle.loads(_value)
            except:
                return _value
        return decoded_value

    def get(self, _input: dict) -> Tuple[dict, str]:
        """
        Receives a full or partial dict and returns the values
        matching in the DB

        Returns:
            (dict, ErrorCode)
        """
        try:
            keys = self.search(_input)
        except:
            keys = self.search_wild(_input)

        kv = list()
        for idx, value in enumerate(self.db_read.mget(keys)):
            if value:
                kv.append((keys[idx], self.decode_value(value)))
            else:  # no value
                try:  # Is it a hash?
                    get_hash = self.db_read.hgetall(keys[idx])
                    kv.append((keys[idx], self.sort_dict(
                        self.decode_hash(get_hash))))
                except:
                    try:  # Is it a list?
                        get_list = self.db_read.lrange(keys[idx], 0, -1)
                        kv.append((keys[idx], self.decode_list(get_list)))
                    except:  # is just a None...
                        pass

        return self.keys_to_dict(kv)

    def set(self, _input: dict, pickl: bool = True, pipe=None,
            ex=None, px=None, nx=False, xx=False, validate=True) -> str:
        """
        Set key values in database
        """

        # here we validate our dict and get the keys
        kvs = self.dict_to_keys(_input, validate)

        db_set = pipe if isinstance(pipe, Pipeline) else self.db_write
        # Save each key value in redis according to template value type
        for key, value, source in kvs:
            if pickl and source not in ['hash', 'list']:
                value = pickle.dumps(value)
            try:
                if source[0] == '&':
                    # value is in key, need to rename if exists
                    search_dict = self.update_dict(
                        self.keys_to_dict([(key, '')]), '*')
                    previous_key = self.search(search_dict)
                    if not previous_key:
                        db_set.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
                    elif len(previous_key) == 1:
                        db_set.rename(previous_key[0], key)
                    else:
                        print('More that 1 key in Redis for the same structure value')
                else:
                    if source == 'hash':
                        value = {hkey: pickle.dumps(hval)
                                 for hkey, hval in value.items()}
                        if value:
                            db_set.delete(key)
                            db_set.hmset(key, value)
                    elif source == 'list':
                        for lval in value:
                            if pickl:
                                lval = pickle.dumps(lval)
                            db_set.rpush(key, lval)
                    else:
                        db_set.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
            except:
                print('Something went wrong while saving this in Redis...')

    def delete(self, _input: dict, pipe=None) -> int:
        """
        deletes _input
        Returns:
            number of deleted entries.
        """
        db_del = pipe if isinstance(pipe, Pipeline) else self.db_write

        keys = list()
        for key, _, _ in self.dict_to_keys(_input, validate=False):
            keys.append(key)

        if not keys:
            return 0

        return db_del.delete(*keys)

    def unsafe_delete(self, _input: dict, pipe=None) -> str:
        """
        deletes _input
        Returns:
            number of deleted entries.
        """
        db_del = pipe if isinstance(pipe, Pipeline) else self.db_write
        try:
            keys = self.search(_input)
        except:
            keys = self.search_wild(_input)
        if not keys:
            return ""

        return db_del.delete(*keys)

    def exists(self, _input: dict) -> bool:
        """
        assumes it get one or more full keys, no * allowed here
        """
        keys = [key for key, _, _ in self.dict_to_keys(_input, validate=False)]
        if not keys:
            raise Exception('Invalid input')
        if self.db_read.exists(*keys) == len(keys):
            return True

        return False

    def rename(self, old_input: dict, new_input: dict) -> bool:
        '''Receives two dicts with same struct to replace one with the other'''
        keys = list()
        try:
            old_keys = self.dict_to_keys(old_input, validate=False)
            new_keys = self.dict_to_keys(new_input, validate=True)
            # problems of mismatch here if we send large dicts due strange
            # things in sort?, for now is used for single dicts,
            # needs more testing
            for (old_key, _, _), (new_key, _, _) in zip(old_keys, new_keys):
                keys.append((old_key, new_key))

        except Exception as e:
            #TODO add log
            raise InvalidStructure('Invalid rename: %s' % e)

        for old, new in keys:
            self.db_write.rename(old, new)

        return True  # need also local

    # ===================  SUBSCRIBERS  ===================================
    async def subscribe_channel(self, _input: dict, function):
        """Subscribes to a specific channel"""
        for elem in self.dict_to_keys(_input, validate=False):
            key, _, _ = elem
            self.loop.create_task(self.task_subscriber(key+'*', function))

    async def subscribe(self, _input: dict, function):
        """Subscribes to a KeySpace event"""
        for elem in self.dict_to_keys(_input, validate=False):
            key, _, _ = elem
            self.loop.create_task(self.task_subscriber(
                '__keyspace@*__:%s' % key, function))

    async def task_subscriber(self, key: str, callback) -> None:
        """Calls a callback every time it gets a message."""
        # Acquires a connection from free pool.
        # Creates new connection if needed.
        _conn = await self.pubsub.acquire()
        # Create Redis interface
        conn = aioredis.Redis(_conn)
        # Switch connection to Pub/Sub mode and subscribe to specified patterns
        channel = await conn.psubscribe(key)
        # Waits for message to become available in channel
        while await channel[0].wait_message():
            msg = await channel[0].get(encoding='utf-8')
            callback(msg)
        conn.close()
        await conn.wait_closed()

    # ===================  List and Hashes  ===============================
    def push(self, _input: dict, pickl: bool = True):
        """Push a value to the right of a Redis list"""
        kvs = self.dict_to_keys(_input, validate=True)
        for key, value, _ in kvs:
            if pickl:
                value = pickle.dumps(value)
            try:
                self.db_write.rpush(key, value)
            except:
                print('Something went wrong while saving "%s" in Redis' % (key))

    def pop(self, _input: dict):
        """Pop a value from the left of a Redis list"""
        keys = self.search(_input)
        pop_value = None
        for key in keys:
            pop_value = self.db_write.lpop(key)
            break
        if pop_value:
            pop_value = self.decode_value(pop_value)

        return pop_value

    def hset(self, _input: dict):
        """
        Implementation of hset, from redys-py: Set key to value within hash

        Returns:
            1 if HSET created a new field, otherwise 0
            e.g {'Robot':{'lala':{'Parameters': {'Foo':2, 'Bar':3}}}}
        """
        kvs = self.dict_to_keys(_input, validate=True)
        for key, value, _ in kvs:
            try:
                for hash_field in value:
                    self.db_write.hset(
                        key, hash_field, pickle.dumps(value[hash_field]))
            except:
                print('Something went wrong while saving "%s" in Redis' % (key))

    def hget(self, _input: dict, hash_field: str, search=True):
        """Return the value of a key within the hash name"""
        if search:  # value might be on the key so we need a search
            keys = self.search(_input)
        else:
            # just convert the dict to a key
            keys = [self.dict_to_keys(_input)[0][0]]
        for key in keys:
            value = self.db_read.hget(key, hash_field)
            if value:
                value = self.decode_value(value)
            return value

    def hdel(self, _input: dict, hash_field: str, search=True):
        """Deletes a key within the hash name"""
        if search:
            keys = self.search(_input)
        else:
            # just convert the dict to a key
            keys = [self.dict_to_keys(_input)[0][0]]
        for key in keys:
            return self.db_write.hdel(key, hash_field)

    def get_list(self, _input: dict, search=True) -> Any:
        '''Gets a full list from Redis'''
        if search:
            keys = self.search(_input)
        else:
            # just convert the dict to a key
            keys = [self.dict_to_keys(_input)[0][0]]
        for key in keys:
            get_list = self.db_read.lrange(key, 0, -1)
            return self.decode_list(get_list)

    def get_hash(self, _input: dict, search=True) -> Any:
        '''Gets a full hash from Redis'''
        if search:
            keys = self.search(_input)
        else:
            # just convert the dict to a key
            keys = [self.dict_to_keys(_input)[0][0]]
        for key in keys:
            get_hash = self.db_read.hgetall(key)
            return self.decode_hash(get_hash)

    def decode_hash(self, _hash):
        '''Decodes a full hash from redis'''
        decoded_hash = {}
        for key, val in _hash.items():  # decode 1 by 1
            try:
                decoded_hash[key.decode('utf-8')] = val.decode('utf-8')
            except UnicodeDecodeError:
                decoded_hash[key.decode('utf-8')] = pickle.loads(val)
        return decoded_hash

    def decode_list(self, _list):
        '''Decodes a full list from redis'''
        try:
            decoded_list = [elem.decode('utf-8') for elem in _list]
        except UnicodeDecodeError:
            decoded_list = [pickle.loads(elem) for elem in _list]
        return decoded_list

    # ===================  Distributed Events  ============================
    # https://redislabs.com/redis-best-practices/communication-patterns/distributed-events/
    def hset_pub(self, _input: dict):
        """Same as hset with addition publish in a respective channel"""
        kvs = self.dict_to_keys(_input, validate=True)
        for key, value, _ in kvs:
            value = {hkey: pickle.dumps(hval) for hkey, hval in value.items()}
            changed_hkeys = ' '.join([hkey for hkey in value])
            try:
                self.db_write.hmset(key, value)
            except:
                print('Something went wrong while saving "%s" in Redis' % (key))
            self.db_write.publish(key, str(changed_hkeys))

    # ===================  Pipe Commands  =================================
    def create_pipe(self, write=True):  # redis.client.Pipeline
        """Create a pipeline"""
        if write:
            return self.db_write.pipeline()
        return self.db_read.pipeline()

    @staticmethod
    def execute_pipe(pipe):
        return pipe.execute()

    # ===================  Convert and Validate  ==========================
    def validate_value(self, value, condition):
        """Value validation before safe in database"""
        # can't validate against the new API, so:
        return  # no validate at all :)
        # pylint: disable=unreachable
        function = self.validator.get(condition, False)
        if function:
            function(value)
        else:
            pass

    def validate(self, d, api, base_key, validate, keys):
        """Validation before safe in database"""
        for (k, v) in d.items():
            key = base_key
            is_ok = False
            for k_api, _ in api.items():
                if k_api[0] == '$':
                    if validate:
                        self.validate_value(k, k_api[1:])
                    key += k+','
                    temp_api = api[k_api]
                    is_ok = True
                    break
                else:
                    if k == k_api:
                        key += k+':'
                        temp_api = api[k]
                        is_ok = True
                        break
            
            if not is_ok:
                raise Exception('Structure provided does not exist')
            if isinstance(v, dict) and isinstance(temp_api, dict):
                self.validate(v, temp_api, key, validate, keys)
            else:
                value = v
                if temp_api[0] == '&':
                    if validate:
                        self.validate_value(v, temp_api[1:])
                    key += v
                    value = ''
                else:
                    if validate:
                        self.validate_value(v, temp_api)
                key_val = (key, value, temp_api)
                keys.append(key_val)

    def dict_to_keys(self, _input: dict, validate: bool = True) -> tuple:
        keys = list()  # careful with class variables...
        self.validate(_input, self.api_struct, '', validate, keys)
        return keys

    @staticmethod
    def keys_to_dict(kv: tuple):
        kk = dict()
        for k, v in kv:
            o = kk
            pieces = split("[:,]", k)
            if len(pieces) >= 3:
                for idx, h in enumerate(pieces):
                    if idx == len(pieces)-2:
                        if pieces[-1] == '':
                            o[h] = v
                        else:
                            o[h] = pieces[-1]
                        o = o[h]
                        break
                    try:
                        o[h]
                    except Exception:
                        o[h] = dict()
                    o = o[h]
            else:
                raise Exception(
                    '[keys_to_dict] less than 3 elements provided!!!')
        return kk

    def sort_dict(self, item: dict) -> dict:
        """
        Sort nested dict.
        Adapted from:
            https://gist.github.com/gyli/f60f0374defc383aa098d44cfbd318eb

        Example:
             Input: {'a': 1, 'c': 3, 'b': {'b2': 2, 'b1': 1}}
             Output: {'a': 1, 'b': {'b1': 1, 'b2': 2}, 'c': 3}
        """
        return {k: self.sort_dict(v)
                if isinstance(v, dict) else v for k, v in sorted(item.items())}

    # ===================  By Args stuff  =================================
    def exists_by_args(self, scope, **kwargs) -> bool:
        """Check if some key exists in redis giving arguments"""
        search_dict = self.get_search_dict(scope, **kwargs)
        patterns = list()
        for k, v, s in self.dict_to_keys(search_dict, validate=False):
            patterns.append(k)
        # keys = list()
        for p in patterns:
            for elem in self.db_read.scan_iter(p, count=1000):
                return True
                # keys.append(elem.decode('utf-8'))
        return False

    def search_by_args(self, scope, **kwargs) -> Tuple[dict, int]:
        """Search keys in redis giving arguments"""
        search_dict = self.get_search_dict(scope, **kwargs)
        keys = self.search(search_dict)
        kv = list()
        for elem in keys:
            kv.append((elem, ''))
        # return the dict without the values
        return self.keys_to_dict(kv), len(keys)

    def get_by_args(self, scope, **kwargs) -> dict:
        """Get keys from redis giving arguments"""
        search_dict = self.get_search_dict(scope, **kwargs)
        return self.get(search_dict)

    def delete_by_args(self, scope, **kwargs) -> dict:
        """Delete keys in redis giving arguments"""
        search_dict = self.get_search_dict(scope, **kwargs)
        return self.unsafe_delete(search_dict)

    def subscribe_by_args(self, scope, function, **kwargs) -> dict:
        """Subscribe to a redis pattern giving arguments"""
        search_dict = self.get_search_dict(scope, **kwargs)
        self.loop.create_task(self.subscribe(search_dict, function))

    def dict_to_args(self, _input: dict) -> dict:
        """Get a plain args dict from the nested one"""
        for scope in _input:
            scope_name = scope
            final_dict = {'Scope': scope_name}
        for name in _input[scope_name]:
            main_name = name
            if main_name != '*':
                final_dict.update({'Name': main_name})

        def recursive(_input):
            for key, value in _input.items():
                if isinstance(value, dict):
                    for value_name in _input[key]:
                        if value_name != '*':
                            final_dict.update({key: value_name})
                        recursive(_input[key][value_name])
        recursive(_input[scope_name][main_name])
        return final_dict

    def get_search_dict(self, scope, **kwargs) -> dict:
        """Get the search dictionary from the args"""
        try:
            kwargs[scope] = kwargs['Name']
        except Exception:
            pass
        star = {scope: self.api_star[scope]}
        return self.args_to_dict(star, kwargs)

    def template_to_star(self, _input: dict) -> dict:
        new = dict()

        def changeKeys(d, n):
            for k, v in d.items():
                key = k
                if '$' in k:
                    key = "*"

                if isinstance(v, dict):
                    n[key] = dict()
                    changeKeys(v, n[key])
                else:
                    n[key] = "*"

        changeKeys(_input, new)
        return new

    def args_to_dict(self, _input: dict, _replaces: dict) -> dict:
        new = dict()
        repl = _replaces

        def changeKeys(d, n, c):
            got_some = 0
            for k, v in d.items():
                if isinstance(v, dict):
                    if k == '*':
                        got_some = 1
                        change = None
                        n[c] = dict()
                        nn = n[c]
                        break
                    if k in repl:
                        got_some = 1
                        change = repl[k]
                        n[k] = dict()
                        nn = n[k]
                        break
                else:
                    if k in repl:
                        got_some = 2
                        change = repl[k]
                        n[k] = change
                        nn = n[k]
                        break
            if got_some == 1:
                changeKeys(v, nn, change)
            elif got_some == 2:
                pass
            else:
                star_finish(d, n)

        def star_finish(d, n):
            for k, v in d.items():
                if isinstance(v, dict):
                    n[k] = dict()
                    star_finish(v, n[k])
                else:
                    n[k] = v
        changeKeys(_input, new, None)
        return new

    def update_dict(self, d: dict, u: dict):
        def update(d):
            for k, v in d.items():
                if isinstance(v, dict):
                    update(v)
                else:
                    d[k] = u
        if d == {}:
            return u
        elif u == {}:
            return d
        else:
            update(d)
        return d

    @staticmethod
    def get_from_path(base_dict: dict, path: str) -> dict:
        """ Returns dictionary from the specified path """
        curr = base_dict
        # Gets rid of first '%%' as it's unnecessary
        path = path.split("%%")[1:]
        while len(path):
            key = path.pop(0)
            curr = curr.get(key)
            # Check if path exists
            if type(curr) is not dict and len(path):
                return None
        return curr

    @staticmethod
    def set_dict(base: dict, path: str, value: dict) -> None:
        """ Appends value to dict with specified path """
        keys = path.split(
            '%%')[1:]  # Gets rid of first '%%' as it's unnecessary
        latest = keys.pop()
        for k in keys:
            base = base.setdefault(k, {})
        base.setdefault(latest, value)

    @staticmethod
    def dict_to_paths(value, path: str = '') -> list:
        """ Returns list with all dict as string paths """
        if isinstance(value, dict):
            if not value.items():
                yield from MovaiDB.dict_to_paths(False, path)
            for key, val in value.items():
                path2 = '{}%%{}'.format(path, key)
                yield from MovaiDB.dict_to_paths(val, path2)
        else:
            yield path

    @staticmethod
    def break_paths(path: str) -> list:
        """ Return list with paths broken down """
        if not isinstance(path, list):
            path = path.split("%%")[1:]
        if len(path) <= 1:
            return ["%%" + "".join(path)]
        beginning = path
        remaining = [*path]
        remaining.pop()
        return ["%%" + "%%".join(beginning)] + MovaiDB.break_paths(remaining)

    @staticmethod
    def validate_path(path: str, structure: dict) -> str:
        # Translate dict to list of paths
        struct_paths = [p for p in MovaiDB.dict_to_paths(structure)]
        p1 = path
        exists = None
        for p2 in struct_paths:
            if p1 == p2:
                exists = p2
                break
            p1_split = p1.split("%%")[1:]
            p2_split = p2.split("%%")[1:]
            if len(p2_split) == len(p1_split):
                for (k, v) in enumerate(p2_split):
                    if '$' in v:
                        p2_split[k] = p1_split[k]
                if p1_split == p2_split:
                    exists = "%%" + "%%".join(p2_split)
                    break
            elif len(p1_split) > len(p2_split):
                for (k, v) in enumerate(p2_split):
                    if '$' in v:
                        p2_split[k] = p1_split[k]
                p1_join = "%%" + "%%".join(p1_split)
                p2_join = "%%" + "%%".join(p2_split)
                for bp in MovaiDB.break_paths(p1_join):
                    if bp == p2_join:
                        exists = bp
                        break
        return exists

    @staticmethod
    def merge_dicts(self, a: dict, b: dict, path: str = None) -> dict:
        """ Merges b into a"""
        if path is None:
            path = []
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    self.merge(a[key], b[key], path + [str(key)])
                elif a[key] == b[key]:
                    pass  # same leaf value
                else:
                    raise Exception('Conflict at %s' %
                                    '.'.join(path + [str(key)]))
            else:
                a[key] = b[key]
        return a

    @staticmethod
    def calc_scope_update(old_dict: dict,
                          new_dict: dict, structure: dict) -> list:
        """ Calculate scope updates dicts """
        # Translate dict to list of paths
        old_dict_paths = [p for p in MovaiDB.dict_to_paths(old_dict)]
        # Translate dict to list of paths
        new_dict_paths = [p for p in MovaiDB.dict_to_paths(new_dict)]
        # Validate paths against structure

        old_dict_paths_valid = []
        for path in old_dict_paths:
            valid_path = MovaiDB.validate_path(path, structure)
            if valid_path:
                old_dict_paths_valid.append(valid_path)

        new_dict_paths_valid = []
        for path in new_dict_paths:
            valid_path = MovaiDB.validate_path(path, structure)
            if valid_path:
                new_dict_paths_valid.append(valid_path)

        # Merge both paths to create unique list of paths to check for differences
        paths_list = list(set(old_dict_paths_valid) |
                          set(new_dict_paths_valid))
        scope_updates = []
        for path in paths_list:
            first_dict = {}
            MovaiDB.set_dict(first_dict, path,
                              MovaiDB.get_from_path(old_dict, path))
            second_dict = {}
            MovaiDB.set_dict(second_dict, path,
                              MovaiDB.get_from_path(new_dict, path))
            to_delete = {}

            diff = DeepDiff(first_dict, second_dict)
            if diff:
                # Check differences and build to_set and to_delete dict_keys
                type_changes = diff.get('type_changes', False)
                type_changes_value = type_changes.popitem()[
                    1] if type_changes else None

                # Build to_delete key
                if type_changes_value is None \
                   or not type_changes_value.get('old_value') is None:
                    MovaiDB.set_dict(to_delete, path, '*')
                else:
                    to_delete = None

                # Build to_set key
                if type_changes_value is None \
                   or not type_changes_value.get('new_value') is None:
                    to_set = second_dict
                else:
                    to_set = None

                # Append results to list of scope updates
                scope_updates.append({
                    'path': path,
                    # If to set exists ignore to_delete
                    'to_delete': to_delete if not to_set else None,
                    'to_set': to_set
                })

        return scope_updates
