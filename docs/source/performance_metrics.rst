Performance Metrics
==================

This document describes performance metrics and monitoring capabilities in the DAL Redis connection pooling.

Memory Usage
-----------

Redis Connection Pools
~~~~~~~~~~~~~~~~~~~

For detailed configuration and implementation, see :doc:`memory_optimization`.

The Redis connection pool optimization provides significant memory savings across processes:

Memory Metrics
^^^^^^^^^^^^^

1. **Per-Process Memory**:

   * RSS (Resident Set Size):
     - Base reduction: 15-25%
     - With connection sharing: 35-45%
     - Example: 100MB → 55-65MB

   * VMS (Virtual Memory Size):
     - Base reduction: 40-50%
     - With all optimizations: 70-80%
     - Example: 150MB → 30-45MB

2. **Connection Metrics**:

   * Pool Connections:
     - Master pool: max 10 connections
     - Slave pool: max 20 connections
     - Local pool: max 5 connections
     - Async pool: 5-20 connections

   * Connection Sharing:
     - Multiple clients share same pool
     - 80-90% reduction in total connections
     - Example: 100 clients → 10-20 connections

3. **System-wide Impact** (100 processes):

   * Memory Savings:
     - RSS reduction: 5-10GB
     - VMS reduction: 10-12GB
     - Total connections: 80-90% fewer

Monitoring Tools
^^^^^^^^^^^^^

1. **Pool Statistics API**:

   .. code-block:: python

       from dal.shared_pool import SharedPoolRegistry

       # Get pool metrics
       stats = SharedPoolRegistry.get_pool_stats()

       print(f"Active pools: {stats['total_pools']}")
       for name, info in stats['pools'].items():
           print(f"Pool {name}:")
           print(f"  Idle time: {info['idle_time']:.1f}s")
           print(f"  Type: {info['type']}")

2. **System Commands**:

   .. code-block:: bash

       # Process memory usage
       ps -o pid,rss,vsize,cmd -p <pid>

       # Redis connection count
       redis-cli CLIENT LIST | wc -l

       # Redis server stats
       redis-cli INFO Clients
       redis-cli INFO Memory

3. **Custom Metrics**:

   .. code-block:: python

       import psutil

       def get_process_memory():
           process = psutil.Process()
           return {
               'rss': process.memory_info().rss / 1024 / 1024,  # MB
               'vms': process.memory_info().vms / 1024 / 1024   # MB
           }

Pool Health Checks
^^^^^^^^^^^^^^^

1. **Automatic Monitoring**:
   - Idle pool detection
   - Connection health verification
   - Resource cleanup

2. **Health Metrics**:
   - Pool size vs utilization
   - Connection age
   - Error rates
   - Cleanup effectiveness

3. **Warning Signs**:
   - Growing RSS/VMS usage
   - Increasing connection counts
   - Pool creation frequency
   - Cleanup failures

Configuration Impact
-----------------

Memory vs Performance
^^^^^^^^^^^^^^^^^^

For complete configuration options and best practices, see :doc:`memory_optimization`.

Different pool configurations impact memory and performance:

1. **Minimal Memory** (tight resources):

   .. code-block:: bash

       export REDIS_MASTER_POOL_SIZE=5
       export REDIS_SLAVE_POOL_SIZE=10
       export REDIS_LOCAL_POOL_SIZE=3
       export REDIS_ASYNC_POOL_MIN=3
       export REDIS_ASYNC_POOL_MAX=10

   * Benefits:
     - Lowest memory usage
     - Best for memory-constrained systems
   * Trade-offs:
     - More connection wait time
     - Potential connection contention

2. **Balanced** (default):

   .. code-block:: bash

       export REDIS_MASTER_POOL_SIZE=10
       export REDIS_SLAVE_POOL_SIZE=20
       export REDIS_LOCAL_POOL_SIZE=5
       export REDIS_ASYNC_POOL_MIN=5
       export REDIS_ASYNC_POOL_MAX=20

   * Benefits:
     - Good memory savings
     - Adequate connection availability
   * Trade-offs:
     - Moderate memory usage
     - Some connection management overhead

3. **High Performance** (resource-rich):

   .. code-block:: bash

       export REDIS_MASTER_POOL_SIZE=20
       export REDIS_SLAVE_POOL_SIZE=40
       export REDIS_LOCAL_POOL_SIZE=10
       export REDIS_ASYNC_POOL_MIN=10
       export REDIS_ASYNC_POOL_MAX=40

   * Benefits:
     - Maximum connection availability
     - Minimal wait times
   * Trade-offs:
     - Higher memory usage
     - More cleanup overhead

Best Practices
-----------

1. **Memory Optimization**:
   - Enable connection sharing
   - Use lazy initialization
   - Configure automatic cleanup
   - Monitor pool statistics

2. **Performance Tuning**:
   - Size pools based on usage patterns
   - Balance memory vs connection availability
   - Enable health checks
   - Monitor system impact

3. **Monitoring Strategy**:
   - Track memory metrics regularly
   - Monitor connection usage
   - Watch for warning signs
   - Adjust configurations as needed
