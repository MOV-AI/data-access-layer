from cachetools import TTLCache
from threading import Lock


CACHE_SIZE_MB = 500

cache_size_in_bytes = CACHE_SIZE_MB * 1024 * 1024  # 500 MB in bytes
average_object_size = 48  # Size of each object in bytes, calculated using sys.getsizeof
max_entries = cache_size_in_bytes // average_object_size


class ThreadSafeCache:
    _instance = None
    _lock = Lock()

    def __new__(cls, maxsize=max_entries, ttl=3600):
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
