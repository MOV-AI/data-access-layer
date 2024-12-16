"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020
   - Dor Marcus (dor@mov.ai) - 2023

   Websocket to Redis Subscriber
"""
import asyncio
import json
import sys
import uuid

import aioredis
import yaml
from aiohttp import web
from aiohttp import WSMsgType
from movai_core_shared.logger import Log

from dal.movaidb import MovaiDB
from dal.movaidb import RedisClient

try:
    from gd_node.callback import GD_Callback

    gdnode_modules = {"GD_Callback": GD_Callback}
except ImportError:
    gdnode_modules = {}

LOGGER = Log.get_logger("WSRedisSub")


class WSRedisSub:
    """API for dynamic subscriber to redis"""

    def __init__(self, app: web.Application, _node_name: str, **_ignore):
        self.topic = "/ws/subscriber"
        self.http_endpoint = "/subscriber"
        self.node_name = _node_name
        self.app = app

        self.databases = None
        self.connections = {}
        self.tasks = {}
        self.movaidb = MovaiDB()
        self.loop = asyncio.get_event_loop()
        self.recovery_mode = False

        # API available actions
        self.actions = {
            "subscribe": self.add_pattern,
            "unsubscribe": self.remove_pattern,
            "list": self.get_patterns,
            "execute": self.execute,
        }

        # Add API endpoint
        # <http/ws.py>

        # create database client
        self.loop.create_task(self.connect())

    async def connect(self):
        # create database client
        self.databases = await RedisClient.get_client()

    async def acquire(self, retries: int = 3):
        """Acquire a Redis connection with retry logic, handle cancellations, health checks, and remove unhealthy connections"""
        LOGGER.debug(f"Acquiring connection. Retries left: {retries}")
        if retries == 0:
            return None
        try:
            await self.connect()
            conn = await asyncio.wait_for(self.databases.slave_pubsub.acquire(), timeout=30)

            # Check if the connection is healthy
            if await conn.execute('PING') != b'PONG':
                raise Exception("Failed to receive PONG response")
            return conn
        except asyncio.CancelledError:
            LOGGER.debug("Acquire operation was cancelled")
            return None
        except asyncio.TimeoutError:
            LOGGER.error("Acquire operation timed out")
            return None
        except Exception as e:
            LOGGER.error(f"Error acquiring connection: {e}. Retrying...")
            # Close the connection if it's already acquired but unhealthy
            if 'conn' in locals() and conn:
                conn.close()
                await conn.wait_closed()
            await asyncio.sleep(2 ** (3 - retries))  # Exponential backoff
            return await asyncio.wait_for(self.acquire(retries - 1), timeout=60)

    async def release(self, conn_id):
        conn = self.connections[conn_id]["subs"]
        if conn:
            self.loop.create_task(conn.wait_closed())
        del self.connections[conn_id]
        if self.recovery_mode:
            await self.databases.shutdown()
            self.recovery_mode = False

    async def close(self, ws: web.WebSocketResponse, conn_id: str):
        """Close the WebSocket and clean up tasks and connections"""
    
        for task in self.tasks[conn_id]:
            if not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=2)
                except asyncio.CancelledError:
                    LOGGER.debug("[WSRedisSub.close] Task was properly cancelled "+ str(task))
                except asyncio.TimeoutError:
                    LOGGER.error("[WSRedisSub.close] Waited 2 seconds for it. Force cancelling! "+ str(task))

        self.tasks.pop(conn_id, None)
        await self.release(conn_id)
        await ws.close()

    async def print_current_task_count(self):
        tasks = asyncio.Task.all_tasks(loop=asyncio.get_event_loop())
        LOGGER.warning(f"Number of current tasks: {len(tasks)}")

    async def handler(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connections"""
        connection_queue = asyncio.Queue()
        lock = asyncio.Lock()
        conn = None

        ws_resp = web.WebSocketResponse()
        await ws_resp.prepare(request)
        
        conn_id = uuid.uuid4().hex
        self.connections[conn_id] = {"conn": connection_queue, "subs": conn, "patterns": []}

        # Ensure the loop is running and get it
        loop = asyncio.get_event_loop()
        write_task = loop.create_task(self.write_websocket_loop(ws_resp, connection_queue, lock))
        self.tasks[conn_id] = [write_task]

        try:
            try:
                #_conn = await self.acquire()
                _conn = await asyncio.wait_for(self.acquire(), timeout=160)
                if _conn:
                    conn = aioredis.Redis(_conn)
                    self.connections[conn_id]["subs"] = conn
                    
                else:
                    LOGGER.error(f"Error acquiring Redis connection:")
                    self.recovery_mode = True
                    raise Exception("Unable to acquire Redis connection") 
            except Exception as error:
                LOGGER.error(f"Exception: {error}")
                output = {"event": None, "patterns": None, "error": "{error}"}
                await self.push_to_queue(connection_queue, output)
                raise

            async for ws_msg in ws_resp:
                if ws_msg.type == WSMsgType.TEXT:
                    try:
                        if ws_msg.data == "close":
                            break
                        data = ws_msg.json()
                        if "event" in data:
                            if data["event"] == "execute":
                                _config = {
                                    "conn_id": conn_id,
                                    "conn": conn,
                                    "callback": data.get("callback"),
                                    "func": data.get("func"),
                                    "data": data.get("data"),
                                }
                            else:
                                _config = {
                                    "conn_id": conn_id,
                                    "conn": conn,
                                    "_pattern": data.get("pattern"),
                                }
                            await self.actions[data["event"]](**_config)
                        else:
                            raise KeyError("Missing 'event' key in WebSocket message")
                    except aioredis.PoolClosedError:
                        LOGGER.debug("Connection closed while executing.")
                        output = {"event": None, "patterns": None, "error": "Connection was closed"}
                        await self.push_to_queue(connection_queue, output)
                    except Exception as e:
                        LOGGER.error(f"Error handling WebSocket message: {e}")
                        output = {"event": None, "patterns": None, "error": str(e)}
                        await self.push_to_queue(connection_queue, output)
                elif ws_msg.type == WSMsgType.ERROR:
                    LOGGER.error(f"WebSocket connection closed with exception: {ws_resp.exception()}")
                else:
                    LOGGER.error(f"Unexpected WebSocket message type: {ws_msg.type}")
        finally:
            # Drain the messaging queue before closing the connection
            LOGGER.debug(f"Closing everything and cancelling ongoing async tasks!{conn_id}")
            attempts = 0
            while connection_queue.qsize() > 0 and attempts < 5:
                LOGGER.debug(f"Waiting for websocket writter to drain queued responses.Attempt [{attempts}]. Messaging queue size is :{connection_queue.qsize()}")
                await asyncio.sleep(2)
                attempts += 1

            async with lock:
                await self.close(ws_resp, conn_id)
        return ws_resp
        
    async def write_websocket_loop(
        self,
        ws_resp: web.WebSocketResponse,
        connection_queue: asyncio.Queue,
        lock: asyncio.Lock,
    ):
        """Write messages to websocket.
        args:
            ws_resp: websocket _response
            connection_queue: queue to write messages to Websocket
        """
        try:
            while True:
                msg = await connection_queue.get()
                #used for debugging
                #await self.print_current_task_count()
                async with lock:
                    if (
                        ws_resp is not None
                        and not ws_resp.closed
                        and not ws_resp._closing
                    ):
                        await ws_resp.send_json(msg)
                    else:
                        break
        except asyncio.CancelledError:
            LOGGER.debug("Stopping websocket writter.")
        except Exception as err:
            LOGGER.error("Writing back to websocket failed! " + str(err))
            

    def convert_pattern(self, _pattern: dict) -> str:
        try:
            pattern = _pattern.copy()
            scope = pattern.pop("Scope")
            search_dict = self.movaidb.get_search_dict(scope, **pattern)

            keys = []
            for elem in self.movaidb.dict_to_keys(search_dict, validate=False):
                key, _, _ = elem
                keys.append(key)
            return keys
        except Exception as e:
            LOGGER.error(e)
            return None

    async def add_pattern(self, conn_id, conn, _pattern, **ignore):
        """Add pattern to subscriber"""
        LOGGER.info(f"add_pattern{_pattern}")

        
        self.connections[conn_id]["patterns"].append(_pattern)
        key_patterns = []
        if isinstance(_pattern, list):
            for patt in _pattern:
                key_patterns.extend(self.convert_pattern(patt))
        else:
            key_patterns = self.convert_pattern(_pattern)
        keys = []
        tasks = []
        for key_pattern in key_patterns:
            pattern = "__keyspace@*__:%s" % (key_pattern)
            channel = await conn.psubscribe(pattern)
            loop = asyncio.get_event_loop()
            read_task = loop.create_task(self.wait_message(conn_id, channel[0]))
            self.tasks[conn_id].append(read_task)

            # add a new get_keys task
            tasks.append(self.get_keys(key_pattern))

        # wait for all get_keys tasks to run
        _values = await asyncio.gather(*tasks)

        for value in _values:
            for key in value:
                keys.append(key)

        # get all values
        values = await self.mget(keys)

        ws = self.connections[conn_id]["conn"]
        await self.push_to_queue(
            ws, {"event": "subscribe", "patterns": [_pattern], "value": values}
        )

    async def remove_pattern(self, conn_id, conn, _pattern, **ignore):
        """Remove pattern from subscriber"""
        LOGGER.debug(f"removing pattern {_pattern} {conn}")
        if _pattern in self.connections[conn_id]["patterns"]:
            self.connections[conn_id]["patterns"].remove(_pattern)

        key_patterns = self.convert_pattern(_pattern)
        for key_pattern in key_patterns:
            pattern = "__keyspace@*__:%s" % (key_pattern)
            await conn.punsubscribe(pattern)

        ws = self.connections[conn_id]["conn"]
        await self.push_to_queue(ws, {"event": "unsubscribe", "patterns": [_pattern]})

    async def get_patterns(self, conn_id, conn, **ignore):
        """Get list of patterns"""

        output = {"event": "list", "patterns": self.connections[conn_id]["patterns"]}

        await self.push_to_queue(self.connections[conn_id]["conn"], output)

    async def wait_message(self, conn_id, channel):
        """Receive messages from redis subscriber"""
        output = {"event": "unknown"}
        try:
            while await channel.wait_message():
                ws = self.connections[conn_id]["conn"]
                msg = await channel.get(encoding="utf-8")
                value = ""
                key = msg[0].decode("utf-8").split(":", 1)[1]
                # match the key triggerd with any patterns
                match_patterns = []
                for dict_pattern in self.connections[conn_id]["patterns"]:
                    patterns = self.convert_pattern(dict_pattern)
                    for pattern in patterns:
                        if all(piece in key for piece in pattern.split("*")):
                            match_patterns.append(dict_pattern)
                if msg[1] in ("set", "hset", "hdel"):
                    key_in_dict = await self.get_value(key)
                else:
                    key_in_dict = self.movaidb.keys_to_dict([(key, value)])
                output.update(
                    {
                        "event": msg[1],
                        "patterns": match_patterns,
                        "key": key_in_dict,
                        "value": value,
                    }
                )

                await self.push_to_queue(ws, output)
        except asyncio.CancelledError:
            LOGGER.debug("Wait task was cancelled, socket is closing!")
        except Exception as err:
            LOGGER.error(str(err))

    async def get_keys(self, pattern: str) -> list:
        """Get all redis keys in pattern"""
        _conn = self.databases.db_slave
        keys = await _conn.keys(pattern)

        # sort keys
        keys = [key.decode("utf-8") for key in keys]
        keys.sort(key=str.lower)
        keys = [key.encode("utf-8") for key in keys]

        return keys

    async def get_value(self, keys):
        """Get key value"""
        # TODO DEPRECATED NOT YET
        output = {}
        _conn = self.databases.db_slave
        key_values = []
        if not isinstance(keys, list):
            keys = [keys]
        tasks = []
        for key in keys:
            tasks.append(self.fetch_value(_conn, key))
        values = await asyncio.gather(*tasks)
        for key, value in values:
            if isinstance(key, bytes):
                key_values.append((key.decode("utf-8"), value))
            else:
                key_values.append((key, value))
        output = self.movaidb.keys_to_dict(key_values)
        return output

    async def fetch_value(self, _conn, key):
        try:
            type_ = await _conn.type(key)
            type_ = type_.decode("utf-8")
            if type_ == "string":
                value = await _conn.get(key)
                value = self.movaidb.decode_value(value)
            if type_ == "list":
                value = await _conn.lrange(key, 0, -1)
                value = self.movaidb.decode_list(value)
            if type_ == "hash":
                value = await _conn.hgetall(key)
                value = self.movaidb.decode_hash(value)
        except (aioredis.PoolClosedError, aioredis.ConnectionForcedCloseError):
            LOGGER.debug("Connection closed while fetching value")
        try:  # Json cannot dump ROS Messages
            json.dumps(value)
        except:
            try:
                value = yaml.load(str(value), Loader=yaml.SafeLoader)
            except:
                value = None
        return (key, value)

    async def mget(self, keys):
        """get values using redis mget"""
        _conn = self.databases.db_slave
        output = []
        values = []

        try:
            values = await _conn.mget(*keys)

        except Exception as e:
            return

        for key, value in zip(keys, values):
            try:
                if isinstance(key, bytes):
                    key = key.decode("utf-8")
                if not value:
                    # not a string
                    value = await self.get_key_val(_conn, key)
                else:
                    value = self.__decode_value("string", value)

            except ValueError:
                value = None

            output.append((key, value))

        return self.movaidb.keys_to_dict(output)

    async def get_key_val(self, _conn, key):
        """get value by type"""

        type_ = await _conn.type(key)

        # get redis type
        type_ = type_.decode("utf-8")

        # get value by redis type
        if type_ == "string":
            value = await _conn.get(key)
        elif type_ == "list":
            value = await _conn.lrange(key, 0, -1)
        elif type_ == "hash":
            value = await _conn.hgetall(key)
        else:
            raise ValueError(f"Unexpected type: {type_} for key: {key}")

        # return decode value
        return self.__decode_value(type_, value)

    def __decode_value(self, type_, value):
        """decode value by type"""
        if type_ == "string":
            value = self.movaidb.decode_value(value)
        elif type_ == "list":
            value = self.movaidb.decode_list(value)
        elif type_ == "hash":
            value = self.movaidb.sort_dict(self.movaidb.decode_hash(value))
        else:
            raise ValueError(f"Unexpected type: {type_} for value: {value}")

        try:  # Json cannot dump ROS Messages
            json.dumps(value)
        except Exception:
            try:
                value = yaml.load(str(value), Loader=yaml.SafeLoader)
            except Exception:
                value = None

        return value

    async def execute(self, conn_id, conn, callback, data=None, **ignore):
        """
        event: execute
        execute specific callback
        Request implemented in Database.js
        """

        ws = self.connections[conn_id]["conn"]

        try:
            # get callback
            callback = GD_Callback(
                callback, self.node_name, "cloud", _update=False
            )

            # update callback with request data
            callback.user.globals.update({"msg": data, "response": {}})
            # execute callback
            callback.execute(data)

            # create response
            response = {"event": "execute", "result": None, "patterns": ["execute"]}
            _response = callback.updated_globals["response"]

            if isinstance(_response, dict):
                response.update(_response)
            else:
                response["result"] = _response

            # send response
            await self.push_to_queue(ws, response)

        except Exception:
            error = f"{str(sys.exc_info()[1])} {sys.exc_info()}"
            await self.push_to_queue(
                ws,
                {
                    "event": "execute",
                    "callback": callback,
                    "result": None,
                    "error": error,
                },
            )

    async def push_to_queue(self, conn: asyncio.Queue, data):
        """send json data"""
        try:
            await conn.put(data)
        except Exception as e:
            LOGGER.error(str(e))