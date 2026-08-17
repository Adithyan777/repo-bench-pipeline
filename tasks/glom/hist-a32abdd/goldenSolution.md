# Golden solution: a32abdd

Commit `a32abddd599f89ede932142848338580da41a5f8` (parent `43db1d704a470f682af6e717695ef2a13920a53b`): glom Match re-raises errors as MatchError

The historical change, applied to `input/` gives `solution/` exactly (hygiene overlay files aside).

```diff
diff --git a/glom/matching.py b/glom/matching.py
index 4587fe1..f31c7eb 100644
--- a/glom/matching.py
+++ b/glom/matching.py
@@ -677,9 +677,14 @@ def _glom_match(target, spec, scope):
             result.append(scope[glom](sub_target, sub_spec, scope))
         return tuple(result)
     elif callable(spec):
-        if spec(target):
-            return target
-        raise MatchError("{}({!r}) did not validate".format(spec.__name__, target))
+        try:
+            if spec(target):
+                return target
+        except Exception as e:
+            raise MatchError("{}({!r}) did not validate (got exception {!r})".format(
+                spec.__name__, target, e))
+        raise MatchError("{}({!r}) did not validate (non truthy return)".format(
+            spec.__name__, target))
     elif target != spec:
         raise MatchError("{!r} does not match {!r}", target, spec)
     return target
diff --git a/glom/test/test_match.py b/glom/test/test_match.py
index 5302412..6028f86 100644
--- a/glom/test/test_match.py
+++ b/glom/test/test_match.py
@@ -30,6 +30,8 @@ def test_basic():
     _chk(Match({int}), {1}, [1])
     _chk(Match(frozenset({float})), frozenset({}), frozenset({"1"}))
     _chk(Match(len), [1], [])
+    with pytest.raises(MatchError):
+        glom(None, Match(len))
     with pytest.raises(MatchError):
         glom([1], Match([]))  # empty shouldn't match
     glom({"a": 1, "b": 2}, Match({str: int}))
```

## Why correct

The diff modifies the callable-spec branch in `_glom_match` so that exceptions thrown by callables like `len` are caught and re-raised as `MatchError` with a descriptive message, rather than leaking the original exception. It also separates the non-truthy return path so that when a callable returns a falsy value (e.g., `len([])` returns `0`), the code raises a distinct `MatchError` instead of falling through. The verifier tests confirm this behavior: `test_basic` asserts that `glom(None, Match(len))` and `glom([1], Match([]))` both raise `MatchError`, which now pass because `len(None)` raises a `TypeError` that gets wrapped, and `len([])` returns `0` which is caught by the new non-truthy branch.
