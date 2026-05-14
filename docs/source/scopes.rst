Scopes
======

Scopes are the main data structure used in the data access layer.
They are used to store and retrieve data from the key value database.

The following sections describe the different types of scopes and how they are used in the data access layer.

The fllowing scopes exist in the data access layer:

- Alert
- Application
- Callback
- Configuration
- FleetRobot
- Flow
- Form
- Message
- Node
- Package
- Ports
- Robot
- Role
- StateMachine
- System
- Translation
- User
- Widget

Node
----

Specific validations
~~~~~~~~~~~~~~~~~~~~

Besides the JSON schema validation, Node scopes have some specific validations:

- The `Type` field must be a valid node type
- The `PortsInst` field is validated against the node `Type` with:

  - Type must be one of the defined NODE_TYPES
  - If Type is in ROS1 category, PortsInst cannot have ROS2 templates
  - If Type is in ROS2 category, PortsInst cannot have ROS1 templates
  - If Type is MovAI/State, PortsInst must have at least one transition template
  - If Type is not MovAI/State, PortsInst cannot have transition templates
  - If Type is ROS1/Plugin, PortsInst must have at least one ROS1/PluginClient template
  - If Type is not ROS1/Plugin, PortsInst cannot have ROS1/PluginClient templates
  - If Type is ROS1/Nodelet, PortsInst must have at least one ROS1/NodeletClient or ROS1/NodeletServer template
  - If Type is not ROS1/Nodelet, PortsInst cannot have ROS1/NodeletClient or ROS1/NodeletServer templates
  - If Type is MOVAI/Server, PortsInst must have at least one MOVAI http template
  - If Type is not MOVAI/Server, PortsInst cannot have MOVAI http templates

Allowed I/O templates
~~~~~~~~~~~~~~~~~~~~~

The following I/O templates are allowed for each node type:

- `ROS1/Nodelet`:

  - `MovAI/Depends`
  - `MovAI/Dependency`
  - `ROS1/ActionClient`
  - `ROS1/ActionServer`
  - `ROS1/Bag`
  - `ROS1/NodeletClient`
  - `ROS1/NodeletServer`
  - `ROS1/ParameterServer`
  - `ROS1/PluginServer`
  - `ROS1/Publisher`
  - `ROS1/ReconfigureClient`
  - `ROS1/ReconfigureServer`
  - `ROS1/ServiceClient`
  - `ROS1/ServiceServer`
  - `ROS1/Subscriber`
  - `ROS1/TFPublisher`
  - `ROS1/TFSubscriber`
  - `ROS1/Timer`
  - `ROS1/TopicHz`

- `ROS1/Node`:

  - `MovAI/Depends`
  - `MovAI/Dependency`
  - `ROS1/ActionClient`
  - `ROS1/ActionServer`
  - `ROS1/Bag`
  - `ROS1/ParameterServer`
  - `ROS1/PluginServer`
  - `ROS1/Publisher`
  - `ROS1/ReconfigureClient`
  - `ROS1/ReconfigureServer`
  - `ROS1/ServiceClient`
  - `ROS1/ServiceServer`
  - `ROS1/Subscriber`
  - `ROS1/TFPublisher`
  - `ROS1/TFSubscriber`
  - `ROS1/Timer`
  - `ROS1/TopicHz`

- `ROS1/Plugin`:

  - `ROS1/PluginClient`

- `MovAI/Node`:

  - `MovAI/ContextClient`
  - `MovAI/ContextServer`
  - `MovAI/Dependency`
  - `MovAI/Depends`
  - `MovAI/Init`
  - `ROS1/ActionClient`
  - `ROS1/Bag`
  - `ROS1/ParameterServer`
  - `ROS1/Publisher`
  - `ROS1/ReconfigureClient`
  - `ROS1/ReconfigureServer`
  - `ROS1/ServiceClient`
  - `ROS1/ServiceServer`
  - `ROS1/Subscriber`
  - `ROS1/TFPublisher`
  - `ROS1/TFSubscriber`
  - `ROS1/Timer`
  - `ROS1/TopicHz`
  - `Redis/Subscriber`
  - `Redis/VarSubscriber`

- `MovAI/State`:

  - `MovAI/ContextClient`
  - `MovAI/ContextServer`
  - `MovAI/Dependency`
  - `MovAI/Depends`
  - `MovAI/Init`
  - `MovAI/TransitionFor` (aka `MovAI/TransitionOut`)
  - `MovAI/TransitionTo` (aka `MovAI/TransitionIn`)
  - `ROS1/ActionClient`
  - `ROS1/Bag`
  - `ROS1/ParameterServer`
  - `ROS1/Publisher`
  - `ROS1/ReconfigureClient`
  - `ROS1/ReconfigureServer`
  - `ROS1/ServiceClient`
  - `ROS1/ServiceServer`
  - `ROS1/Subscriber`
  - `ROS1/TFPublisher`
  - `ROS1/TFSubscriber`
  - `ROS1/Timer`
  - `ROS1/TopicHz`
  - `Redis/Subscriber`
  - `Redis/VarSubscriber`

