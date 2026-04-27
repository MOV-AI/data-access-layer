Schemas and validation
======================

Available schemas
-----------------

- `1.0`
- `2.0`
- `2.4`

1.0 - Custom object model
~~~~~~~~~~~~~~~~~~~~~~~~~

Defines a custom object model which determines how scopes are stored in the key value database.
Some patterns result in unexpected behaviors.

Reading fields defined with the following pattern is not possible:

.. code-block:: JSON

    {
        "$name": "str"
    }

2.0 - Unused
~~~~~~~~~~~~

Unused schema.

2.4 - Data validation
~~~~~~~~~~~~~~~~~~~~~

Jsonschemas used for full data validation of some scopes objects.

See which data is validated in `SCOPES_TO_VALIDATE` of :ref:`ResourceType<dal.scopes package>`.
