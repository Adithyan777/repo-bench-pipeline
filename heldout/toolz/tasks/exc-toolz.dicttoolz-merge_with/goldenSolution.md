# Golden solution: toolz.dicttoolz.merge_with

Restores the original body of `merge_with(func, *dicts, **kwargs)` in `toolz/dicttoolz.py` (lines 56-83); the excised input raises `raise NotImplementedError("excised")` in its place.

```diff
--- input/toolz/dicttoolz.py
+++ solution/toolz/dicttoolz.py
@@ -68,7 +68,19 @@
     See Also:
         merge
     """
-    raise NotImplementedError("excised")
+    if len(dicts) == 1 and not isinstance(dicts[0], Mapping):
+        dicts = dicts[0]
+    factory = _get_factory(merge_with, kwargs)
+
+    values = collections.defaultdict(lambda: [].append)
+    for d in dicts:
+        for k, v in d.items():
+            values[k](v)
+
+    result = factory()
+    for k, v in values.items():
+        result[k] = func(v.__self__)
+    return result
 
 
 def valmap(func, d, factory=dict):
```

## Why correct

The change restores the original body of merge_with so it once again merges multiple dictionaries and applies the given function to the combined values for each key. It first normalizes the case where a single iterable of dicts is passed, then collects values per key using defaultdict with list append, and finally builds the result by calling func on each collected list. This matches the contract and makes the verifier tests pass: test_merge_with checks that merge_with(sum)({1: 1}, {1: 2}) == {1: 3}, test_merge_with_list checks merge_with(sum, [{"a": 1}, {"a": 2}]) == {"a": 3}, and the dicttoolz tests verify behavior with multiple dicts, iterable arguments, custom mappings, and defaultdict factories.
