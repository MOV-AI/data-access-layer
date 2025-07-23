"""
Redis connection pool optimization with memory optimization settings.

This module provides centralized configuration for Redis connection pools,
including both synchronous and asynchronous clients. It implements feature
flags for gradual rollout and configuration for optimal memory usage.
"""

from typing import Dict, Any
import os
from dataclasses import dataclass


@dataclass
class RedisPoolConfig:
    """Configuration for Redis connection pools."""

    max_connections: int
    min_connections: int
    health_check_interval: int = 30
    connection_timeout: float = 5.0


class PoolConfig:
    """Central configuration for Redis connection pools with feature flags."""

    # Feature flags for gradual rollout
    OPTIMIZATIONS_ENABLED = {
        "master": bool(int(os.getenv("REDIS_MASTER_POOL_ENABLED", "1"))),
        "slave": bool(int(os.getenv("REDIS_SLAVE_POOL_ENABLED", "1"))),
        "local": bool(int(os.getenv("REDIS_LOCAL_POOL_ENABLED", "1"))),
        "async": bool(int(os.getenv("REDIS_ASYNC_POOL_ENABLED", "1"))),
    }

    # Synchronous Redis pool configurations
    SYNC_POOL_CONFIGS = {
        "master": RedisPoolConfig(
            max_connections=int(os.getenv("REDIS_MASTER_POOL_SIZE", "3")), min_connections=1
        ),
        "slave": RedisPoolConfig(
            max_connections=int(os.getenv("REDIS_SLAVE_POOL_SIZE", "3")), min_connections=1
        ),
        "local": RedisPoolConfig(
            max_connections=int(os.getenv("REDIS_LOCAL_POOL_SIZE", "3")), min_connections=1
        ),
    }

    # Asynchronous Redis pool configuration
    ASYNC_POOL_CONFIG = {
        "minsize": int(os.getenv("REDIS_ASYNC_POOL_MIN", "1")),
        "maxsize": int(os.getenv("REDIS_ASYNC_POOL_MAX", "3")),
    }

    @staticmethod
    def get_sync_pool_config(pool_type: str) -> Dict[str, Any]:
        """Get configuration for a specific synchronous pool type."""
        if pool_type not in PoolConfig.SYNC_POOL_CONFIGS:
            raise ValueError(f"Unknown pool type: {pool_type}")

        # Redis-py ConnectionPool only supports max_connections
        return {"max_connections": PoolConfig.SYNC_POOL_CONFIGS[pool_type].max_connections}

    @staticmethod
    def get_async_pool_config() -> Dict[str, Any]:
        """Get the asynchronous pool configuration."""
        return PoolConfig.ASYNC_POOL_CONFIG.copy()

    @staticmethod
    def is_optimization_enabled(pool_type: str) -> bool:
        """Check if optimizations are enabled for a specific pool type."""
        return PoolConfig.OPTIMIZATIONS_ENABLED.get(pool_type, False)

    @staticmethod
    def get_pool_config(pool_type: str) -> Dict[str, Any]:
        """Get pool configuration if optimization is enabled for the pool type.

        Args:
            pool_type: The type of pool ('master', 'slave', 'local', or 'async')

        Returns:
            Dict with pool configuration if optimization is enabled, empty dict otherwise
        """
        if pool_type == "async":
            return (
                PoolConfig.get_async_pool_config()
                if PoolConfig.is_optimization_enabled("async")
                else {}
            )

        if PoolConfig.is_optimization_enabled(pool_type):
            return PoolConfig.get_sync_pool_config(pool_type)
        return {}
