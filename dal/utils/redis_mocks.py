import asyncio
import logging
import os
import pickle
from fnmatch import fnmatch
from typing import Any, Callable, Dict, List, Optional, Type
from unittest.mock import _patch, _get_target

import redis
import aioredis


### Set to True if you want to record real interactions with Redis
### Set to False to mock Redis using pre-saved interactions
RECORD = True


logger = logging.getLogger("RedisProxies")


RECEIVER_LOOP: List[asyncio.AbstractEventLoop] = []
CHANNELS: Dict[bytes, aioredis.Channel] = {}


class _fake_redis(_patch):
    recording_dir: str

    @staticmethod
    def make_connection_class(recording_path: str) -> Type:
        class FakeConnection(redis.connection.Connection):
            """Implements a VCRpy style mock, which can record real connections
            to Redis and save them to a file. Then that file can be used
            to reproduce communications without needing Redis"""

            __responses = {}
            __last_out: List[Optional[str]] = [None]

            def __init__(self, host, port, db=0, **kwargs):
                if not RECORD:
                    with open(recording_path, "rb") as f:
                        FakeConnection.__responses = pickle.load(f)
                super().__init__(host=host, port=port, db=db, **kwargs)

            def connect(self):
                if RECORD:
                    super().connect()
                else:
                    self.on_connect()

            def can_read(self, timeout: Optional[float] = 0) -> bool:
                return super().can_read(timeout=timeout) if RECORD else False

            def send_command(self, *args, **kwargs) -> None:
                FakeConnection.__last_out[0] = f"({args}, {kwargs})"
                logger.info("send_command(%s, %s)", args, kwargs)
                if RECORD:
                    super().send_command(*args, **kwargs)
                elif args[0] == "PUBLISH":
                    loop = RECEIVER_LOOP[0]
                    channel_name, msg = args[1], args[2]
                    for pattern, channel in CHANNELS.items():
                        pattern_str = pattern.decode("utf-8")
                        if fnmatch(channel_name, pattern_str):
                            logger.warning(
                                "Publishing %s %s to %s(%s) on loop %s",
                                pattern,
                                msg,
                                channel,
                                id(channel),
                                loop,
                            )
                            loop.call_soon_threadsafe(
                                (
                                    lambda channel, pattern, msg: channel.put_nowait(
                                        (pattern, msg.encode("utf-8"))
                                    )
                                ),
                                channel,
                                pattern,
                                msg,
                            )

            def read_response(
                self, *a, **kw
            ):
                logger.warning("read_response()")
                if RECORD:
                    try:
                        value = super().read_response(*a, **kw)
                    except Exception as e:
                        logger.warning("GOT EXC: %s", e)
                        value = e

                    FakeConnection.__responses[FakeConnection.__last_out[0]] = value
                    with open(recording_path, "wb") as f:
                        pickle.dump(FakeConnection.__responses, f)
                    logger.warning("returning %s", value)
                else:
                    value = FakeConnection.__responses[FakeConnection.__last_out[0]]

                if isinstance(value, Exception):
                    raise value
                else:
                    return value

            def disconnect(self, *args: object) -> None:
                if RECORD:
                    super().disconnect(*args)

        return FakeConnection

    def __init__(self: _patch, getter: Callable[[], Any], attribute: str, recording_dir) -> None:
        super().__init__(
            getter,
            attribute,
            new=None,
            spec=None,
            create=False,
            spec_set=None,
            autospec=None,
            new_callable=None,
            kwargs={},
        )
        self.recording_dir = recording_dir

    def __call__(self, func: Callable) -> Callable:
        recording_path = os.path.join(self.recording_dir, f"{func.__name__}.pickle")
        self.new = self.make_connection_class(recording_path)
        return super().__call__(func)


def fake_redis(target, recording_dir):
    # copied from unittest.mock.patch()
    getter, attribute = _get_target(target)
    return _fake_redis(getter, attribute, recording_dir=recording_dir)


class FakeAsyncConnection(aioredis.connection.AbcConnection):
    """Basic mock connection that allows subscribing to a channel pattern (psubscribe)"""

    def __init__(self, reader, writer, *, address, encoding=None, parser=None, loop=None):
        self._pubsub_channels = CHANNELS

    def close(self):
        return

    async def wait_closed(self):
        return

    def execute_pubsub(self, command, *channels):
        channels = [aioredis.Channel(ch, is_pattern=True) for ch in channels]
        for channel in channels:
            self._pubsub_channels[channel.name] = channel
        logger.warning("Subscribe to channels %s", self._pubsub_channels)
        loop = asyncio.get_running_loop()
        if len(RECEIVER_LOOP) == 0:
            RECEIVER_LOOP.append(loop)
        fut = loop.create_future()
        fut.set_result([(None, channel.name, None) for channel in channels])
        return fut

    def execute(self, command, *args, encoding=...):
        fut = asyncio.get_running_loop().create_future()
        fut.set_result(True)
        return fut

    @property
    def closed(self):
        return False

    @property
    def db(self):
        return 0

    @property
    def encoding(self):
        return None

    @property
    def address(self):
        return "fakehost"

    @property
    def in_pubsub(self):
        return True

    @property
    def pubsub_channels(self):
        return {}

    @property
    def pubsub_patterns(self):
        return CHANNELS


class FakeAsyncPool(aioredis.ConnectionsPool):
    def _create_new_connection(self, address):
        if RECORD:
            return super()._create_new_connection(address)
        else:
            fut = asyncio.get_running_loop().create_future()
            fut.set_result(FakeAsyncConnection(None, None, address=address))
            return fut
