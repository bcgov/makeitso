# Properly copied from stackoverflow
# https://stackoverflow.com/a/78227581

import functools
from threading import Timer
from typing import Any


def debounce(timeout: float):
    """
    Decorator that debounces a function so that it is only called after it stops being called for a specified timeout period.
    Args:
        timeout (float): The debounce timeout period in seconds.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            wrapper.func.cancel()
            wrapper.func = Timer(timeout, func, args, kwargs)
            wrapper.func.start()

        wrapper.func = Timer(timeout, lambda: None)
        return wrapper

    return decorator
