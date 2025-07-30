Schemas and validation
======================

Written after an incomplete review.

Available schemas
-----------------

- `1.0` - used to determine how scope fields are written into redis
- `2.0` - seems not to be used
- `2.4` - used to validate scope fields before writing into redis

Data validation
---------------

Scopes data may be validated before writing into redis.

See which data is validated in `SCOPES_TO_VALIDATE` of :ref:`ResourceType<dal.scopes package>`.
