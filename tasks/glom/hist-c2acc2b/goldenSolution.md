# Golden solution: c2acc2b

Commit `c2acc2b4fa5ef90bbb781fa03e4e5095dd8f0d8c` (parent `00293b2d8c1d9e084148b15f17f2c7338fc0e740`): fixing T[slice] repr

The historical change, applied to `input/` gives `solution/` exactly (hygiene overlay files aside).

```diff
diff --git a/glom/core.py b/glom/core.py
index eaab94b..d24b2f2 100644
--- a/glom/core.py
+++ b/glom/core.py
@@ -414,8 +414,8 @@ class _BBRepr(Repr):
         for name in self.__dict__:
             setattr(self, name, 1024)
 
-    def repr1(self, x, maxlevel):
-        ret = Repr.repr1(self, x, maxlevel)
+    def repr1(self, x, level):
+        ret = Repr.repr1(self, x, level)
         if not ret.startswith('<'):
             return ret
         return _BUILTIN_ID_NAME_MAP.get(id(x), ret)
@@ -1429,6 +1429,15 @@ class Let(object):
         return format_invocation(cn, kwargs=self._binding, repr=bbrepr)
 
 
+def _format_slice(x):
+    if type(x) is not slice:
+        return bbrepr(x)
+    fmt = lambda v: "" if v is None else bbrepr(v)
+    if x.step is None:
+        return fmt(x.start) + ":" + fmt(x.stop)
+    return fmt(x.start) + ":" + fmt(x.stop) + ":" + fmt(x.step)    
+
+
 def _format_t(path, root=T):
     prepr = ['T' if root is T else 'S']
     i = 0
@@ -1437,7 +1446,11 @@ def _format_t(path, root=T):
         if op == '.':
             prepr.append('.' + arg)
         elif op == '[':
-            prepr.append("[%s]" % (bbrepr(arg),))
+            if type(arg) is tuple:
+                index = ", ".join([_format_slice(x) for x in arg])
+            else:
+                index = _format_slice(arg)
+            prepr.append("[%s]" % (index,))
         elif op == '(':
             args, kwargs = arg
             prepr.append(format_invocation(args=args, kwargs=kwargs, repr=bbrepr))
diff --git a/glom/test/test_path_and_t.py b/glom/test/test_path_and_t.py
index f231a5d..8a44299 100644
--- a/glom/test/test_path_and_t.py
+++ b/glom/test/test_path_and_t.py
@@ -29,6 +29,7 @@ def test_empty_path_access():
 def test_path_t_roundtrip():
     # check that T repr roundrips
     assert repr(T['a'].b.c()) == "T['a'].b.c()"
+    assert repr(T[1:]) == "T[1:]"
 
     # check that Path repr roundtrips
     assert repr(Path('a', 1, 'b.b', -1.0)) == "Path('a', 1, 'b.b', -1.0)"
```

## Why correct

The change adds a dedicated `_format_slice` helper that converts slice objects into the familiar `[start:stop:step]` string syntax instead of relying on Python's default slice repr, which would output something like `slice(1, None, None)`. In `_format_t`, slice arguments (and tuples of slices, such as multi-dimensional indices) are now passed through this helper before being wrapped in brackets. The verifier test `test_path_t_roundtrip` explicitly asserts that `repr(T[1:])` equals `"T[1:]"`, confirming that the slice is rendered cleanly without the `slice(...)` constructor call. By handling `None` boundaries as empty strings and preserving the step only when present, the formatter produces concise, readable output that matches the expected Python indexing syntax, which is why the roundtrip test passes.
