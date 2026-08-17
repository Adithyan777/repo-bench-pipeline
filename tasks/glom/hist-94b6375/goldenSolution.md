# Golden solution: 94b6375

Commit `94b63752c686a42bf71baeec15e250257aee167d` (parent `599496d9f55f86f19402c692627ea51671c4e9f2`): Merge pull request #196 from mahmoud/arg-mode

The historical change, applied to `input/` gives `solution/` exactly (hygiene overlay files aside).

```diff
diff --git a/codecov.yml b/codecov.yml
new file mode 100644
index 0000000..846b9d4
--- /dev/null
+++ b/codecov.yml
@@ -0,0 +1,2 @@
+ignore:
+  - "**/*_backport.py"  # ignore coverage on vendored py2 backports
diff --git a/glom/core.py b/glom/core.py
index 925f1ae..a24c48e 100644
--- a/glom/core.py
+++ b/glom/core.py
@@ -42,11 +42,12 @@ if PY2:
     _AbstractIterableBase = object
     from .chainmap_backport import ChainMap
     from repr import Repr
+    from .reprlib_backport import recursive_repr
 else:
     basestring = str
     _AbstractIterableBase = ABCMeta('_AbstractIterableBase', (object,), {})
     from collections import ChainMap
-    from reprlib import Repr
+    from reprlib import Repr, recursive_repr
 
 GLOM_DEBUG = os.getenv('GLOM_DEBUG', '').strip().lower()
 GLOM_DEBUG = False if (GLOM_DEBUG in ('', '0', 'false')) else True
@@ -112,6 +113,8 @@ in case of exceptions
 
 MODE =  make_sentinel('MODE')
 
+MIN_MODE =  make_sentinel('MIN_MODE')
+
 CHILD_ERRORS = make_sentinel('CHILD_ERRORS')
 CHILD_ERRORS.__doc__ = """
 ``CHILD_ERRORS`` is used by glom internals to keep track of
@@ -187,11 +190,17 @@ class GlomError(Exception):
         return exc_get_message()
 
 
-def _unpack_stack(scope):
+def _unpack_stack(scope, only_errors=True):
     """
     convert scope to [[scope, spec, target, error, [children]]]
 
     this is a convenience method for printing stacks
+
+    only_errors=True means ignore branches which may still be hanging around
+    which were not involved in the stack trace of the error
+
+    only_errors=False could be useful for debugger / introspection (similar
+    to traceback.print_stack())
     """
     stack = []
     scope = scope.maps[0]
@@ -215,6 +224,11 @@ def _unpack_stack(scope):
         cur, nxt = stack[i], stack[i + 1]
         if cur[3] == nxt[3]:
             cur[3] = None
+    if only_errors:  # trim the stack to the last error
+        # leave at least 1 to not break formatting func below
+        # TODO: make format_target_spec_trace() tolerate an "empty" stack cleanly
+        while len(stack) > 1 and stack[-1][3] is None:
+            stack.pop()
     return stack
 
 
@@ -279,7 +293,7 @@ def format_oneline_trace(scope):
     # if the target is the same, don't repeat it
     segments = []
     prev_target = _MISSING
-    for scope, spec, target, error, branches in _unpack_stack(scope):
+    for scope, spec, target, error, branches in _unpack_stack(scope, only_errors=False):
         segments.append('/')
         if type(spec) in (TType, Path):
             segments.append(bbrepr(spec))
@@ -526,7 +540,7 @@ class _BBRepr(Repr):
         return _BUILTIN_ID_NAME_MAP.get(id(x), ret)
 
 
-bbrepr = _BBRepr().repr
+bbrepr = recursive_repr()(_BBRepr().repr)
 
 
 class _BBReprFormatter(string.Formatter):
@@ -925,7 +939,7 @@ class Coalesce(object):
                 continue
         else:
             if self.default is not _MISSING:
-                ret = self.default
+                ret = arg_val(target, self.default, scope)
             elif self.default_factory is not _MISSING:
                 ret = self.default_factory()
             else:
@@ -1087,19 +1101,8 @@ class Call(object):
 
     def glomit(self, target, scope):
         'run against the current target'
-        def _eval(t):
-            if type(t) in (Spec, TType):
-                return scope[glom](target, t, scope)
-            return t
-        if type(self.args) is TType:
-            args = _eval(self.args)
-        else:
-            args = [_eval(a) for a in self.args]
-        if type(self.kwargs) is TType:
-            kwargs = _eval(self.kwargs)
-        else:
-            kwargs = {name: _eval(val) for name, val in self.kwargs.items()}
-        return _eval(self.func)(*args, **kwargs)
+        r = lambda spec: arg_val(target, spec, scope)
+        return r(self.func)(*r(self.args), **r(self.kwargs))
 
     def __repr__(self):
         cn = self.__class__.__name__
@@ -1566,7 +1569,7 @@ def _t_eval(target, _t, scope):
             # S(var='spec') style assignment
             _, kwargs = t_path[2]
             scope.update({
-                k: scope[glom](target, v, scope) for k, v in kwargs.items()})
+                k: arg_val(target, v, scope) for k, v in kwargs.items()})
             return target
 
     else:
@@ -1574,8 +1577,7 @@ def _t_eval(target, _t, scope):
     pae = None
     while i < fetch_till:
         op, arg = t_path[i], t_path[i + 1]
-        if type(arg) in (Spec, TType, Val):
-            arg = scope[glom](target, arg, scope)
+        arg = arg_val(target, arg, scope)
         if op == '.':
             try:
                 cur = getattr(cur, arg)
@@ -2258,6 +2260,7 @@ def glom(target, spec, **kwargs):
         Path: kwargs.pop('path', []),
         Inspect: kwargs.pop('inspector', None),
         MODE: AUTO,
+        MIN_MODE: None,
         CHILD_ERRORS: [],
         'globals': ScopeVars({}, {}),
     })
@@ -2274,7 +2277,7 @@ def glom(target, spec, **kwargs):
         except skip_exc:
             if default is _MISSING:
                 raise
-            ret = default
+            ret = default  # should this also be arg_val'd?
     except Exception as e:
         if glom_debug:
             raise
@@ -2335,16 +2338,19 @@ def _glom(target, spec, scope):
         UP: parent,
         CHILD_ERRORS: [],
         MODE: pmap[MODE],
+        MIN_MODE: pmap[MIN_MODE],
     })
     pmap[LAST_CHILD_SCOPE] = scope
 
     try:
         if type(spec) is TType:  # must go first, due to callability
+            scope[MIN_MODE] = None  # None is tombstone
             return _t_eval(target, spec, scope)
         elif _has_callable_glomit(spec):
+            scope[MIN_MODE] = None
             return spec.glomit(target, scope)
 
-        return scope.maps[0][MODE](target, spec, scope)
+        return (scope.maps[0][MIN_MODE] or scope.maps[0][MODE])(target, spec, scope)
     except Exception as e:
         scope.maps[1][CHILD_ERRORS].append(scope)
         scope.maps[0][CUR_ERROR] = e
@@ -2538,3 +2544,38 @@ def FILL(target, spec, scope):
     if callable(spec):
         return spec(target)
     return spec
+
+class _ArgValuator(object):
+    def __init__(self):
+        self.cache = {}
+
+    def mode(self, target, spec, scope):
+        """
+        similar to FILL, but without function calling;
+        useful for default, scope assignment, call/invoke, etc
+        """
+        recur = lambda val: scope[glom](target, val, scope)
+        result = spec
+        if type(spec) in (list, dict):  # can contain themselves
+            if id(spec) in self.cache:
+                return self.cache[id(spec)]
+            result = self.cache[id(spec)] = type(spec)()
+            if type(spec) is dict:
+                result.update({recur(key): recur(val) for key, val in spec.items()})
+            else:
+                result.extend([recur(val) for val in spec])
+        if type(spec) in (tuple, set, frozenset):  # cannot contain themselves
+            result = type(spec)([recur(val) for val in spec])
+        return result
+
+
+def arg_val(target, arg, scope):
+    """
+    evaluate an argument to find its value
+    (arg_val phonetically similar to "eval" -- evaluate as an arg)
+    """
+    mode = scope[MIN_MODE]
+    scope[MIN_MODE] = _ArgValuator().mode
+    result = scope[glom](target, arg, scope)
+    scope[MIN_MODE] = mode
+    return result
diff --git a/glom/matching.py b/glom/matching.py
index 1228535..ed71b69 100644
--- a/glom/matching.py
+++ b/glom/matching.py
@@ -14,7 +14,7 @@ from pprint import pprint
 from boltons.iterutils import is_iterable
 from boltons.typeutils import make_sentinel
 
-from .core import GlomError, glom, T, MODE, bbrepr, bbformat, format_invocation, Path, chain_child, Val
+from .core import GlomError, glom, T, MODE, bbrepr, bbformat, format_invocation, Path, chain_child, Val, arg_val
 
 
 _MISSING = make_sentinel('_MISSING')
@@ -152,7 +152,7 @@ class Match(object):
         except GlomError:
             if self.default is _MISSING:
                 raise
-            ret = self.default
+            ret = arg_val(target, self.default, scope)
         return ret
 
     def verify(self, target):
@@ -284,7 +284,7 @@ class _Bool(object):
             return self._glomit(target, scope)
         except GlomError:
             if self.default is not _MISSING:
-                return self.default
+                return arg_val(target, self.default, scope)
             raise
 
     def _m_repr(self):
@@ -685,9 +685,10 @@ def _handle_dict(target, spec, scope):
         key for key in spec_keys
         if _precedence(key) == 0 and type(key) is not Optional
         or type(key) is Required}
-    result = {  # pre-load result with defaults
+    defaults = {  # pre-load result with defaults
         key.key: key.default for key in spec_keys
         if type(key) is Optional and key.default is not _MISSING}
+    result = {}
     for key, val in target.items():
         for maybe_spec_key in spec_keys:
             # handle Required as a special case here rather than letting it be a stand-alone spec
@@ -705,6 +706,8 @@ def _handle_dict(target, spec, scope):
                 break
         else:
             raise MatchError("key {0!r} didn't match any of {1!r}", key, spec_keys)
+    for key in set(defaults) - set(result):
+        result[key] = arg_val(target, defaults[key], scope)
     if required:
         raise MatchError("target missing expected keys: {0}", ', '.join([bbrepr(r) for r in required]))
     return result
@@ -852,7 +855,7 @@ class Switch(object):
                 continue
             return scope[glom](target, valspec, chain_child(scope))
         if self.default is not _MISSING:
-            return self.default
+            return arg_val(target, self.default, scope)
         raise MatchError("no matches for target in %s"  % self.__class__.__name__)
 
     def __repr__(self):
@@ -961,7 +964,7 @@ class Check(object):
             target = scope[glom](target, self.spec, scope)
         if self.types and type(target) not in self.types:
             if self.default is not RAISE:
-                return self.default
+                return arg_val(target, self.default, scope)
             errs.append('expected type to be %r, found type %r' %
                         (self.types[0].__name__ if len(self.types) == 1
                          else tuple([t.__name__ for t in self.types]),
@@ -969,7 +972,7 @@ class Check(object):
 
         if self.vals and target not in self.vals:
             if self.default is not RAISE:
-                return self.default
+                return arg_val(target, self.default, scope)
             if len(self.vals) == 1:
                 errs.append("expected {}, found {}".format(self.vals[0], target))
             else:
@@ -996,7 +999,7 @@ class Check(object):
             # (early return to avoid potentially expensive or even error-causeing
             # string formats)
             if self.default is not RAISE:
-                return self.default
+                return arg_val(target, self.default, scope)
             errs.append('expected instance of %r, found instance of %r' %
                         (self.instance_of[0].__name__ if len(self.instance_of) == 1
                          else tuple([t.__name__ for t in self.instance_of]),
diff --git a/glom/mutation.py b/glom/mutation.py
index 1cf3b11..554cbbd 100644
--- a/glom/mutation.py
+++ b/glom/mutation.py
@@ -11,7 +11,8 @@ import operator
 from pprint import pprint
 
 from .core import Path, T, S, Spec, glom, UnregisteredTarget, GlomError, PathAccessError, UP
-from .core import TType, register_op, TargetRegistry, bbrepr, PathAssignError, _assign_op
+from .core import TType, register_op, TargetRegistry, bbrepr, PathAssignError, arg_val, _assign_op
+
 
 try:
     basestring
@@ -149,10 +150,7 @@ class Assign(object):
         self.missing = missing
 
     def glomit(self, target, scope):
-        if type(self.val) is Spec:
-            val = scope[glom](target, self.val, scope)
-        else:
-            val = self.val
+        val = arg_val(target, self.val, scope)
 
         op, arg, path = self.op, self.arg, self.path
         if self.path.startswith(S):
diff --git a/glom/reprlib_backport.py b/glom/reprlib_backport.py
new file mode 100644
index 0000000..b06f6ba
--- /dev/null
+++ b/glom/reprlib_backport.py
@@ -0,0 +1,37 @@
+import sys
+
+PY2 = (sys.version_info[0] == 2)
+
+if PY2:
+    from thread import get_ident
+else:
+    from _thread import get_ident
+
+
+def recursive_repr(fillvalue='...'):
+    'Decorator to make a repr function return fillvalue for a recursive call'
+
+    def decorating_function(user_function):
+        repr_running = set()
+
+        def wrapper(self):
+            key = id(self), get_ident()
+            if key in repr_running:
+                return fillvalue
+            repr_running.add(key)
+            try:
+                result = user_function(self)
+            finally:
+                repr_running.discard(key)
+            return result
+
+        # Can't use functools.wraps() here because of bootstrap issues
+        wrapper.__module__ = getattr(user_function, '__module__')
+        wrapper.__doc__ = getattr(user_function, '__doc__')
+        wrapper.__name__ = getattr(user_function, '__name__')
+        if not PY2:
+            wrapper.__qualname__ = getattr(user_function, '__qualname__')
+            wrapper.__annotations__ = getattr(user_function, '__annotations__', {})
+        return wrapper
+
+    return decorating_function
diff --git a/glom/test/test_basic.py b/glom/test/test_basic.py
index 2c561c5..2d3d093 100644
--- a/glom/test/test_basic.py
+++ b/glom/test/test_basic.py
@@ -294,7 +294,7 @@ def test_spec_and_recursion():
     assert glom(['cat', {'cat': 1}], T[1][T[0]]) == 1
     assert glom(
         [['ab', 'cd', 'ef'], ''.join],
-        Call(T[1], args=(Spec((T[0], [T[1:]])),))) == 'bdf'
+        Call(T[1], args=(Auto((T[0], [T[1:]])),))) == 'bdf'
 
     # test that spec works on the left of a dict spec
     assert glom({'a': 'A'}, {Spec('a'): 'a', 'a': 'a'}) == {'A': 'A', 'a': 'A'}
diff --git a/glom/test/test_error.py b/glom/test/test_error.py
index 4c51b5e..b97035a 100644
--- a/glom/test/test_error.py
+++ b/glom/test/test_error.py
@@ -60,20 +60,6 @@ def test_line_trace():
     assert fmtd_stack == '/tuple!list/list<0>/dict!int/S'
 
 
-def test_short_trace():
-    stacklifier = ([{'data': S}],)
-    scope = glom([1], stacklifier)[0]['data'][ROOT][LAST_CHILD_SCOPE]
-    fmtd_stack = format_target_spec_trace(scope, None)
-    exp_lines = [
-        " - Target: [1]",
-        " - Spec: ([{'data': S}],)",
-        " - Spec: [{'data': S}]",
-        " - Target: 1",
-        " - Spec: {'data': S}",
-        " - Spec: S",
-    ]
-    assert fmtd_stack.splitlines() == exp_lines
-
 # full traceback testing:
 
 def _norm_stack(formatted_stack, exc):
diff --git a/glom/test/test_match.py b/glom/test/test_match.py
index 3176777..e31dfd8 100644
--- a/glom/test/test_match.py
+++ b/glom/test/test_match.py
@@ -102,6 +102,9 @@ def test_defaults():
 def test_match_default():
     default = []
     res = glom(None, Match(list, default=default))
+    assert res == default
+    default = []
+    res = glom(None, Match(list, default=Val(default)))
     assert res is default
 
 
@@ -500,7 +503,7 @@ def test_switch():
     	Switch({})
     with pytest.raises(TypeError):
     	Switch("wrong type")
-    assert glom(None, Switch({S(a=lambda t: 1): S['a']})) == 1
+    assert glom(None, Switch({S(a=1): S['a']})) == 1
     repr(Switch(cases))
 
 
diff --git a/glom/test/test_mutation.py b/glom/test/test_mutation.py
index 2356175..efa0e81 100644
--- a/glom/test/test_mutation.py
+++ b/glom/test/test_mutation.py
@@ -1,7 +1,7 @@
 import pytest
 
 from glom import glom, Path, T, S, Spec, Glommer, PathAssignError, PathAccessError
-from glom import assign, Assign, delete, Delete, PathDeleteError
+from glom import assign, Assign, delete, Delete, PathDeleteError, Or
 from glom import core
 from glom.core import UnregisteredTarget
 
@@ -36,9 +36,18 @@ def test_assign():
     assert repr(assign_spec) == repr(eval(repr(assign_spec)))
 
 
+def test_assign_recursive():
+    val = {}
+    val[1] = [val]
+    recur_out = glom({}, Assign(T['a'], val))['a']
+    assert recur_out[1][0] is recur_out
+
+
 def test_assign_spec_val():
     output = glom({'b': 'c'}, Assign('a', Spec('b')))
     assert output['a'] == output['b'] == 'c'
+    output = glom({'b': 'c'}, Assign('a', Or('d', 'b')))
+    assert output['a'] == output['b'] == 'c'
 
 
 def test_unregistered_assign():
diff --git a/glom/test/test_path_and_t.py b/glom/test/test_path_and_t.py
index 14b30b8..7990f5a 100644
--- a/glom/test/test_path_and_t.py
+++ b/glom/test/test_path_and_t.py
@@ -1,7 +1,7 @@
 
 from pytest import raises
 
-from glom import glom, Path, S, T, A, PathAccessError, GlomError, BadSpec, Assign, Delete
+from glom import glom, Path, S, T, A, PathAccessError, GlomError, BadSpec, Or, Assign, Delete
 from glom import core
 
 def test_list_path_access():
@@ -104,6 +104,30 @@ def test_t_picklability():
     assert repr(s_spec) == repr(pickle.loads(pickle.dumps(s_spec)))
 
 
+def test_t_subspec():
+    # tests that arg-mode is a min-mode, allowing for
+    # other specs to be embedded inside T calls
+    data = [
+        {'id': 1},
+        {'pk': 1}]
+
+    get_ids = (
+        S(id_type=int),
+        [S.id_type(Or('id', 'pk'))])
+
+    assert glom(data, get_ids) == [1, 1]
+
+    data = {'a': 1, 'b': 2, 'c': 3}
+
+    # test that "shallow" data structures translate as-is
+    get_vals = (
+        S(seq_type=tuple),
+        S.seq_type([T['a'], T['b'], Or('c', 'd')])
+    )
+
+    assert glom(data, get_vals) == (1, 2, 3)
+
+
 def test_a_forbidden():
     with raises(BadSpec):
         A()  # cannot assign to function call
@@ -222,8 +246,12 @@ def test_path_star():
             self.a = 1
             self.b = {'c': 2}
     val = A()
-    assert glom(val, '*') == [1, {'c': 2}]
-    assert glom(val, '**') == [1, {'c': 2}, 2]
+    if core.PY2:  # compensate for unpredictable attribute order
+        assert sorted(glom(val, '*')) == sorted([1, {'c': 2}])
+        assert sorted(glom(val, '**')) == sorted([1, {'c': 2}, 2])
+    else:
+        assert glom(val, '*') == [1, {'c': 2}]
+        assert glom(val, '**') == [1, {'c': 2}, 2]
     core.PATH_STAR = False
 
 
diff --git a/glom/test/test_scope_vars.py b/glom/test/test_scope_vars.py
index ddd09b7..70a7ee2 100644
--- a/glom/test/test_scope_vars.py
+++ b/glom/test/test_scope_vars.py
@@ -9,7 +9,7 @@ from glom.mutation import PathAssignError
 def test_s_scope_assign():
     data = {'a': 1, 'b': [{'c': 2}, {'c': 3}]}
     output = [{'a': 1, 'c': 2}, {'a': 1, 'c': 3}]
-    assert glom(data, (S(a='a'), ('b', [{'a': S['a'], 'c': 'c'}]))) == output
+    assert glom(data, (S(a=T['a']), ('b', [{'a': S['a'], 'c': 'c'}]))) == output
     assert glom(data, ('b', [{'a': S[ROOT][Val(T)]['a'], 'c': 'c'}])) == output
 
     with pytest.raises(TypeError):
@@ -18,20 +18,20 @@ def test_s_scope_assign():
         S()
 
     assert glom([[1]], (S(v=Vars()), [[A.v.a]], S.v.a)) == 1
-    assert glom(1, (S(v=lambda t: {}), A.v['a'], S.v['a'])) == 1
+    assert glom(1, (S(v={}), A.v['a'], S.v['a'])) == 1
     with pytest.raises(GlomError):
-        glom(1, (S(v=lambda t: 1), A.v.a))
+        glom(1, (S(v=1), A.v.a))
 
     class FailAssign(object):
         def __setattr__(self, name, val):
             raise Exception('nope')
 
     with pytest.raises(PathAssignError):
-        glom(1, (S(v=lambda t: FailAssign()), Path(A.v, 'a')))
+        glom(1, (S(v=FailAssign()), Path(A.v, 'a')))
 
     assert repr(S(a=T.a.b)) == 'S(a=T.a.b)'
 
-    spec = (S(a='x'), S.a)
+    spec = (S(a=T['x']), S.a)
     assert glom({'x': 'y'}, spec) == 'y'
 
     return
```

## Why correct

The change introduces `MIN_MODE` and `arg_val` to enable argument evaluation against targets in glom constructs. Previously, arguments like defaults in `Coalesce` or function arguments in `Call` were not evaluated as glom specs against the current target, which meant nested specs (like `T` or `Spec`) inside arguments would not be resolved. The new `arg_val` function temporarily sets `MIN_MODE` to an `_ArgValuator` mode that recursively evaluates lists, dicts, tuples, and sets, while also handling `Spec`, `TType`, and `Val` objects by glomming them against the target. This is applied to `Coalesce.glomit` for defaults, `Call.glomit` for args and kwargs, `_t_eval` for scope assignments and path arguments, and matching constructs like `Match` and `Check` for their defaults. The tests pass because `test_spec_and_recursion` verifies that `Spec` and `T` expressions nested inside `Call` arguments are properly evaluated against the target, and `test_call_and_target` confirms that `T` references in `Call` args/kwargs resolve to the current target value. The `recursive_repr` backport addition ensures that recursive structures in these evaluated arguments can be safely repr'd without infinite recursion, which is exercised by the various repr tests and deep nesting in the test suite.
