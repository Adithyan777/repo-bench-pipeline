# Golden solution: 0d75aab

Commit `0d75aab4bfdc6cc7dfa13b1a44a2f05c93f7c884` (parent `81316a1c61df29cfbdc0c501bd4e24091d4362fa`): more specific T dunder attribute error message

The historical change, applied to `input/` gives `solution/` exactly (hygiene overlay files aside).

```diff
diff --git a/glom/core.py b/glom/core.py
index 46e157d..bb77821 100644
--- a/glom/core.py
+++ b/glom/core.py
@@ -1326,7 +1326,9 @@ class TType(object):
 
     def __getattr__(self, name):
         if name.startswith('__'):
-            raise AttributeError('T instances reserve dunder attributes, use T.__()')
+            raise AttributeError('T instances reserve dunder attributes.'
+                                 ' To access the "{name}" attribute, use'
+                                 ' T.__("{d_name}")'.format(name=name, d_name=name[2:]))
         return _t_child(self, '.', name)
 
     def __getitem__(self, item):
diff --git a/glom/test/test_path_and_t.py b/glom/test/test_path_and_t.py
index 6949874..df5bcf4 100644
--- a/glom/test/test_path_and_t.py
+++ b/glom/test/test_path_and_t.py
@@ -230,6 +230,9 @@ def test_t_dict_key():
 
 
 def test_t_dunders():
-    with raises(AttributeError):
+    with raises(AttributeError) as exc_info:
         T.__name__
-    assert glom(1, T.__('class__')) == int
+
+    assert 'use T.__("name__")' in str(exc_info.value)
+
+    assert glom(1, T.__('class__')) is int
```

## Why correct

The change updates the error message in TType.__getattr__ to include the specific dunder attribute name that was accessed and the correct T.__() syntax to use it. The test_t_dunders verifier confirms this by checking that accessing T.__name__ raises an AttributeError containing the substring 'use T.__("name__")', which matches the new formatted message. The test also verifies that glom(1, T.__('class__')) correctly works when the proper syntax is used, demonstrating the behavior is unchanged except for the improved error message.
