"""Test Redis connection pool optimization."""
import os
import redis
import aioredis
import asyncio
import psutil
import pytest
from dal.pool_config import PoolConfig
from dal.shared_pool import SharedPoolRegistry


def get_process_memory():
    """Get current process memory usage."""
    process = psutil.Process(os.getpid())
    return {
        "rss": process.memory_info().rss / 1024 / 1024,  # MB
        "vms": process.memory_info().vms / 1024 / 1024,  # MB
    }


@pytest.mark.asyncio
async def test_async_pool(global_db):
    """Test async Redis pool memory usage."""
    print("\nTesting Async Redis Pool Memory Usage")
    print("-------------------------------------")

    # Memory before connections
    initial_mem = get_process_memory()
    print(f"Initial Memory - RSS: {initial_mem['rss']:.2f}MB, VMS: {initial_mem['vms']:.2f}MB")

    # Create pool with optimization
    os.environ["REDIS_ASYNC_POOL_ENABLED"] = "1"
    os.environ["REDIS_ASYNC_POOL_MIN"] = "1"
    os.environ["REDIS_ASYNC_POOL_MAX"] = "32"

    try:
        address = (
            os.environ.get("REDIS_MASTER_HOST", "localhost"),
            int(os.environ.get("REDIS_MASTER_PORT", 6379)),
        )
        pool = await aioredis.create_redis_pool(
            address, pool_cls=aioredis.ConnectionsPool, **PoolConfig.get_pool_config("async")
        )

        # Create multiple clients to test connection sharing
        clients = []
        for _ in range(32):
            clients.append(
                await aioredis.create_redis(
                    address,
                )
            )

        # Memory after pool and clients creation
        pool_mem = get_process_memory()
        print(f"Pool Memory   - RSS: {pool_mem['rss']:.2f}MB, VMS: {pool_mem['vms']:.2f}MB")
        print(
            f"Difference    - RSS: {pool_mem['rss'] - initial_mem['rss']:.2f}MB, "
            f"VMS: {pool_mem['vms'] - initial_mem['vms']:.2f}MB"
        )

        # Test connection sharing effectiveness
        stats = SharedPoolRegistry.get_pool_stats()
        print(f"\nPool Statistics:")
        print(f"Total pools: {stats['total_pools']}")
        print("Individual pools:")
        for name, info in stats["pools"].items():
            print(f"  {name}: idle_time={info['idle_time']:.1f}s, type={info['type']}")

        # Test idle cleanup
        print("\nTesting idle cleanup...")
        await asyncio.sleep(2)
        stats = SharedPoolRegistry.get_pool_stats()
        print(f"Active pools after 2s: {stats['total_pools']}")

        # Cleanup
        pool.close()
        for client in clients:
            client.close()
        await pool.wait_closed()

    except Exception as e:
        print(f"Error in async pool test: {e}")
        assert False, f"Async pool test failed: {e}"


def test_sync_pool(global_db):
    """Test synchronous Redis pool memory usage."""
    print("\nTesting Sync Redis Pool Memory Usage")
    print("-----------------------------------")

    # Memory before connections
    initial_mem = get_process_memory()
    print(f"Initial Memory - RSS: {initial_mem['rss']:.2f}MB, VMS: {initial_mem['vms']:.2f}MB")

    # Create pool with optimization
    os.environ["REDIS_MASTER_POOL_ENABLED"] = "1"
    os.environ["REDIS_MASTER_POOL_SIZE"] = "10"

    try:
        address = (
            os.environ.get("REDIS_MASTER_HOST", "localhost"),
            int(os.environ.get("REDIS_MASTER_PORT", 6379)),
        )
        pool = redis.ConnectionPool(
            host=address[0], port=address[1], db=0, **PoolConfig.get_pool_config("master")
        )

        # Create Redis clients with shared connections
        clients = [redis.Redis(connection_pool=pool) for _ in range(10)]
        print("\nCreated 5 clients sharing the same connection pool")

        # Memory after pool creation and client initialization
        pool_mem = get_process_memory()
        print(f"Pool Memory   - RSS: {pool_mem['rss']:.2f}MB, VMS: {pool_mem['vms']:.2f}MB")
        print(
            f"Difference    - RSS: {pool_mem['rss'] - initial_mem['rss']:.2f}MB, "
            f"VMS: {pool_mem['vms'] - initial_mem['vms']:.2f}MB"
        )

        # Test connection sharing effectiveness
        print("\nTesting connection sharing...")
        stats = SharedPoolRegistry.get_pool_stats()
        print(f"Total pools in registry: {stats['total_pools']}")
        print(f"Pool info: {stats['pools']}")

        # Cleanup
        for client in clients:
            client.close()
        pool.disconnect()

    except Exception as e:
        print(f"Error in sync pool test: {e}")
        assert False, f"Sync pool test failed: {e}"


