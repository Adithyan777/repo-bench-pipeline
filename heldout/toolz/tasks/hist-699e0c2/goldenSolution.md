# Golden solution: 699e0c2

Commit `699e0c217622abacd99498377faa9a7531100a90` (parent `8cdc7fec3da3196f74ddc1dd25da81a1446a0bfc`): Merge pull request #244 from themiurgo/peek

The historical change, applied to `input/` gives `solution/` exactly (hygiene overlay files aside).

```diff
diff --git a/AUTHORS.md b/AUTHORS.md
index 7ea041f..e232e8b 100644
--- a/AUTHORS.md
+++ b/AUTHORS.md
@@ -21,3 +21,5 @@ Tom Prince                                      [@tomprince](https://github.com/
 Bart van Merriënboer                            [@bartvm](https://github.com/bartvm)
 
 Nikolaos-Digenis Karagiannis                    [@digenis](https://github.com/digenis/)
+
+[Antonio Lima](https://twitter.com/themiurgo)   [@themiurgo](https://github.com/themiurgo/)
diff --git a/doc/source/api.rst b/doc/source/api.rst
index 706b36c..f985217 100644
--- a/doc/source/api.rst
+++ b/doc/source/api.rst
@@ -33,6 +33,7 @@ Itertoolz
    nth
    partition
    partition_all
+   peek
    pluck
    reduceby
    remove
diff --git a/toolz/itertoolz.py b/toolz/itertoolz.py
index a91278d..544afda 100644
--- a/toolz/itertoolz.py
+++ b/toolz/itertoolz.py
@@ -12,7 +12,7 @@ __all__ = ('remove', 'accumulate', 'groupby', 'merge_sorted', 'interleave',
            'first', 'second', 'nth', 'last', 'get', 'concat', 'concatv',
            'mapcat', 'cons', 'interpose', 'frequencies', 'reduceby', 'iterate',
            'sliding_window', 'partition', 'partition_all', 'count', 'pluck',
-           'join', 'tail', 'diff', 'topk')
+           'join', 'tail', 'diff', 'topk', 'peek')
 
 
 def remove(predicate, seq):
@@ -877,3 +877,22 @@ def topk(k, seq, key=None):
     if key and not callable(key):
         key = getter(key)
     return tuple(heapq.nlargest(k, seq, key=key))
+
+
+def peek(seq):
+    """ Retrieve the next element of a sequence
+
+    Returns the first element and an iterable equivalent to the original
+    sequence, still having the element retrieved.
+
+    >>> seq = [0, 1, 2, 3, 4]
+    >>> first, seq = peek(seq)
+    >>> first
+    0
+    >>> list(seq)
+    [0, 1, 2, 3, 4]
+
+    """
+    iterator = iter(seq)
+    item = next(iterator)
+    return item, itertools.chain([item], iterator)
diff --git a/toolz/tests/test_itertoolz.py b/toolz/tests/test_itertoolz.py
index 7e3e028..0a2d522 100644
--- a/toolz/tests/test_itertoolz.py
+++ b/toolz/tests/test_itertoolz.py
@@ -11,7 +11,7 @@ from toolz.itertoolz import (remove, groupby, merge_sorted,
                              reduceby, iterate, accumulate,
                              sliding_window, count, partition,
                              partition_all, take_nth, pluck, join,
-                             diff, topk)
+                             diff, topk, peek)
 from toolz.compatibility import range, filter
 from operator import add, mul
 
@@ -458,3 +458,12 @@ def test_topk():
 
 def test_topk_is_stable():
     assert topk(4, [5, 9, 2, 1, 5, 3], key=lambda x: 1) == (5, 9, 2, 1)
+
+
+def test_peek():
+    alist = ["Alice", "Bob", "Carol"]
+    element, blist  = peek(alist)
+    element == alist[0]
+    assert list(blist) == alist
+
+    assert raises(StopIteration, lambda: peek([]))
```

## Why correct

The change adds a new `peek` function to `itertoolz.py` and exports it in the module's `__all__` tuple. The implementation converts the input sequence to an iterator, pulls the first element with `next`, and then returns that element paired with a new iterable formed by chaining the pulled element back onto the front of the remaining iterator. This satisfies the required behavior of returning the first element while still leaving it present in the returned iterable. The verifier tests confirm this works by checking that `peek` can extract the first item from a list and that converting the returned iterable back to a list reproduces the original sequence unchanged, including that first element.
