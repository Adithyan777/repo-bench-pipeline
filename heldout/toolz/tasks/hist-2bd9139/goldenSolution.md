# Golden solution: 2bd9139

Commit `2bd9139d0d0e17d3426cb467b5f58b1fb6d8a439` (parent `e052d819b2d8dcf50f0147b5659b9a530204d05f`): Merge pull request #399 from groutr/fix-partition-all

The historical change, applied to `input/` gives `solution/` exactly (hygiene overlay files aside).

```diff
diff --git a/toolz/itertoolz.py b/toolz/itertoolz.py
index a25eea3..71c7ddc 100644
--- a/toolz/itertoolz.py
+++ b/toolz/itertoolz.py
@@ -720,7 +720,23 @@ def partition_all(n, seq):
         yield prev
         prev = item
     if prev[-1] is no_pad:
-        yield prev[:prev.index(no_pad)]
+        try:
+            # If seq defines __len__, then
+            # we can quickly calculate where no_pad starts
+            yield prev[:len(seq) % n]
+        except TypeError:
+            # Get first index of no_pad without using .index()
+            # https://github.com/pytoolz/toolz/issues/387
+            # Binary search from CPython's bisect module,
+            # modified for identity testing.
+            lo, hi = 0, n
+            while lo < hi:
+                mid = (lo + hi) // 2
+                if prev[mid] is no_pad:
+                    hi = mid
+                else:
+                    lo = mid + 1
+            yield prev[:lo]
     else:
         yield prev
 
diff --git a/toolz/tests/test_itertoolz.py b/toolz/tests/test_itertoolz.py
index 93aa856..e0a8d17 100644
--- a/toolz/tests/test_itertoolz.py
+++ b/toolz/tests/test_itertoolz.py
@@ -318,6 +318,17 @@ def test_partition_all():
     assert list(partition_all(3, range(5))) == [(0, 1, 2), (3, 4)]
     assert list(partition_all(2, [])) == []
 
+    # Regression test: https://github.com/pytoolz/toolz/issues/387
+    class NoCompare(object):
+        def __eq__(self, other):
+            if self.__class__ == other.__class__:
+                return True
+            raise ValueError()
+    obj = NoCompare()
+    result = [(obj, obj, obj, obj), (obj, obj, obj)]
+    assert list(partition_all(4, [obj]*7)) == result
+    assert list(partition_all(4, iter([obj]*7))) == result
+
 
 def test_count():
     assert count((1, 2, 3)) == 3
```

## Why correct

The original code used `prev.index(no_pad)` to find where padding started, but this fails for sequences with `__len__` when the sentinel `no_pad` cannot be compared against elements (e.g., objects that raise on `__eq__`). The fix first tries to use `len(seq) % n` for sequences that define `__len__`, which directly computes the correct final chunk size without any searching or comparisons. For sequences without `__len__` (like iterators), it falls back to a binary search using identity testing (`is`) instead of equality, avoiding the comparison issue entirely. The verifier tests confirm this works because `test_partition_all` includes a regression test with `NoCompare` objects that raise `ValueError` on `__eq__`, and the test asserts that both list and iterator inputs produce the correct partitioned output without errors.