- `MovAI/Server`:

  - `MovAI/ContextClient`
  - `MovAI/ContextServer`
  - `MovAI/Dependency`
  - `MovAI/Depends`
  - `MovAI/Init`
  - `ROS1/ActionClient`
  - `ROS1/Bag`
  - `ROS1/ParameterServer`
  - `ROS1/Publisher`
  - `ROS1/ReconfigureClient`
  - `ROS1/ReconfigureServer`
  - `ROS1/ServiceClient`
  - `ROS1/ServiceServer`
  - `ROS1/Subscriber`
  - `ROS1/TFPublisher`
  - `ROS1/TFSubscriber`
  - `ROS1/Timer`
  - `ROS1/TopicHz`
  - `Redis/Subscriber`
  - `Redis/VarSubscriber`
  - `AioHttp/Http`
  - `AioHttp/Websocket`

- `ROS2/Node`:

  - `MovAI/Depends`
  - `MovAI/Dependency`
  - `ROS2/Publisher`
  - `ROS2/ServiceClient`
  - `ROS2/ServiceServer`
  - `ROS2/Subscriber`
  - `ROS2/ActionServer`
  - `ROS2/ActionClient`

- `ROS2/Launch`:

  - `MovAI/Depends`
  - `MovAI/Dependency`

Mandatory I/O templates
~~~~~~~~~~~~~~~~~~~~~~~~

From the above rules, we can derive the following mandatory I/O templates for each node type:

- `ROS1/Nodelet`: a port with either `ROS1/NodeletClient` or `ROS1/NodeletServer` template
- `ROS1/Node`: no mandatory I/O templates
- `ROS1/Plugin`: a port with `ROS1/PluginClient` template
- `MovAI/Node`: no mandatory I/O templates
- `MovAI/State`: a port with either a `MovAI/TransitionTo` or `MovAI/TransitionFor` template
- `MovAI/Server`: a port with either a `AioHttp/Http` or `AioHttp/Websocket` template
- `ROS2/Node`: no mandatory I/O templates
- `ROS2/Launch`: no mandatory I/O templates

Sensible default ports
~~~~~~~~~~~~~~~~~~~~~~

Sensible default ports for each node type (to be added autocamatically when creating a node of that type):

- `ROS1/Nodelet`:

  - a port named `nodelet_client` with `ROS1/NodeletClient` template

- `ROS1/Node`:

  - a port named `depends` with `MovAI/Depends` template

- `ROS1/Plugin`:

  - a port named `plugin` with `ROS1/PluginClient` template

- `MovAI/Node`:

  - a port named `depends` with `MovAI/Depends` template
  - a port named `init` with `MovAI/Init` template

- `MovAI/State`:

  - a port named `init` with `MovAI/Init` template
  - a port named `in` with a `MovAI/TransitionTo` template
  - a port named `out` with a `MovAI/TransitionFor` template

- `MovAI/Server`:

  - a port named `depends` with `MovAI/Depends` template
  - a port named `init` with `MovAI/Init` template
  - a port named `http` with `AioHttp/Http` template

- `ROS2/Node`:

  - a port named `depends` with `MovAI/Depends` template

- `ROS2/Launch`:

  - a port named `depends` with `MovAI/Depends` template

Ports (I/O templates)
---------------------

Ports are complex structures based on the following concepts:

- Transports: the base communication mechanism used by the protocol, e.g. ROS1, ROS2, Redis, AioHttp, MovAI
- Protocols and primitives (direction): the specific communication pattern used by the port, e.g. Publisher, Subscriber
  - In MovAI `Protocol` is used to identify both the protocol and the primitive
- I/O templates: configuration of a transport and protocol + primitive, e.g. MovAI/ContextClient
  - This is the structure that can actually be added to a node. It can be an in port, an out port, or both.

Each Transport has the following I/O templates available:

- `ROS1`:

  - `ROS1/ActionClient`
  - `ROS1/ActionServer`
  - `ROS1/Bag`
  - `ROS1/NodeletClient`
  - `ROS1/NodeletServer`
  - `ROS1/ParameterServer`
  - `ROS1/PluginClient`
  - `ROS1/PluginServer`
  - `ROS1/Publisher`
  - `ROS1/ReconfigureClient`
  - `ROS1/ReconfigureServer`
  - `ROS1/ServiceClient`
  - `ROS1/ServiceServer`
  - `ROS1/Subscriber`
  - `ROS1/TFPublisher`
  - `ROS1/TFSubscriber`
  - `ROS1/Timer`
  - `ROS1/TopicHz`

- `ROS2`:

  - `ROS2/Publisher`
  - `ROS2/ServiceClient`
  - `ROS2/ServiceServer`
  - `ROS2/Subscriber`
  - `ROS2/ActionServer`
  - `ROS2/ActionClient`

- `MovAI`:

  - `MovAI/ContextClient`
  - `MovAI/ContextServer`
  - `MovAI/Dependency`
  - `MovAI/Depends`
  - `MovAI/Init`
  - `MovAI/TransitionFor` (aka `MovAI/TransitionOut`)
  - `MovAI/TransitionTo` (aka `MovAI/TransitionIn`)

- `Redis`:

  - `Redis/Subscriber`
  - `Redis/VarSubscriber`

- `AioHttp`:

  - `AioHttp/Http`
  - `AioHttp/Websocket`
