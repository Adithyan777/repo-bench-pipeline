from functools import partial, reduce  # noqa: F401

from .dicttoolz import *  # noqa: F403
from .functoolz import *  # noqa: F403
from .itertoolz import *  # noqa: F403
from .recipes import *  # noqa: F403

sorted = sorted

map = map

filter = filter

# Aliases
comp = compose  # noqa: F405

from . import curried, sandbox  # noqa: E402, F401

functoolz._sigs.create_signature_registry()  # noqa: F405


def __getattr__(name):
    if name == "__version__":
        from importlib.metadata import version

        rv = version("toolz")
        globals()[name] = rv
        return rv
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
