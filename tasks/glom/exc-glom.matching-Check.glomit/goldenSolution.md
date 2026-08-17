# Golden solution: glom.matching.Check.glomit

Restores the original body of `glomit(self, target, scope)` in `glom/matching.py` (lines 958-1008); the excised input raises `raise NotImplementedError("excised")` in its place.

```diff
--- input/glom/matching.py
+++ solution/glom/matching.py
@@ -956,7 +956,56 @@
         pass
 
     def glomit(self, target, scope):
-        raise NotImplementedError("excised")
+        ret = target
+        errs = []
+        if self.spec is not T:
+            target = scope[glom](target, self.spec, scope)
+        if self.types and type(target) not in self.types:
+            if self.default is not RAISE:
+                return arg_val(target, self.default, scope)
+            errs.append('expected type to be %r, found type %r' %
+                        (self.types[0].__name__ if len(self.types) == 1
+                         else tuple([t.__name__ for t in self.types]),
+                         type(target).__name__))
+
+        if self.vals and target not in self.vals:
+            if self.default is not RAISE:
+                return arg_val(target, self.default, scope)
+            if len(self.vals) == 1:
+                errs.append(f"expected {self.vals[0]}, found {target}")
+            else:
+                errs.append(f'expected one of {self.vals}, found {target}')
+
+        if self.validators:
+            for i, validator in enumerate(self.validators):
+                try:
+                    res = validator(target)
+                    if res is False:
+                        raise self._ValidationError
+                except Exception as e:
+                    msg = ('expected %r check to validate target'
+                           % getattr(validator, '__name__', None) or ('#%s' % i))
+                    if type(e) is self._ValidationError:
+                        if self.default is not RAISE:
+                            return self.default
+                    else:
+                        msg += ' (got exception: %r)' % e
+                    errs.append(msg)
+
+        if self.instance_of and not isinstance(target, self.instance_of):
+            # TODO: can these early returns be done without so much copy-paste?
+            # (early return to avoid potentially expensive or even error-causeing
+            # string formats)
+            if self.default is not RAISE:
+                return arg_val(target, self.default, scope)
+            errs.append('expected instance of %r, found instance of %r' %
+                        (self.instance_of[0].__name__ if len(self.instance_of) == 1
+                         else tuple([t.__name__ for t in self.instance_of]),
+                         type(target).__name__))
+
+        if errs:
+            raise CheckError(errs, self, scope[Path])
+        return ret
 
     def __repr__(self):
         cn = self.__class__.__name__
```

## Why correct

The diff restores the full body of `Check.glomit` so it once again evaluates the configured checks (type, value, validators, instance_of) against the target, returns a default when checks fail and a default is configured, and raises `CheckError` with descriptive messages when checks fail and no default is set. This makes the verifier tests pass because `test_check_basic` and `test_check_multi` rely on `Check` actually performing validation, returning defaults like `SKIP` and `STOP`, and raising `CheckError` with the expected error messages, all of which the restored implementation provides.
