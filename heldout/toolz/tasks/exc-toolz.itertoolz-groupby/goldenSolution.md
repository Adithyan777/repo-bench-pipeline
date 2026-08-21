# Golden solution: toolz.itertoolz.groupby

Restores the original body of `groupby(key, seq)` in `toolz/itertoolz.py` (lines 103-136); the excised input raises `raise NotImplementedError("excised")` in its place.

```diff
--- input/toolz/itertoolz.py
+++ solution/toolz/itertoolz.py
@@ -125,7 +125,15 @@
     See Also:
         countby
     """
-    raise NotImplementedError("excised")
+    if not callable(key):
+        key = getter(key)
+    d = collections.defaultdict(lambda: [].append)
+    for item in seq:
+        d[key(item)](item)
+    rv = {}
+    for k, v in d.items():
+        rv[k] = v.__self__
+    return rv
 
 
 def merge_sorted(*seqs, **kwargs):
```

## Why correct

The diff replaces the `raise NotImplementedError("excised")` placeholder with a proper `groupby` implementation that matches the expected behavior. The new code first converts non-callable keys (like integers or lists) into a getter function using `getter(key)`, which allows grouping by elements or attributes as shown in the contract examples. It then uses a `defaultdict` with `list.append` as the factory to efficiently accumulate items into groups, and finally extracts the underlying lists from the append methods to build the result dictionary. This implementation satisfies `test_groupby` by correctly grouping elements by a callable key function, and satisfies `test_groupby_non_callable` by handling integer and list keys via the `getter` conversion, producing the expected grouped dictionaries.
