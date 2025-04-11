Resource permissions
====================

.. warning::
    This document is a work in progress.

As base for the platform permissions we use the library `miracle-acl <https://github.com/kolypto/py-miracle>`_ (now deprecated).

The library includes the following concepts - which we mirror in the platform:
 * resource - the object you want to protect
 * permissions - possible actions on the resource
 * roles - used to group resource + permission set

Permissions
-----------

The available permissions are:
 * create
 * read
 * update
 * delete
 * execute
 * reset

.. note::
    Not all permissions are available for all resources.

Resources
---------

See available resources in: :ref:`ResourceType<dal.models package>`.

Roles
-----

The available roles are:
 * ADMIN
 * DEPLOYER
 * OPERATOR

The DEPLOYER role includes the following permissions:
 * EmailsAlertsConfig: read and update
 * EmailsAlertsRecipients: read
 * Configuration: read
 * InternalUser: read
 * Role: read
 * AclObject: read
 * Access to all Applications

The OPERATOR role includes the following permissions:
 * EmailsAlertsConfig: read
 * EmailsAlertsRecipients: read and update
 * Configuration: read
 * Access to Launcher and FleetBoard
