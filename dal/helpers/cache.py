"""
# Size of each object in bytes, calculated using pympler asizeof
_________________________________
| Type          |   Models      |
---------------------------------
│ Node          |   7.28 MB     |
│ Callback      |   14.39 MB    |
│ Flow          |   19.36 MB    |
│ Configuration |   21.86 MB    |
│ Ports         |   23.18 MB    |
| Layout        |   23.04 MB    |
| Annotation    |   23.04 MB    |
| GraphicScene  |   22.7  MB    |
---------------------------------
"""

from cachetools import TTLCache
from threading import Lock
from datetime import datetime


CACHE_SIZE_MB = 1000
average_object_size = 20  # Size of each object in Mega bytes
max_entries = CACHE_SIZE_MB // average_object_size  # ~ 50 entries
TTL_SECONDS = 3 * 3600  # (3 hour)


class ThreadSafeCache:
    _instance = None
    _lock = Lock()

    def __new__(cls, maxsize=100, ttl=TTL_SECONDS):
        if not cls._instance:
            with cls._lock:
                cls._instance = super().__new__(cls)
                cls._instance.cache = TTLCache(maxsize=maxsize, ttl=ttl)
                cls.last_parsed = datetime.min
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
            self.last_parsed = datetime.now()

    def __delitem__(self, key):
        with self._lock:
            del self.cache[key]

    def __contains__(self, key):
        with self._lock:
            return key in self.cache

    def __len__(self):
        with self._lock:
            return len(self.cache)
