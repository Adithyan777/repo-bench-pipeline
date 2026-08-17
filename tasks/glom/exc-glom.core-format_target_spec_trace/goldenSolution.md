# Golden solution: glom.core.format_target_spec_trace

Restores the original body of `format_target_spec_trace(scope, root_error, width=TRACE_WIDTH, depth=0, prev_target=_MISSING, last_branch=True)` in `glom/core.py` (lines 242-279); the excised input raises `raise NotImplementedError("excised")` in its place.

```diff
--- input/glom/core.py
+++ solution/glom/core.py
@@ -243,7 +243,40 @@
     """
     unpack a scope into a multi-line but short summary
     """
-    raise NotImplementedError("excised")
+    segments = []
+    indent = " " + "|" * depth
+    tick = "| " if depth else "- "
+    def mk_fmt(label, t=None):
+        pre = indent + (t or tick) + label + ": "
+        fmt_width = width - len(pre)
+        return lambda v: pre + _format_trace_value(v, fmt_width)
+    fmt_t = mk_fmt("Target")
+    fmt_s = mk_fmt("Spec")
+    fmt_b = mk_fmt("Spec", "+ ")
+    recurse = lambda s, last=False: format_target_spec_trace(s, root_error, width, depth + 1, prev_target, last)
+    tb_exc_line = lambda e: "".join(traceback.format_exception_only(type(e), e))[:-1]
+    fmt_e = lambda e: indent + tick + tb_exc_line(e)
+    for scope, spec, target, error, branches in _unpack_stack(scope):
+        if target is not prev_target:
+            segments.append(fmt_t(target))
+        prev_target = target
+        if branches:
+            segments.append(fmt_b(spec))
+            segments.extend([recurse(s) for s in branches[:-1]])
+            segments.append(recurse(branches[-1], last_branch))
+        else:
+            segments.append(fmt_s(spec))
+        if error is not None and error is not root_error:
+            last_line_error = True
+            segments.append(fmt_e(error))
+        else:
+            last_line_error = False
+    if depth:  # \ on first line, X on last line
+        remark = lambda s, m: s[:depth + 1] + m + s[depth + 2:]
+        segments[0] = remark(segments[0], "\\")
+        if not last_branch or last_line_error:
+            segments[-1] = remark(segments[-1], "X")
+    return "\n".join(segments)
 
 
 # TODO: not used (yet)
```

## Why correct

The change restores the full body of `format_target_spec_trace` so it no longer raises `NotImplementedError`. The implementation iterates over the unpacked scope stack, formats each target, spec, and any branch recursions into annotated trace lines with proper indentation and tree-drawing characters (`\`, `|`, `X`), and joins them into a multi-line summary string. This directly satisfies the contract to "unpack a scope into a multi-line but short summary." The verifier tests exercise `glom_cli` with a failing spec (`a.b.c` on `{"a": 1}`), which triggers a `PathAccessError`; the CLI catches this `GlomError` and prints the formatted trace, so restoring `format_target_spec_trace` allows the error path to complete and return exit code 1 with `PathAccessError` in the output, making `test_glom_error_returns_one` pass. Similarly, the `test_check_basic` and `test_check_multi` tests rely on glom error handling that formats traces via this function, so restoring it ensures those checks can complete and propagate errors correctly.
