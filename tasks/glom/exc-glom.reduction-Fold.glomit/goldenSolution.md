# Golden solution: glom.reduction.Fold.glomit

Restores the original body of `glomit(self, target, scope)` in `glom/reduction.py` (lines 68-83); the excised input raises `raise NotImplementedError("excised")` in its place.

```diff
--- input/glom/reduction.py
+++ solution/glom/reduction.py
@@ -66,7 +66,21 @@
                             (self.__class__.__name__, init))
 
     def glomit(self, target, scope):
-        raise NotImplementedError("excised")
+        is_agg = False
+        if scope[MODE] is GROUP and scope.get(CUR_AGG) is None:
+            scope[CUR_AGG] = self
+            is_agg = True
+
+        if self.subspec is not T:
+            target = scope[glom](target, self.subspec, scope)
+
+        if is_agg:
+            return self._agg(target, scope[ACC_TREE])
+        try:
+            return self._fold(target_iter(target, scope))
+        except UnregisteredTarget as ut:
+            raise FoldError('can only %s on iterable targets, not %s type (%s)'
+                            % (self.__class__.__name__, type(target).__name__, ut))
 
     def _fold(self, iterator):
         ret, op = self.init(), self.op
```

## Why correct

The diff restores the full body of `Fold.glomit` that was previously replaced with a `NotImplementedError` stub. The restored implementation handles the `GROUP` mode by setting up aggregation context via `CUR_AGG`, evaluates the `subspec` on the target when it is not the default `T`, then either returns an aggregated result via `_agg` or folds over the target's iteration via `_fold`. This re-enables the core reduction machinery so that `Fold`-derived operations like `flatten`, `merge`, and `sum` can actually process targets instead of failing unconditionally. The verifier tests exercise `glom` error formatting and stack traces on specs that rely on these reduction paths functioning correctly; with `glomit` working again, those specs execute rather than hitting `NotImplementedError`, allowing the tests to pass.
