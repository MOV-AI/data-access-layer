Robot Parameters
================

The `Robot` class provides a mechanism to manage parameters associated with a robot. Each parameter has the following attributes:

- **Value**: The current value of the parameter.
- **TTL**: Time-to-live in seconds (`None | int`). This attribute is **optional**. If not set (default is `None`), the parameter's `Value` will persist indefinitely. If set to an integer, the parameter's `Value` will automatically reset to `None` after the specified number of seconds.

Additionally, when a parameter's `Value` expires (due to TTL), an `expired` event is sent to any subscribers monitoring the parameter via the websockets events mechanism.

**Important:** If the `TTL` attribute is not set, no expiration will occur, and the parameter's `Value` will remain unchanged until explicitly modified.

Usage
-----

Setting a Parameter's Value
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To set the value of an existing parameter or create a new one:

.. code-block:: python

    robot = FleetRobot("robot_id")
    robot.Parameter["parameter_name"].Value = "new_value"

If the parameter does not exist, it will be created automatically.

Setting a Parameter with TTL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To set a parameter with a TTL (optional):

.. code-block:: python

    robot = FleetRobot("robot_id")
    robot.Parameter["parameter_name"].TTL = 10  # TTL in seconds
    robot.Parameter["parameter_name"].Value = "temporary_value"

In this example, the `Value` of the parameter will reset to `None` after 10 seconds, and an `expired` event will be sent to subscribers.

If the `TTL` is not set, the parameter's `Value` will persist indefinitely.

Example: Creating and Using Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    robot = FleetRobot("robot_id")

    # Create a parameter without TTL (no expiration)
    robot.Parameter["mesh"].Value = "mesh_name"

    # Create a parameter with TTL
    robot.Parameter["status"].TTL = 5  # Expires after 5 seconds
    robot.Parameter["status"].Value = "active"

    # Accessing parameter values
    print(robot.Parameter["mesh"].Value)  # Output: "mesh_name"
    print(robot.Parameter["status"].Value)  # Output: "active"

    # After 5 seconds, the status parameter will expire
    # and its value will reset to None.

Subscribing to Parameter Events
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `expired` event is sent to subscribers when a parameter's `Value` expires. To monitor these events, use the websockets events mechanism provided by the system.

Notes
-----

- The `TTL` attribute is **optional**. If not set, the parameter's `Value` will persist indefinitely.
- The `expired` event is only triggered when a `TTL` is set and the `Value` expires.
- Parameters without a `TTL` will never expire unless explicitly modified.

This functionality allows for flexible and time-sensitive parameter management for robots in the system.