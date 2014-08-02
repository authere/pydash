"""Functions
"""

from __future__ import absolute_import

import inspect
import time

from .objects import is_number
from .utilities import now


class After(object):
    """Wrap a function in an after context."""
    def __init__(self, n, func):
        try:
            n = int(n)
            assert n >= 0
        except (ValueError, AssertionError):
            n = 0

        self.n = n
        self.func = func

    def __call__(self, *args, **kargs):
        """Return results of `self.func` after `self.n` calls."""
        self.n -= 1

        if self.n < 1:
            return self.func(*args, **kargs)


class Curry(object):
    """Wrap a function in a curry context."""

    def __init__(self, func, arity, args=None, kargs=None):
        self.func = func
        self.arity = (len(inspect.getargspec(func).args) if arity is None
                      else arity)
        self.args = () if args is None else args
        self.kargs = {} if kargs is None else kargs

    def __call__(self, *args, **kargs):
        """Store `args` and `kargs` and call `self.func` if we've reached or
        exceeded the function arity.
        """
        args = tuple(list(self.args) + list(args))
        kargs.update(self.kargs)

        if (len(args) + len(kargs)) >= self.arity:
            curried = self.func(*args, **kargs)
        else:
            curried = Curry(self.func, self.arity, args, kargs)

        return curried


class Once(object):
    """Wrap a function in a once context."""

    def __init__(self, func):
        self.func = func
        self.result = None
        self.called = False

    def __call__(self, *args, **kargs):
        """Return results from the first call of `self.func`."""
        if not self.called:
            self.result = self.func(*args, **kargs)
            self.called = True

        return self.result


class Partial(object):
    """Wrap a function in a partial context."""

    def __init__(self, func, args, from_right=False):
        self.func = func
        self.args = args
        self.from_right = from_right

    def __call__(self, *args, **kargs):
        """Return results from `self.func` with `self.args` + `args. Apply args
        from left or right depending on `self.from_right`.
        """
        if self.from_right:
            args = list(args) + list(self.args)
        else:
            args = list(self.args) + list(args)

        return self.func(*args, **kargs)


class Debounce(object):
    """Wrap a function in a debounce context."""

    def __init__(self, func, wait, max_wait=False):
        self.func = func
        self.wait = wait
        self.max_wait = max_wait

        self.last_result = None

        # Initialize last_* times to be prior to the wait periods so that func
        # is primed to be executed on first call.
        self.last_call = now() - self.wait
        self.last_execution = (now() - max_wait if is_number(max_wait)
                               else None)

    def __call__(self, *args, **kargs):
        """Execute `self.func` if function hasn't been called witinin last
        `self.wait` milliseconds or in last `self.max_wait` milliseconds.
        Return results of last successful call.
        """
        present = now()

        if any([(present - self.last_call) >= self.wait,
                (self.max_wait and
                 (present - self.last_execution) >= self.max_wait)]):
            self.last_result = self.func(*args, **kargs)
            self.last_execution = present

        self.last_call = present

        return self.last_result


class Throttle(object):
    """Wrap a function in a throttle context."""

    def __init__(self, func, wait):
        self.func = func
        self.wait = wait

        self.last_result = None
        self.last_execution = now() - self.wait

    def __call__(self, *args, **kargs):
        """Execute `self.func` if function hasn't been called witinin last
        `self.wait` milliseconds. Return results of last successful call.
        """
        present = now()

        if (present - self.last_execution) >= self.wait:
            self.last_result = self.func(*args, **kargs)
            self.last_execution = present

        return self.last_result


def after(n, func):
    """Creates a function that executes `func`, with the arguments of the
    created function, only after being called `n` times.
    """
    return After(n, func)


def compose(*funcs):
    """Creates a function that is the composition of the provided functions,
    where each function consumes the return value of the function that follows.
    For example, composing the functions f(), g(), and h() produces f(g(h())).
    """
    def wrapper(*args, **kargs):  # pylint: disable=missing-docstring
        # NOTE: Cannot use `funcs` for the variable name of list(funcs) due to
        # the way Python handles closure variables. Basically, `funcs` has to
        # remain unmodified.
        fns = list(funcs)

        # Compose functions in reverse order starting with the first.
        ret = (fns.pop())(*args, **kargs)

        for func in reversed(fns):
            ret = func(ret)

        return ret

    return wrapper


def curry(func, arity=None):
    """Creates a function which accepts one or more arguments of `func` that
    when  invoked either executes `func` returning its result, if all `func`
    arguments have been provided, or returns a function that accepts one or
    more of the remaining `func` arguments, and so on.
    """
    return Curry(func, arity)


def debounce(func, wait, max_wait=False):
    """Creates a function that will delay the execution of `func` until after
    `wait` milliseconds have elapsed since the last time it was invoked.
    Subsequent calls to the debounced function will return the result of the
    last `func` call.

    Args:
        func (function): Function to execute.
        wait (int): Milliseconds to wait before executing `func`.
        max_wait (optional): Maximum time to wait before executing `func`.

    Returns:
        Debounce: Debounced function class wrapper.
    """
    return Debounce(func, wait, max_wait=max_wait)


def delay(func, wait, *args, **kargs):
    """Executes the `func` function after `wait` milliseconds. Additional
    arguments will be provided to `func` when it is invoked.

    Args:
        func (function): Function to execute.
        wait (int): Milliseconds to wait before executing `func`.
        *args (optional): Arguments to pass to `func`.
        **kargs (optional): Keyword arguments to pass to `func`.

    Returns:
        mixed: Return from `func`
    """
    time.sleep(wait / 1000.0)
    return func(*args, **kargs)


def once(func):
    """Creates a function that is restricted to execute func once. Repeat calls
    to the function will return the value of the first call.
    """
    return Once(func)


def partial(func, *args):
    """Creates a function that, when called, invokes `func` with any additional
    partial arguments prepended to those provided to the new function.
    """
    return Partial(func, args)


def partial_right(func, *args):
    """This method is like :func:`partial` except that partial arguments are
    appended to those provided to the new function.
    """
    return Partial(func, args, from_right=True)


def throttle(func, wait):
    """Creates a function that, when executed, will only call the `func`
    function at most once per every `wait` milliseconds. Subsequent calls to
    the throttled function will return the result of the last `func` call.

    Args:
        func (function): Function to throttle.
        wait (int): Milliseconds to wait before calling `func` again.

    Returns:
        mixed: Results of last `func` call.
    """
    return Throttle(func, wait)


def wrap(value, wrapper):
    """Creates a function that provides value to the wrapper function as its
    first argument. Additional arguments provided to the function are appended
    to those provided to the wrapper function.
    """
    return Partial(wrapper, (value,))
