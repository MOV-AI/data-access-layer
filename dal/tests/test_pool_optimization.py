"""Test Redis connection pool optimization."""
import os
import time
import psutil
import redis
import aioredis
import asyncio
from dal.pool_config import PoolConfig
from dal.shared_pool import SharedPoolRegistry


def get_process_memory():
    """Get current process memory usage."""
    process = psutil.Process(os.getpid())
    return {
        "rss": process.memory_info().rss / 1024 / 1024,  # MB
        "vms": process.memory_info().vms / 1024 / 1024,  # MB
    }


async def test_async_pool():
    """Test async Redis pool memory usage."""
    print("\nTesting Async Redis Pool Memory Usage")
    print("-------------------------------------")

    # Memory before connections
    initial_mem = get_process_memory()
    print(f"Initial Memory - RSS: {initial_mem['rss']:.2f}MB, VMS: {initial_mem['vms']:.2f}MB")

    # Create pool with optimization
    os.environ["REDIS_ASYNC_POOL_ENABLED"] = "1"
    os.environ["REDIS_ASYNC_POOL_MIN"] = "5"
    os.environ["REDIS_ASYNC_POOL_MAX"] = "20"

    try:
        address = ("localhost", 6379)
        pool = await aioredis.create_redis_pool(
            address, pool_cls=aioredis.ConnectionsPool, **PoolConfig.get_pool_config("async")
        )

        # Create multiple clients to test connection sharing
        clients = []
        for _ in range(5):
            clients.append(
                await aioredis.create_redis(
                    address,
                    pool_cls=aioredis.ConnectionsPool,
                    **PoolConfig.get_pool_config("async"),
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


def test_sync_pool():
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
        pool = redis.ConnectionPool(
            host="localhost", port=6379, db=0, **PoolConfig.get_pool_config("master")
        )

        # Create Redis clients with shared connections
        clients = [redis.Redis(connection_pool=pool) for _ in range(5)]
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


async def main():
    """Run all tests."""
    print("Redis Connection Pool Optimization Test")
    print("=====================================")

    # Start pool cleanup task
    SharedPoolRegistry.start_cleanup_task()

    # Run tests
    await test_async_pool()
    test_sync_pool()

    # Stop cleanup task
    SharedPoolRegistry.stop_cleanup_task()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {e}")
