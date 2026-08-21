# Golden solution: 386c750

Commit `386c75033d64f7be4bac9536cea291b848a47fbf` (parent `1aa72df3a75b3584eb26c4456269e9c0afbc043f`): Merge pull request #551 from LincolnPuzey/revert-isiterable-change

The historical change, applied to `input/` gives `solution/` exactly (hygiene overlay files aside).

```diff
diff --git a/toolz/itertoolz.py b/toolz/itertoolz.py
index 89931ae..5049e5e 100644
--- a/toolz/itertoolz.py
+++ b/toolz/itertoolz.py
@@ -283,7 +283,11 @@ def isiterable(x):
     >>> isiterable(5)
     False
     """
-    return hasattr(x, "__iter__")
+    try:
+        iter(x)
+        return True
+    except TypeError:
+        return False
 
 
 def isdistinct(seq):
diff --git a/toolz/tests/test_itertoolz.py b/toolz/tests/test_itertoolz.py
index 25e7d39..27907b9 100644
--- a/toolz/tests/test_itertoolz.py
+++ b/toolz/tests/test_itertoolz.py
@@ -106,9 +106,34 @@ def test_unique():
 
 
 def test_isiterable():
+    # objects that have a __iter__() or __getitem__() method are iterable
+    # https://docs.python.org/3/library/functions.html#iter
+    class IterIterable:
+        def __iter__(self):
+            return iter(["a", "b", "c"])
+
+    class GetItemIterable:
+        def __getitem__(self, item):
+            return ["a", "b", "c"][item]
+
+    # "if a class sets __iter__() to None, the class is not iterable"
+    # https://docs.python.org/3/reference/datamodel.html#special-method-names
+    class NotIterable:
+        __iter__ = None
+
+    class NotIterableEvenWithGetItem:
+        __iter__ = None
+
+        def __getitem__(self, item):
+            return ["a", "b", "c"][item]
+
     assert isiterable([1, 2, 3]) is True
     assert isiterable('abc') is True
+    assert isiterable(IterIterable()) is True
+    assert isiterable(GetItemIterable()) is True
     assert isiterable(5) is False
+    assert isiterable(NotIterable()) is False
+    assert isiterable(NotIterableEvenWithGetItem()) is False
 
 
 def test_isdistinct():
```

## Why correct

The change replaces the shallow `hasattr(x, "__iter__")` check with a real `iter(x)` call wrapped in try/except, which makes `isiterable` test actual iterability as defined by Python (objects whose `iter()` succeeds are iterable). This aligns the implementation with the documented contract and the verifier tests: the tests include classes like `NotIterable` that set `__iter__ = None` and `NotIterableEvenWithGetItem` that also set `__iter__ = None` despite having `__getitem__`; both must return `False`. The old `hasattr` approach would incorrectly return `True` for these because the attribute exists, whereas calling `iter()` raises `TypeError` and correctly yields `False`. Similarly, `GetItemIterable` (which lacks `__iter__` but has `__getitem__`) is correctly identified as iterable because `iter()` succeeds via the `__getitem__` fallback protocol. The new implementation therefore passes all test assertions by matching Python's actual iteration protocol rather than merely checking attribute presence.
