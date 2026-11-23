"""Internal string evaluation and function retry/timeout helpers.

Copyright (c) 2024 Cleland Lab. Licensed under the MIT License; see LICENSE.
"""

from func_timeout import func_timeout

__all__ = ["evalStr", "safe_wrap"]


def evalStr(s, var, _var=None):
    return eval(f"f'''{s}'''", _var, var) # How amazing this is!

def safe_wrap(retry=2, timeout=300):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(retry + 1):
                try: # func_timeout is dark magic. It calls ctypes.pythonapi to kill a thread
                    return func_timeout(timeout, func, args, kwargs)
                except Exception:
                    if i == retry:
                        raise
        return wrapper
    return decorator
