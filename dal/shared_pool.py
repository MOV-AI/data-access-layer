"""
Shared connection pool registry for Redis connections.

This module implements a shared registry pattern to ensure Redis connection pools
are reused across multiple imports of the DAL, significantly reducing memory usage.
"""

from typing import Dict, Any, Callable, Optional
import asyncio
import logging
import time
import weakref
from threading import Lock

# Configure logging
LOGGER = logging.getLogger("dal.pool")
LOGGER.setLevel(logging.DEBUG)
if not LOGGER.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    LOGGER.addHandler(handler)


class SharedPoolRegistry:
    """
    Central registry for Redis connection pools. Ensures pools are shared across
    multiple imports of the DAL and implements lazy initialization and cleanup.
    """

    _pools: Dict[str, Any] = {}
    _proxies: Dict[str, Any] = {}  # Weak references for cleanup
    _last_used: Dict[str, float] = {}
    _lock = Lock()
    _cleanup_task: Optional[asyncio.Task] = None

    @classmethod
    def get_pool(cls, key: str, create_fn: Callable[[], Any]) -> Any:
        """
        Get or create a connection pool.

        Args:
            key: Unique identifier for the pool
            create_fn: Function to create the pool if it doesn't exist

        Returns:
            The connection pool instance
        """
        with cls._lock:
            if key not in cls._pools:
                # Keep strong reference in _pools
                cls._pools[key] = create_fn()
                # Create weak reference for cleanup tracking
                cls._proxies[key] = weakref.proxy(cls._pools[key])
            cls._last_used[key] = time.time()
            LOGGER.debug(
                "Pool %s: created=%s, using existing=%s",
                key,
                key not in cls._pools,
                key in cls._pools,
            )
        return cls._pools[key]

    @classmethod
    async def cleanup_idle_pools(cls, max_idle_time: int = 300) -> None:
        """
        Clean up idle connection pools.

        Args:
            max_idle_time: Maximum time in seconds a pool can be idle
        """
        while True:
            now = time.time()
            to_remove = []
            LOGGER.debug("Checking idle pools. Current pools: %s", list(cls._pools.keys()))

            with cls._lock:
                for key, last_used in cls._last_used.items():
                    if now - last_used > max_idle_time:
                        try:
                            # Try to access through weak reference first
                            proxy = cls._proxies[key]
                            try:
                                # Check if the pool is still alive
                                if hasattr(proxy, "connection_pool"):
                                    proxy.connection_pool.disconnect()
                                elif hasattr(proxy, "close"):
                                    await proxy.close()
                                elif hasattr(proxy, "disconnect"):
                                    proxy.disconnect()
                            except ReferenceError:
                                # Weak reference is dead, pool can be removed
                                pass
                            to_remove.append(key)
                        except Exception as e:
                            LOGGER.debug("Error cleaning up pool %s: %s", key, e)
                            to_remove.append(key)

                for key in to_remove:
                    cls._pools.pop(key, None)
                    cls._proxies.pop(key, None)
                    cls._last_used.pop(key, None)

            await asyncio.sleep(60)  # Check every minute

    @classmethod
    def start_cleanup_task(cls, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        """Start the periodic cleanup task."""
        if cls._cleanup_task is None:
            loop = loop or asyncio.get_event_loop()
            cls._cleanup_task = loop.create_task(cls.cleanup_idle_pools())

    @classmethod
    def stop_cleanup_task(cls) -> None:
        """Stop the periodic cleanup task."""
        if cls._cleanup_task is not None:
            cls._cleanup_task.cancel()
            cls._cleanup_task = None

    @classmethod
    def get_pool_stats(cls) -> Dict[str, Any]:
        """Get statistics about the pools."""
        with cls._lock:
            now = time.time()
            return {
                "total_pools": len(cls._pools),
                "pools": {
                    key: {"idle_time": now - last_used, "type": type(cls._pools[key]).__name__}
                    for key, last_used in cls._last_used.items()
                },
            }
