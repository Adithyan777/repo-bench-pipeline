# Golden solution: minidump.common_structs.construct_table

Restores the original body of `construct_table(lines, separate_head=True)` in `minidump/common_structs.py` (lines 337-363); the excised input raises `raise NotImplementedError("excised")` in its place.

```diff
--- input/minidump/common_structs.py
+++ solution/minidump/common_structs.py
@@ -337,4 +337,27 @@
 def construct_table(lines, separate_head=True):
     """Prints a formatted table given a 2 dimensional array"""
     # Count the column width
-    raise NotImplementedError("excised")
+    widths = []
+    for line in lines:
+        for i, size in enumerate([len(x) for x in line]):
+            while i >= len(widths):
+                widths.append(0)
+            if size > widths[i]:
+                widths[i] = size
+
+    # Generate the format string to pad the columns
+    print_string = ""
+    for i, width in enumerate(widths):
+        print_string += "{" + str(i) + ":" + str(width) + "} | "
+    if len(print_string) == 0:
+        return
+    print_string = print_string[:-3]
+
+    # Print the actual data
+    t = ""
+    for i, line in enumerate(lines):
+        t += print_string.format(*line) + "\n"
+        if i == 0 and separate_head:
+            t += "-" * (sum(widths) + 3 * (len(widths) - 1)) + "\n"
+
+    return t
```

## Why correct

The change restores the original implementation of `construct_table` by replacing the `raise NotImplementedError` stub with working code that computes per-column widths, builds a padded format string, and returns the formatted table lines with an optional header separator. This satisfies the verifier tests because the restored logic produces the expected string output containing the table data, includes `---` separator lines when `separate_head=True` (as checked by `test_basic`, `test_single_row`, and `test_column_padding`), omits that separator when `separate_head=False` (as in `test_no_separate_head` and `test_single_row_no_separator`), handles multiple columns correctly (`test_multiple_columns`), and returns `None` for empty input (`test_empty_lines`).
