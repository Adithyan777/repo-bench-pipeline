# Golden solution: 4a48227

Commit `4a4822740692de2ead233fae232530ad4bbcf931` (parent `10d07943849e3f00cc22b7ebc55485a75ef2dfa6`): add STOP support to Check tests, fix a bug in Check where failing validator functions wouldn't trigger the returning of the default

The historical change, applied to `input/` gives `solution/` exactly (hygiene overlay files aside).

```diff
diff --git a/glom/core.py b/glom/core.py
index b639b4a..322ec78 100644
--- a/glom/core.py
+++ b/glom/core.py
@@ -1075,7 +1075,10 @@ class Check(object):
                 except Exception as e:
                     msg = ('expected %r check to validate target'
                            % getattr(validator, '__name__', None) or ('#%s' % i))
-                    if type(e) is not self._ValidationError:
+                    if type(e) is self._ValidationError:
+                        if self.default is not RAISE:
+                            return self.default
+                    else:
                         msg += ' (got exception: %r)' % e
                     errs.append(msg)
 
diff --git a/glom/test/test_check.py b/glom/test/test_check.py
index aead5b5..6bbdb4c 100644
--- a/glom/test/test_check.py
+++ b/glom/test/test_check.py
@@ -1,16 +1,26 @@
 
 from pytest import raises
 
-from glom import glom, Check, CheckError, Coalesce, OMIT, T
+from glom import glom, Check, CheckError, Coalesce, OMIT, STOP, T
 
 
 def test_check_basic():
     assert glom([0, OMIT], [T]) == [0]  # sanity check OMIT
 
-    target = [{'id': 0}, {'id': 1}]
+    target = [{'id': 0}, {'id': 1}, {'id': 2}]
+
+    # check that skipping non-passing values works
     assert glom(target, ([Coalesce(Check('id', equal_to=0), default=OMIT)], T[0])) == {'id': 0}
     assert glom(target, ([Check('id', equal_to=0, default=OMIT)], T[0])) == {'id': 0}
 
+    # check that stopping iteration on non-passing values works
+    assert glom(target, [Check('id', equal_to=0, default=STOP)]) == [{'id': 0}]
+
+    # check that stopping chain execution on non-passing values works
+    spec = (Check(validate=lambda x: len(x) > 0, default=STOP), T[0])
+    assert glom('hello', spec) == 'h'
+    assert glom('', spec) == ''  # would fail with IndexError if STOP didn't work
+
     target = [1, 'a']
     assert glom(target, [Check(type=str, default=OMIT)]) == ['a']
     assert glom(target, [Check(type=(str, int))]) == [1, 'a']
```

## Why correct

The change makes `Check.glomit` return `self.default` when a validator raises `self._ValidationError`, whereas before it only returned the default for non-validation exceptions. This is correct because the task requires the default to apply when a validator raises a validation error, not just other exceptions. The test `test_check_basic` verifies this through cases like `Check(validate=lambda x: False)` and `Check(validate=int)` on `'-3.14'`—these validators raise validation errors, and with the fix, if a default were configured, it would be returned instead of propagating the error. The diff specifically adds a branch that checks `if type(e) is self._ValidationError` and returns `self.default` when it is set (not `RAISE`), ensuring the configured default is honored for validation failures just as it was for other exceptions.
