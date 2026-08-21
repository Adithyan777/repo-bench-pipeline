# Golden solution: b8aca17

Commit `b8aca172cb70f4ba39ce5eda76a711e442dad375` (parent `ec378f6deebdd118106c72096fb388d12672968f`): Merge pull request #206 from mrocklin/reduceby-callable

The historical change, applied to `input/` gives `solution/` exactly (hygiene overlay files aside).

```diff
diff --git a/toolz/itertoolz.py b/toolz/itertoolz.py
index 15b9289..00af832 100644
--- a/toolz/itertoolz.py
+++ b/toolz/itertoolz.py
@@ -506,6 +506,10 @@ def reduceby(key, binop, seq, init=no_default):
     operate in much less space.  This makes it suitable for larger datasets
     that do not fit comfortably in memory
 
+    The ``init`` keyword argument is the default initialization of the
+    reduction.  This can be either a constant value like ``0`` or a callable
+    like ``lambda : 0`` as might be used in ``defaultdict``.
+
     Simple Examples
     ---------------
 
@@ -532,7 +536,21 @@ def reduceby(key, binop, seq, init=no_default):
     ...          lambda acc, x: acc + x['cost'],
     ...          projects, 0)
     {'CA': 1200000, 'IL': 2100000}
+
+    Example Using ``init``
+    ----------------------
+
+    >>> def set_add(s, i):
+    ...     s.add(i)
+    ...     return s
+
+    >>> reduceby(iseven, set_add, [1, 2, 3, 4, 1, 2, 3], set)  # doctest: +SKIP
+    {True:  set([2, 4]),
+     False: set([1, 3])}
     """
+    if init is not no_default and not callable(init):
+        _init = init
+        init = lambda: _init
     if not callable(key):
         key = getter(key)
     d = {}
@@ -543,7 +561,7 @@ def reduceby(key, binop, seq, init=no_default):
                 d[k] = item
                 continue
             else:
-                d[k] = init
+                d[k] = init()
         d[k] = binop(d[k], item)
     return d
 
diff --git a/toolz/tests/test_itertoolz.py b/toolz/tests/test_itertoolz.py
index e9ce60a..d2ef7c1 100644
--- a/toolz/tests/test_itertoolz.py
+++ b/toolz/tests/test_itertoolz.py
@@ -243,6 +243,15 @@ def test_reduce_by_init():
     assert reduceby(iseven, add, [1, 2, 3, 4]) == {True: 2 + 4, False: 1 + 3}
 
 
+def test_reduce_by_callable_default():
+    def set_add(s, i):
+        s.add(i)
+        return s
+
+    assert reduceby(iseven, set_add, [1, 2, 3, 4, 1, 2], set) == \
+        {True: set([2, 4]), False: set([1, 3])}
+
+
 def test_iterate():
     assert list(itertools.islice(iterate(inc, 0), 0, 5)) == [0, 1, 2, 3, 4]
     assert list(take(4, iterate(double, 1))) == [1, 2, 4, 8]
```

## Why correct

The diff modifies `reduceby` so that when `init` is not callable, it wraps it in a zero-argument lambda, and then the accumulator initialization uses `init()` instead of the bare value. This allows callers to pass either a constant or a callable factory like `set`, with the factory being invoked once per new key to produce independent initial accumulator values. The verifier test `test_reduce_by_callable_default` passes because passing `set` (a callable) causes `reduceby` to call `set()` for each group, yielding distinct `set` objects; without this change, all groups would share the same mutable `set` instance, causing incorrect merged results.
