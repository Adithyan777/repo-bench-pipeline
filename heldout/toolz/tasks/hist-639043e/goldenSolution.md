# Golden solution: 639043e

Commit `639043e5ead3c78ade96890336ffe33f9a8d6bb6` (parent `2ac03ce80c60085de6a6d6e16bb5b9dbfed943dc`): Merge pull request #411 from eliasmistler/master

The historical change, applied to `input/` gives `solution/` exactly (hygiene overlay files aside).

```diff
diff --git a/toolz/curried/__init__.py b/toolz/curried/__init__.py
index 43aeffd..fab6255 100644
--- a/toolz/curried/__init__.py
+++ b/toolz/curried/__init__.py
@@ -26,6 +26,7 @@ See Also:
 import toolz
 from . import operator
 from toolz import (
+    apply,
     comp,
     complement,
     compose,
diff --git a/toolz/functoolz.py b/toolz/functoolz.py
index 36d2cf1..9091127 100644
--- a/toolz/functoolz.py
+++ b/toolz/functoolz.py
@@ -9,8 +9,9 @@ from .compatibility import PY3, PY34, PYPY
 from .utils import no_default
 
 
-__all__ = ('identity', 'thread_first', 'thread_last', 'memoize', 'compose',
-           'pipe', 'complement', 'juxt', 'do', 'curry', 'flip', 'excepts')
+__all__ = ('identity', 'apply', 'thread_first', 'thread_last', 'memoize',
+           'compose', 'pipe', 'complement', 'juxt', 'do', 'curry', 'flip',
+           'excepts')
 
 
 def identity(x):
@@ -22,6 +23,22 @@ def identity(x):
     return x
 
 
+def apply(*func_and_args, **kwargs):
+    """ Applies a function and returns the results
+    >>> def double(x): return 2*x
+    >>> def inc(x):    return x + 1
+    >>> apply(double, 5)
+    10
+
+    >>> tuple(map(apply, [double, inc, double], [10, 500, 8000]))
+    (20, 501, 16000)
+    """
+    if not func_and_args:
+        raise TypeError('func argument is required')
+    func, args = func_and_args[0], func_and_args[1:]
+    return func(*args, **kwargs)
+
+
 def thread_first(val, *forms):
     """ Thread value through a sequence of functions/forms
 
diff --git a/toolz/tests/test_functoolz.py b/toolz/tests/test_functoolz.py
index 29c4385..148c42f 100644
--- a/toolz/tests/test_functoolz.py
+++ b/toolz/tests/test_functoolz.py
@@ -1,7 +1,7 @@
 import platform
 
 from toolz.functoolz import (thread_first, thread_last, memoize, curry,
-                             compose, pipe, complement, do, juxt, flip, excepts)
+                             compose, pipe, complement, do, juxt, flip, excepts, apply)
 from operator import add, mul, itemgetter
 from toolz.utils import raises
 from functools import partial
@@ -23,6 +23,12 @@ def double(x):
     return 2 * x
 
 
+def test_apply():
+    assert apply(double, 5) == 10
+    assert tuple(map(apply, [double, inc, double], [10, 500, 8000])) == (20, 501, 16000)
+    assert raises(TypeError, apply)
+
+
 def test_thread_first():
     assert thread_first(2) == 2
     assert thread_first(2, inc) == 3
```

## Why correct

The change adds a new public `apply` function in `toolz.functoolz` that takes a function and its arguments, then calls the function with those arguments, which matches the task requirement to add an apply function for curried/functional style invocation. The function is also added to `__all__` in `functoolz.py` and imported in `toolz/curried/__init__.py`, making it properly exposed in the curried namespace as required. The verifier tests confirm this works: `test_apply` checks that `apply` exists in `toolz.functoolz`, validates basic invocation like `apply(double, 5) == 10`, verifies it works with `map` for functional-style usage, and ensures it raises `TypeError` when called without arguments, all of which pass because the implementation correctly unpacks the first argument as the function and passes the rest as positional and keyword arguments.
