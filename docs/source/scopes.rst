Scopes
======================

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
  - `ROS1` node types cannot have ports with `ROS2` port types
  - `ROS2` node types cannot have ports with `ROS1` port types
  - Only `MovAI/State` can have ports with `MovAI/Transition*` port type
  - Only `ROS1/Plugin` can have ports with `ROS1/PluginClient` port type
  - Only `ROS1/Nodelet` can have ports with `ROS1/Nodelet*` port type
  - Only `MovAI/Server` can have ports with `AioHttp/*` port type

Given these rules, when the user is creating a Node the UI can:

- For `ROS1/Plugin`: automatically add a `ROS1/PluginClient` port
- For `MovAI/Node`: automatically add a `MovAI/Init` port
- For `MovAI/State`: automatically add a `MovAI/TransitionTo` port
- For `MovAI/Server`: automatically add an `AioHttp/Http` port
