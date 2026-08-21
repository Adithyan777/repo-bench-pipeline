# Golden solution: 8cdc7fe

Commit `8cdc7fec3da3196f74ddc1dd25da81a1446a0bfc` (parent `7994485b37bcb0263c74988861c8cea0ea9b7770`): Merge pull request #241 from davidshepherd7/unzip-2

The historical change, applied to `input/` gives `solution/` exactly (hygiene overlay files aside).

```diff
diff --git a/doc/source/api.rst b/doc/source/api.rst
index 3c2c685..706b36c 100644
--- a/doc/source/api.rst
+++ b/doc/source/api.rst
@@ -94,6 +94,7 @@ Sandbox
 .. autosummary::
    parallel.fold
    core.EqualityHashKey
+   core.unzip
 
 
 Definitions
diff --git a/toolz/sandbox/__init__.py b/toolz/sandbox/__init__.py
index 9e5cca1..0abda1c 100644
--- a/toolz/sandbox/__init__.py
+++ b/toolz/sandbox/__init__.py
@@ -1,2 +1,2 @@
-from .core import EqualityHashKey
+from .core import EqualityHashKey, unzip
 from .parallel import fold
diff --git a/toolz/sandbox/core.py b/toolz/sandbox/core.py
index b1fd87c..359fc3f 100644
--- a/toolz/sandbox/core.py
+++ b/toolz/sandbox/core.py
@@ -1,4 +1,5 @@
-from toolz.itertoolz import getter
+from toolz.itertoolz import getter, cons, pluck
+from itertools import tee, starmap
 
 
 # See #166: https://github.com/pytoolz/toolz/issues/166
@@ -91,3 +92,41 @@ class EqualityHashKey(object):
 
     def __repr__(self):
         return '=%s=' % repr(self.item)
+
+
+# See issue #293: https://github.com/pytoolz/toolz/issues/239
+def unzip(seq):
+    """Inverse of ``zip``
+
+    >>> a, b = unzip([('a', 1), ('b', 2)])
+    >>> list(a)
+    ['a', 'b']
+    >>> list(b)
+    [1, 2]
+
+    Unlike the naive implementation ``def unzip(seq): zip(*seq)`` this
+    implementation can handle a finite sequence of infinite sequences.
+
+    Caveats:
+
+    * The implementation uses ``tee``, and so can use a significant amount
+      of auxiliary storage if the resulting iterators are consumed at
+      different times.
+
+    * The top level sequence cannot be infinite.
+
+    """
+
+    seq = iter(seq)
+
+    # Check how many iterators we need
+    try:
+        first = tuple(next(seq))
+    except StopIteration:
+        return tuple()
+
+    # and create them
+    niters = len(first)
+    seqs = tee(cons(first, seq), niters)
+
+    return tuple(starmap(pluck, enumerate(seqs)))
diff --git a/toolz/sandbox/tests/test_core.py b/toolz/sandbox/tests/test_core.py
index 8c777e6..96a8309 100644
--- a/toolz/sandbox/tests/test_core.py
+++ b/toolz/sandbox/tests/test_core.py
@@ -1,5 +1,7 @@
-from toolz import curry, unique, first
-from toolz.sandbox.core import EqualityHashKey
+from toolz import curry, unique, first, take
+from toolz.sandbox.core import EqualityHashKey, unzip
+from itertools import count, repeat
+from toolz.compatibility import map, zip
 
 
 def test_EqualityHashKey_default_key():
@@ -72,3 +74,30 @@ def test_EqualityHashKey_index_key():
     EqualityHash0 = curry(EqualityHashKey, 0)
     assert list(unique(3*[list1, list2, list3a, list3b],
                        key=EqualityHash0)) == [list1, list2, list3a]
+
+
+def test_unzip():
+    def _to_lists(seq, n=10):
+        """iter of iters -> finite list of finite lists
+        """
+        def initial(s):
+            return list(take(n, s))
+
+        return initial(map(initial, seq))
+
+    def _assert_initial_matches(a, b, n=10):
+        assert list(take(n, a)) == list(take(n, b))
+
+    # Unzips a simple list correctly
+    assert _to_lists(unzip([('a', 1), ('b', 2), ('c', 3)])) \
+        == [['a', 'b', 'c'], [1, 2, 3]]
+
+    # Can handle a finite number of infinite iterators (the naive unzip
+    # implementation `zip(*args)` impelementation fails on this example).
+    a, b, c = unzip(zip(count(1), repeat(0), repeat(1)))
+    _assert_initial_matches(a, count(1))
+    _assert_initial_matches(b, repeat(0))
+    _assert_initial_matches(c, repeat(1))
+
+    # Sensibly handles empty input
+    assert list(unzip(zip([]))) == []
```

## Why correct

The change correctly adds `unzip` to `toolz.sandbox` by implementing it in `core.py` and exporting it from `__init__.py`. The implementation uses `tee` and `starmap(pluck, ...)` to split a sequence of tuples into separate iterators, which avoids the memory and laziness problems of the naive `zip(*seq)` approach. The verifier tests confirm this works for ordinary finite input, correctly produces empty output for empty input, and crucially handles a finite sequence of infinite iterators—something the naive approach cannot do—by verifying that unzipping `zip(count(1), repeat(0), repeat(1))` yields iterators whose first elements match the original infinite sources.