@pytest.mark.asyncio
async def test_async_redis_stress_pubsub_rw(global_db):
    """Stress test async Redis pool with pub/sub, read, and write operations."""
    print("\nStress Testing Async Redis Pool with Pub/Sub, Read, Write")
    print("------------------------------------------------------")

    initial_mem = get_process_memory()
    print(f"Initial Memory - RSS: {initial_mem['rss']:.2f}MB, VMS: {initial_mem['vms']:.2f}MB")

    os.environ["REDIS_ASYNC_POOL_ENABLED"] = "1"
    os.environ["REDIS_ASYNC_POOL_MIN"] = "1"
    os.environ["REDIS_ASYNC_POOL_MAX"] = "32"

    address = (
        os.environ.get("REDIS_MASTER_HOST", "localhost"),
        int(os.environ.get("REDIS_MASTER_PORT", 6379)),
    )
    pool = await aioredis.create_redis_pool(
        address, pool_cls=aioredis.ConnectionsPool, **PoolConfig.get_pool_config("async")
    )

    channel = "stress_test_channel"
    num_messages = 1000
    num_tasks = 64
    results = {"published": 0, "received": 0, "writes": 0, "reads": 0}

    sub_ready = asyncio.Event()

    async def publisher():
        await sub_ready.wait()  # Wait for subscriber to be ready
        pub = await aioredis.create_redis(address)
        for i in range(num_messages):
            await pub.publish(channel, f"msg-{i}")
            results["published"] += 1
        pub.close()
        await pub.wait_closed()

    async def subscriber():
        sub = await aioredis.create_redis(address)
        res = await sub.subscribe(channel)
        ch = res[0]
        sub_ready.set()  # Signal that subscriber is ready
        count = 0
        while count < num_messages:
            msg = await ch.get()
            if msg is not None:
                results["received"] += 1
                count += 1
        await sub.unsubscribe(channel)
        sub.close()
        await sub.wait_closed()

    async def writer(task_id):
        cli = await aioredis.create_redis(address)
        for i in range(num_messages):
            key = f"stress:key:{task_id}:{i}"
            await cli.set(key, f"val-{i}")
            results["writes"] += 1
        cli.close()
        await cli.wait_closed()

    async def reader(task_id):
        cli = await aioredis.create_redis(address)
        for i in range(num_messages):
            key = f"stress:key:{task_id}:{i}"
            val = await cli.get(key)
            if val is not None:
                results["reads"] += 1
        cli.close()
        await cli.wait_closed()

    # Launch tasks
    print("[Main] Launching publisher, subscriber, and writers...")
    pub_task = asyncio.create_task(publisher())
    sub_task = asyncio.create_task(subscriber())
    write_tasks = [asyncio.create_task(writer(i)) for i in range(num_tasks)]
    await asyncio.gather(pub_task, sub_task, *write_tasks)
    print("[Main] Writers and pub/sub done. Launching readers...")
    read_tasks = [asyncio.create_task(reader(i)) for i in range(num_tasks)]
    await asyncio.gather(*read_tasks)
    print("[Main] Readers done.")

    # Memory after stress test
    pool_mem = get_process_memory()
    print(f"After Stress - RSS: {pool_mem['rss']:.2f}MB, VMS: {pool_mem['vms']:.2f}MB")
    print(
        f"Difference   - RSS: {pool_mem['rss'] - initial_mem['rss']:.2f}MB, VMS: {pool_mem['vms'] - initial_mem['vms']:.2f}MB"
    )

    stats = SharedPoolRegistry.get_pool_stats()
    print("\nPool Statistics:")
    print(f"Total pools: {stats['total_pools']}")
    print("Individual pools:")
    for name, info in stats["pools"].items():
        print(f"  {name}: idle_time={info['idle_time']:.1f}s, type={info['type']}")

    print(f"\nResults: {results}")
    assert results["published"] == num_messages
    assert results["received"] == num_messages
    assert results["writes"] == num_messages * num_tasks
    assert results["reads"] == num_messages * num_tasks

    pool.close()
    await pool.wait_closed()


def teardown_module(module):
    """Ensure Redis pool cleanup task is stopped after tests."""
    SharedPoolRegistry.stop_cleanup_task()
