import time
import uuid
from django.core.cache import cache


def acquire_lock(key: str, ttl: int = 60) -> bool:
    try:
        return cache.set(key, str(uuid.uuid4()), timeout=ttl, nx=True)
    except TypeError:
        if cache.get(key):
            return False
        cache.set(key, str(uuid.uuid4()), timeout=ttl)
        return True


def release_lock(key: str):
    cache.delete(key)
