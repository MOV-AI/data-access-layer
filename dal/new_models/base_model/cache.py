"""
# Size of each object in bytes, calculated using pympler asizeof
│ Node avg size: 18088
│ Callback avg size: 5004
│ Flow avg size: 31280
│ Configuration avg size: 18493
│ Ports avg size: 4619
"""

from cachetools import TTLCache
from threading import Lock


CACHE_SIZE_MB = 500
cache_size_in_bytes = CACHE_SIZE_MB * 1024 * 1024  # 500 MB in bytes
average_object_size = 31280  # Size of each object in bytes
max_entries = cache_size_in_bytes // average_object_size  # ~16760
TTL_SECONDS = 3600  # (1 hour)


class ThreadSafeCache:
    _instance = None
    _lock = Lock()

    def __new__(cls, maxsize=max_entries, ttl=TTL_SECONDS):
        if not cls._instance:
            with cls._lock:
                cls._instance = super().__new__(cls)
                cls._instance.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        return cls._instance

    def get(self, key, default=None):
        with self._lock:
            return self.cache.get(key, default)

    def __getitem__(self, key):
        with self._lock:
            return self.cache[key]

    def __setitem__(self, key, value):
        with self._lock:
            self.cache[key] = value

    def __delitem__(self, key):
        with self._lock:
            del self.cache[key]

    def __contains__(self, key):
        with self._lock:
            return key in self.cache

    def __len__(self):
        with self._lock:
            return len(self.cache)
