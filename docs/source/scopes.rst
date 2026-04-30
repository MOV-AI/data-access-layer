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

Allowed port templates
~~~~~~~~~~~~~~~~~~~~~~

The following port templates are allowed for each node type:

- `ROS1/Nodelet`:

  - `MovAI/Depends`
  - `MovAI/Dependency`
  - `ROS1/Timer`
  - `ROS1/ReconfigureClient`
  - `ROS1/ServiceClient`
  - `ROS1/ActionServer`
  - `ROS1/ActionClient`
  - `ROS1/Subscriber`
  - `ROS1/TFPublisher`
  - `ROS1/ServiceServer`
  - `ROS1/Publisher`
  - `ROS1/TFSubscriber`
  - `ROS1/NodeletClient`
  - `ROS1/NodeletServer`

- `ROS1/Node`:

  - `MovAI/Depends`
  - `MovAI/Dependency`
  - `ROS1/Timer`
  - `ROS1/ReconfigureClient`
  - `ROS1/ServiceClient`
  - `ROS1/ActionServer`
  - `ROS1/ActionClient`
  - `ROS1/Subscriber`
  - `ROS1/TFPublisher`
  - `ROS1/ServiceServer`
  - `ROS1/Publisher`
  - `ROS1/TFSubscriber`
  - `ROS1/PluginServer`

- `ROS1/Plugin`:

  - `ROS1/PluginClient`

- `MovAI/Node`:

  - `MovAI/Init`
  - `MovAI/ContextClientIn`
  - `MovAI/Depends`
  - `MovAI/Dependency`
  - `Redis/Subscriber`
  - `ROS1/Timer`
  - `ROS1/ReconfigureClient`
  - `ROS1/ServiceClient`
  - `ROS1/ActionServer`
  - `ROS1/ActionClient`
  - `ROS1/Subscriber`
  - `ROS1/TFPublisher`
  - `ROS1/ServiceServer`
  - `ROS1/Publisher`
  - `ROS1/TFSubscriber`

- `MovAI/State`:

  - `MovAI/Init`
  - `MovAI/TransitionTo`
  - `MovAI/TransitionFor`
  - `MovAI/ContextClientIn`
  - `MovAI/Depends`
  - `MovAI/Dependency`
  - `Redis/Subscriber`
  - `ROS1/Timer`
  - `ROS1/ReconfigureClient`
  - `ROS1/ServiceClient`
  - `ROS1/ActionServer`
  - `ROS1/ActionClient`
  - `ROS1/Subscriber`
  - `ROS1/TFPublisher`
  - `ROS1/ServiceServer`
  - `ROS1/Publisher`
  - `ROS1/TFSubscriber`

- `MovAI/Server`:

  - `MovAI/Init`
  - `MovAI/ContextClientIn`
  - `MovAI/Depends`
  - `MovAI/Dependency`
  - `Redis/Subscriber`
  - `ROS1/Timer`
  - `ROS1/ReconfigureClient`
  - `ROS1/ServiceClient`
  - `ROS1/ActionServer`
  - `ROS1/ActionClient`
  - `ROS1/Subscriber`
  - `ROS1/TFPublisher`
  - `ROS1/ServiceServer`
  - `ROS1/Publisher`
  - `ROS1/TFSubscriber`
  - `AioHttp/Http`
  - `AioHttp/Websocket`

- `ROS2/Node`:

  - `MovAI/Depends`
  - `MovAI/Dependency`
  - `ROS2/Subscriber`
  - `ROS2/Publisher`
  - `ROS2/ServiceClient`
  - `ROS2/ServiceServer`

- `ROS2/Launch`:

  - `MovAI/Depends`
  - `MovAI/Dependency`

Mandatory port templates
~~~~~~~~~~~~~~~~~~~~~~~~

From the above rules, we can derive the following mandatory port templates for each node type:

- `ROS1/Nodelet`: a port with either `ROS1/NodeletClient` or `ROS1/NodeletServer` template
- `ROS1/Node`: no mandatory port templates
- `ROS1/Plugin`: a port with `ROS1/PluginClient` template
- `MovAI/Node`: no mandatory port templates
- `MovAI/State`: a port with either a `MovAI/TransitionTo` or `MovAI/TransitionFor` template
- `MovAI/Server`: a port with either a `AioHttp/Http` or `AioHttp/Websocket` template
- `ROS2/Node`: no mandatory port templates
- `ROS2/Launch`: no mandatory port templates

Sensible default ports
~~~~~~~~~~~~~~~~~~~~~~

Sensible default ports for each node type (to be added autocamatically when creating a node of that type):

- `ROS1/Nodelet`: a port named `nodelet_client` with `ROS1/NodeletClient` template
- `ROS1/Node`: no ports
- `ROS1/Plugin`: a port named `plugin` with `ROS1/PluginClient` template
- `MovAI/Node`: a port named `init` with `MovAI/Init` template
- `MovAI/State`: a port named `in` with a `MovAI/TransitionTo` template and a port named `out` with a `MovAI/TransitionFor` template
- `MovAI/Server`: a port named `http` with `AioHttp/Http` template
- `ROS2/Node`: no ports
- `ROS2/Launch`: a port named `depends` with `MovAI/Depends` template
