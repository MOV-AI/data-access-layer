Memory Optimization
==================

GD_Node supports memory optimization features that can help control memory usage when running multiple instances.

Environment Variables
-------------------

Redis Pool Settings
~~~~~~~~~~~~~~~~~

Connection pool settings can be configured through environment variables:

Synchronous Pool Configuration:

``REDIS_MASTER_POOL_ENABLED``
    Enable connection pooling for master Redis connections.

    * Type: boolean (0 or 1)
    * Default: 1
    * Example: ``REDIS_MASTER_POOL_ENABLED=1``

``REDIS_MASTER_POOL_SIZE``
    Maximum connections in master pool.

    * Type: integer
    * Default: 10
    * Example: ``REDIS_MASTER_POOL_SIZE=10``

``REDIS_SLAVE_POOL_ENABLED``
    Enable connection pooling for slave Redis connections.

    * Type: boolean (0 or 1)
    * Default: 1
    * Example: ``REDIS_SLAVE_POOL_ENABLED=1``

``REDIS_SLAVE_POOL_SIZE``
    Maximum connections in slave pool.

    * Type: integer
    * Default: 20
    * Example: ``REDIS_SLAVE_POOL_SIZE=20``

``REDIS_LOCAL_POOL_ENABLED``
    Enable connection pooling for local Redis connections.

    * Type: boolean (0 or 1)
    * Default: 1
    * Example: ``REDIS_LOCAL_POOL_ENABLED=1``

``REDIS_LOCAL_POOL_SIZE``
    Maximum connections in local pool.

    * Type: integer
    * Default: 5
    * Example: ``REDIS_LOCAL_POOL_SIZE=5``

Asynchronous Pool Configuration:

``REDIS_ASYNC_POOL_ENABLED``
    Enable connection pooling for async Redis connections.

    * Type: boolean (0 or 1)
    * Default: 1
    * Example: ``REDIS_ASYNC_POOL_ENABLED=1``

``REDIS_ASYNC_POOL_MIN``
    Minimum connections in async pool.

    * Type: integer
    * Default: 5
    * Example: ``REDIS_ASYNC_POOL_MIN=5``

``REDIS_ASYNC_POOL_MAX``
    Maximum connections in async pool.

    * Type: integer
    * Default: 20
    * Example: ``REDIS_ASYNC_POOL_MAX=20``

Connection Pool Optimization
--------------------------

SharedPoolRegistry
~~~~~~~~~~~~~~~~

The SharedPoolRegistry provides centralized management of Redis connection pools, ensuring optimal memory usage across multiple processes:

1. Connection Sharing:
   - Multiple client instances share the same connection pool
   - Prevents connection explosion in multi-process environments
   - Reduces memory overhead per process

2. Lazy Initialization:
   - Pools are created only when first accessed
   - Resources allocated on-demand
   - Reduces initial memory footprint

3. Automatic Cleanup:
   - Idle pools are automatically cleaned up
   - Default idle timeout: 5 minutes
   - Recovers memory from unused connections

Example usage:

.. code-block:: python

    from dal.shared_pool import SharedPoolRegistry

    # Get pool statistics
    stats = SharedPoolRegistry.get_pool_stats()
    print(f"Active pools: {stats['total_pools']}")
    print(f"Pool details: {stats['pools']}")

    # Start automatic cleanup
    SharedPoolRegistry.start_cleanup_task(loop)

    # Stop cleanup when done
    SharedPoolRegistry.stop_cleanup_task()

Memory Impact
~~~~~~~~~~~

For detailed metrics and monitoring tools, see :doc:`performance_metrics`.

The connection pool optimization provides significant memory savings:

1. **RSS (Resident Set Size)**:
   - 15-25% reduction per process
   - Additional 20-30% with connection sharing
   - Example: 100MB → 50-65MB per process

2. **VMS (Virtual Memory Size)**:
   - 40-50% base reduction
   - Up to 70-80% with all optimizations
   - Example: 150MB → 30-45MB per process

3. **System-wide Impact** (100 processes):
   - RSS reduction: 5-10GB
   - VMS reduction: 10-12GB
   - Connection count: 80-90% reduction

Memory Usage Monitoring
---------------------

For comprehensive monitoring tools and metrics analysis, see :doc:`performance_metrics`.

Pool Statistics
~~~~~~~~~~~~~

Monitor pool usage and health using the SharedPoolRegistry API:

.. code-block:: python

    stats = SharedPoolRegistry.get_pool_stats()

    # Check total active pools
    print(f"Total pools: {stats['total_pools']}")

    # Monitor individual pools
    for name, info in stats['pools'].items():
        print(f"Pool {name}:")
        print(f"  Idle time: {info['idle_time']:.1f}s")
        print(f"  Type: {info['type']}")

Process Memory
~~~~~~~~~~~~

Track process memory usage:

.. code-block:: bash

    # Monitor RSS and VMS
    ps -o pid,rss,vsize,cmd -p <pid>

    # Check Redis connections
    redis-cli CLIENT LIST | wc -l

    # Pool statistics
    redis-cli INFO Clients

Best Practices
-------------

1. Enable pool sharing in multi-process environments:
   ``single_connection_client=False``

2. Configure pool sizes based on usage:
   - Master: 10 connections for write operations
   - Slave: 20 connections for read operations
   - Local: 5 connections for local operations

3. Monitor memory usage:
   - Track pool statistics
   - Monitor process memory
   - Watch connection counts

4. Enable automatic cleanup:
   - Start cleanup task on initialization
   - Use default 5-minute idle timeout
   - Stop cleanup task on shutdown

Notes
-----

1. Memory limits are applied per process.
2. Redis pool settings affect both local and remote Redis connections.
3. Connection sharing requires ``single_connection_client=False``.
4. Pool cleanup runs automatically every minute.
5. Strong references prevent premature pool cleanup.
6. Idle pools are automatically cleaned up after 5 minutes.
