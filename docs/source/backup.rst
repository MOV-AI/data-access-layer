Import, export and remove
=========================

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
