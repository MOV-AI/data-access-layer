import asyncio
from dal.movaidb.database import MovaiDB


class ContextMsg:
    """Message for Context
        data -> dictionary of full context table
        changed -> dictionary only of values changed
    """
    def __init__(self, id={}, data={}, changed={}):
        self.data = data
        self.changed = changed
        self.id = id


class ContextProtocolIn:
    def __init__(self, callback: callable, params: dict, **ignore) -> None:
        self._callback = callback
        self.stack = params.get('Namespace', '')
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.register_sub())

    async def register_sub(self) -> None:
        """Subscribe to key."""
        pattern = {'Var': {'context': {'ID': {self.ID: {'Parameter': '**'}}}}}
        databases = await MovaiDB.AioRedisClient.get_client()
        await MovaiDB('local', loop=self.loop, databases=databases).\
            subscribe_channel(pattern, self.callback_wrapper)

    def callback_wrapper(self, msg):
        """Executes callback"""
        key = msg[0].decode('utf-8')
        changed_fields = list(msg[1].split(' '))
        dict_key = MovaiDB().keys_to_dict([(key, '')])
        full_table = MovaiDB('local').get_hash(dict_key)

        changed = {item: full_table[item] for item in changed_fields}

        _id = full_table.pop('_id')
        changed.pop('_id')

        msg = ContextMsg(id=_id, data=full_table, changed=changed)
        self._callback.execute(msg)


class ContextClientIn(ContextProtocolIn):
    def __init__(self, callback: callable, params: dict, **kwargs) -> None:
        super().__init__(callback, params, **kwargs)

    @property
    def ID(self):
        return self.stack + "_TX"


class ContextServerIn(ContextProtocolIn):
    def __init__(self, callback: callable, params: dict, **kwargs) -> None:
        super().__init__(callback, params, **kwargs)

    @property
    def ID(self):
        return self.stack + "_RX"


class ContextProtocolOut:
    def __init__(self, node_name: str, params: dict) -> None:
        """Init"""
        self.stack = params.get('Namespace', '')
        self._node_name = node_name

    def send(self, msg):
        """Send function"""

        if not isinstance(msg, dict):
            raise Exception('Wrong message type, this should be a dictionary')

        msg.update({'_id': self._node_name})
        to_send = {'Var': {'context': {'ID': {self.ID: {'Parameter': msg}}}}}
        MovaiDB('local').hset_pub(to_send)


class ContextClientOut(ContextProtocolOut):
    def __init__(self, node_name: str, params: dict) -> None:
        super().__init__(node_name, params)

    @property
    def ID(self):
        return self.stack + "_RX"


class ContextServerOut(ContextProtocolOut):
    def __init__(self, node_name: str, params: dict) -> None:
        super().__init__(node_name, params)

    @property
    def ID(self):
        return self.stack + "_TX"
