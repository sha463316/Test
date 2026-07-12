import time
import uuid
import logging
from contextlib import contextmanager
from django.core.cache import cache

logger = logging.getLogger("core.lock")


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


@contextmanager
def distributed_lock(key: str, ttl: int = 60, retry_count: int = 0, retry_delay: float = 0.1):
    acquired = False
    for attempt in range(retry_count + 1):
        if acquire_lock(key, ttl):
            acquired = True
            logger.info("lock.acquired", extra={"lock_key": key, "attempt": attempt + 1})
            break
        if attempt < retry_count:
            time.sleep(retry_delay)
    if not acquired:
        logger.warning("lock.busy", extra={"lock_key": key})
    try:
        yield acquired
    finally:
        if acquired:
            release_lock(key)
            logger.info("lock.released", extra={"lock_key": key})
