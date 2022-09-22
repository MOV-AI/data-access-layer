# Mov.ai Core Module

This is part of Mov.ai and is responsible for implementing system core functions like Logging, Resources, Plugin system

## Implementation

Classes Available:
- Log, LogAdapter
- Plugin, PluginManager, SinglePluginManager
- Resource, ResourcePlugin
- Template

## Log and LogAdapter

A simple logger, for now is missing the integration with the time-series database, should be implemented

Usage:

```
logger = Log.get_logger("backup.mov.ai")
log.info("Backup job started: %s", job_id)
```

## Plugin, PluginManager and SinglePluginManager

A framework to help on developing plugins inside Mov.ai
- Every plugin in Mov.ai implements the ```Plugin``` interface
- The PluginManager and SinglePluginManager implements the logic of loading automatically the plugin when needed
- The PluginManager is to be used when there is needed to load multiple plugins
- Thin SinglePluginManager is used when only one instance of a plugin may exists

Usage:

First define the Plugin Interface and PluginManager
```File: movai/data/persistence.py```
```
class PersistencePlugin(Plugin):
    """
    A interface for a workspace plugin
    """

    @abstractproperty
    def versioning(self):
        """
        returns if this plugin supports versioning
        """

class Persistence(PluginManager):
    """
    Implements an interface for accessing the persistance
    layer
    """
    logger = Log.get_logger("persistence.mov.ai")

    @classmethod
    def plugin_class(cls):
        """
        Get current class plugin
        """
        return "persistence"
```

Then implement the interface and register the plugin in the Manager
```File: movai/plugins/persistence/redis/redis.py```
```
class RedisPlugin(PersistencePlugin):

    @PersistencePlugin.versioning.getter
    def versioning(self):
        """
        returns if this plugin supports versioning
        """
        return False

Persistence.register_plugin("redis", RedisPlugin)
```

The plugin wil be avaialable using:
```
plugin = Persistence.get_plugin_class("redis")
```

## Resource and ResourcePlugin

Implements an abstraction to access to resources, it allows to implement different plugins to load resources from remote locations  

Usage:
```
buffer = Resource.read_text("file://tests/resources/file.txt")
text = str(buffer.read())
```

## Template

A simple helper class that encapsulates dicts on a SimpleNamespace

Usage:
```
protocol_config = {
    "name": str,
    "parameters": dict,
}

callback_config = {
    "name": str,
    "libs": dict,
    "file": str
}

port_config = {
    "name": str,
    "direction": str,
    "protocol": protocol_config,
    "callback": callback_config
}

node_config = {
    "logfile": str,
    "name": str,
    "parameters": dict,
    "ports": [port_config]
}

c = Template.load("node.json", node_config, "./tests/configs")

print(c.name)
print(c.logfile)
print(c.ports[0].name)
```
