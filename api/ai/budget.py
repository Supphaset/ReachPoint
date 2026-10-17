"""Bound optional model work so Hosting can return a reply within 60 seconds."""

from concurrent.futures import ThreadPoolExecutor, TimeoutError

_workers = ThreadPoolExecutor(max_workers=8)


def within(seconds, call, *args, **kwargs):
    # Only use for reads: a late result must never change a room.
    future = _workers.submit(call, *args, **kwargs)
    try:
        return future.result(timeout=seconds)
    except TimeoutError:
        future.cancel()
        return None
