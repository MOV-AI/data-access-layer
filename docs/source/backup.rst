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
    [Direct] Flow: fake_drop
             Node Instance: log_operation_success
    [Direct] Flow: pick
             Node Instance: pick_success
    [Direct] Flow: tugbot_idle_sim
             Node Instance: spawn_log
    [Indirect] Flow: movai_lab_loop
             Via Child Flow: pick (instance: pick)
    [Indirect] Flow: movai_lab_loop_fleet_sim
             Via Child Flow: pick (instance: pick)
    [Indirect] Flow: movai_lab_loop_sim
             Via Child Flow: pick (instance: pick)


- Example 2: Search for subflow usage with debug output

.. code-block:: bash

  mobdata usage-search flow pick --verbose
  # Output:
  Flow 'pick' is used in 7 flow(s):
  ------------------------------------------------------------
    [Direct] Flow: drop
             Flow Instance (Container): pick
    [Direct] Flow: movai_lab_loop
             Flow Instance (Container): pick
    [Direct] Flow: movai_lab_loop_fleet_sim
             Flow Instance (Container): pick
    [Direct] Flow: movai_lab_loop_sim
             Flow Instance (Container): pick
    [Indirect] Flow: movai_lab_loop
             Via Child Flow: drop (instance: drop)
    [Indirect] Flow: movai_lab_loop_fleet_sim
             Via Child Flow: drop (instance: drop)
    [Indirect] Flow: movai_lab_loop_sim
             Via Child Flow: drop (instance: drop)

  Full JSON result:
  {
    "scope": "Flow",
    "name": "pick",
    "usage": {
      "Flow": {
        "drop": {
          "direct": [
            {
              "flow_instance_name": "pick"
            }
          ],
          "indirect": []
        },
        "movai_lab_loop": {
          "direct": [
            {
              "flow_instance_name": "pick"
            }
          ],
          "indirect": [
            {
              "flow_template_name": "drop",
              "flow_instance_name": "drop"
            }
          ]
        },
        "movai_lab_loop_fleet_sim": {
          "direct": [
            {
              "flow_instance_name": "pick"
            }
          ],
          "indirect": [
            {
              "flow_template_name": "drop",
              "flow_instance_name": "drop"
            }
          ]
        },
        "movai_lab_loop_sim": {
          "direct": [
            {
              "flow_instance_name": "pick"
            }
          ],
          "indirect": [
            {
              "flow_template_name": "drop",
              "flow_instance_name": "drop"
            }
          ]
        }
      }
    }
  }


- Example 3: Error respose - Node not found

.. code-block:: bash

  mobdata usage-search node NonExistentNode
  # Output:
  Error: Node 'NonExistentNode' does not exist
