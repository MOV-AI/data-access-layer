Schemas and validation
======================

DAL contains 2 types of schemas:

- redis_schema: Used to determine how scopes are stored in the key value database.
- json_schema: Used for data validation of scopes objects.

Redis schema
------------

Defines a custom object model which determines how scopes are stored in the key value database.
Some patterns result in unexpected behaviors.

Reading fields defined with the following pattern is not possible:

.. code-block:: JSON

    {
        "$name": "str"
    }


JSON schema
-----------

Jsonschemas used for full data validation of some scopes objects.

See which data is validated in `SCOPES_TO_VALIDATE` of :ref:`ResourceType<dal.scopes package>`.
