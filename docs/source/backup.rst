Mobdata CLI Tool
=================

Import, Export and Remove Documents
-------------------------------------

To import, export or remove documents from the database, use the following commands:

.. code-block:: bash

    mobdata import <args>
    mobdata export <args>
    mobdata remove <args>

For information on the available arguments see:

.. code-block:: bash

    mobdata --help

Using mobdata along with a manifest file the working directory must have the following structure:

.. code-block:: bash

    ├── manifest.txt
    └── metadata
        ├── Annotation
        │   └── <name>.json
        ├── Callback
        │   ├── <name>.json
        │   └── <name>.py
        ├── Configuration
        │   ├── <name>.json
        │   └── <name>.yaml
        ├── Flow
        │   └── <name>.json
        ├── GraphicScene
        │   └── <name>.json
        ├── Layout
        │   └── <name>.json
        ├── Node
        │   └── <name>.json
        ├── SharedDataEntry
        │   └── <name>.json
        ├── SharedDataTemplate
        │   └── <name>.json
        └── Translation
            ├── <name>_fr.po
            ├── <name>.json
            └── <name>_pt.po

Searching for Usages of Nodes and Flows
----------------------------------------
The `mobdata` tool supports searching for Node and Flow usage across the system through the `usage-search` command.
This command can be used to identify where specific nodes or flows are utilized, either directly or indirectly (recursively).

Options
~~~~~~~~~~~~~~~~~~~~~
- `--verbose` / `-v`: Enable debug output and show full JSON results

Commands
~~~~~~~~~~~~~~~~~~~~~

Search for Node Usage
^^^^^^^^^^^^^^^^^^^^

Search for where a specific node template is used across all flows:

.. code-block:: bash

  # Search for all usages of a node
  mobdata usage-search node <node-name>

Search for Flow Usage
^^^^^^^^^^^^^^^^^^^^

Search for where a specific flow is used as a subflow in other flows:

.. code-block:: bash

  # Search for all usages of a flow
  mobdata usage-search flow <flow-name>


Examples
^^^^^^^^^^^^^^^^^^^^
- Example 1: Find all flows using a node

.. code-block:: bash

  mobdata usage-search node create_log
  # Output:
  Node 'create_log' is used in 6 flow(s):
  ------------------------------------------------------------
    [Direct] Flow: fake_drop, NodeInst: log_operation_success
    [Direct] Flow: pick, NodeInst: pick_success
    [Direct] Flow: tugbot_idle_sim, NodeInst: spawn_log
    [Indirect] Flow: movai_lab_loop, NodeInst: pick_success,
    Path: {'flow': 'movai_lab_loop', 'Container': 'pick'} -> {'flow': 'pick', 'NodeInst': 'pick_success'}
    [Indirect] Flow: movai_lab_loop_fleet_sim, NodeInst: pick_success,
    Path: {'flow': 'movai_lab_loop_fleet_sim', 'Container': 'pick'} -> {'flow': 'pick', 'NodeInst': 'pick_success'}
    [Indirect] Flow: movai_lab_loop_sim, NodeInst: pick_success,
    Path: {'flow': 'movai_lab_loop_sim', 'Container': 'pick'} -> {'flow': 'pick', 'NodeInst': 'pick_success'}


- Example 2: Search for subflow usage with debug output

.. code-block:: bash

  mobdata usage-search flow pick --verbose
  # Output:
  Flow 'pick' is used in 7 flow(s):
  ------------------------------------------------------------
    [Direct] Flow: drop, Container: pick
    [Direct] Flow: movai_lab_loop, Container: pick
    [Direct] Flow: movai_lab_loop_fleet_sim, Container: pick
    [Direct] Flow: movai_lab_loop_sim, Container: pick
    [Indirect] Flow: movai_lab_loop, Container: drop,
    Path: {'flow': 'movai_lab_loop', 'Container': 'drop'} -> {'flow': 'drop', 'Container': 'pick'}
    [Indirect] Flow: movai_lab_loop_fleet_sim, Container: drop,
    Path: {'flow': 'movai_lab_loop_fleet_sim', 'Container': 'drop'} -> {'flow': 'drop', 'Container': 'pick'}
    [Indirect] Flow: movai_lab_loop_sim, Container: drop,
    Path: {'flow': 'movai_lab_loop_sim', 'Container': 'drop'} -> {'flow': 'drop', 'Container': 'pick'}


  Full JSON result:
  {
    "flow": "pick",
    "usage": [
      {
        "flow": "drop",
        "Container": "pick",
        "direct": true
      },
      {
        "flow": "movai_lab_loop",
        "Container": "pick",
        "direct": true
      },
      {
        "flow": "movai_lab_loop_fleet_sim",
        "Container": "pick",
        "direct": true
      },
      {
        "flow": "movai_lab_loop_sim",
        "Container": "pick",
        "direct": true
      },
      {
        "flow": "movai_lab_loop",
        "direct": false,
        "Container": "drop",
        "path": [
          {
            "flow": "movai_lab_loop",
            "Container": "drop"
          },
          {
            "flow": "drop",
            "Container": "pick"
          }
        ]
      },
      {
        "flow": "movai_lab_loop_fleet_sim",
        "direct": false,
        "Container": "drop",
        "path": [
          {
            "flow": "movai_lab_loop_fleet_sim",
            "Container": "drop"
          },
          {
            "flow": "drop",
            "Container": "pick"
          }
        ]
      },
      {
        "flow": "movai_lab_loop_sim",
        "direct": false,
        "Container": "drop",
        "path": [
          {
            "flow": "movai_lab_loop_sim",
            "Container": "drop"
          },
          {
            "flow": "drop",
            "Container": "pick"
          }
        ]
      }
    ]
  }


- Example 3: Error respose - Node not found

.. code-block:: bash

  mobdata usage-search node NonExistentNode
  # Output:
  Error: Node 'NonExistentNode' does not exist
