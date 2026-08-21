# Golden solution: minidump.common_structs.hexdump

Restores the original body of `hexdump(src, length=16, sep='.', start=0)` in `minidump/common_structs.py` (lines 285-334); the excised input raises `raise NotImplementedError("excised")` in its place.

```diff
--- input/minidump/common_structs.py
+++ solution/minidump/common_structs.py
@@ -291,7 +291,47 @@
 
     @note Full support for python2 and python3 !
     """
-    raise NotImplementedError("excised")
+    result = []
+
+    # Python3 support
+    try:
+        xrange(0, 1)
+    except NameError:
+        xrange = range
+
+    for i in xrange(0, len(src), length):
+        subSrc = src[i : i + length]
+        hexa = ""
+        isMiddle = False  # noqa: F841
+        for h in xrange(0, len(subSrc)):
+            if h == length / 2:
+                hexa += " "
+            h = subSrc[h]
+            if not isinstance(h, int):
+                h = ord(h)
+            h = hex(h).replace("0x", "")
+            if len(h) == 1:
+                h = "0" + h
+            hexa += h + " "
+        hexa = hexa.strip(" ")
+        text = ""
+        for c in subSrc:
+            if not isinstance(c, int):
+                c = ord(c)
+            if 0x20 <= c < 0x7F:
+                text += chr(c)
+            else:
+                text += sep
+        if start == 0:
+            result.append(
+                ("%08x:  %-" + str(length * (2 + 1) + 1) + "s  |%s|") % (i, hexa, text)
+            )
+        else:
+            result.append(
+                ("%08x(+%04x):  %-" + str(length * (2 + 1) + 1) + "s  |%s|")
+                % (start + i, i, hexa, text)
+            )
+    return "\n".join(result)
 
 
 def construct_table(lines, separate_head=True):
```

## Why correct

The diff replaces the `raise NotImplementedError("excised")` stub with a full implementation of `hexdump` that iterates over the source bytes in chunks, formats each chunk as hexadecimal values with a mid-row space, builds a printable text representation using the configurable `sep` character for non-ASCII bytes, and assembles each line with an address prefix (optionally including a start offset). This restored behavior matches the verifier tests exactly: `test_empty` expects an empty string for empty input, `test_single_byte` and `test_ascii_string` verify correct hex and text formatting with zero-padded addresses, `test_non_ascii_bytes` and `test_custom_sep` confirm non-printable characters are replaced by the separator, `test_start_offset` checks the `start` parameter format, `test_multiple_rows` ensures chunking by `length` and address incrementing, `test_odd_length` validates partial final rows, `test_hex_formatting_single_digit` checks zero-padding of single-digit hex values, and `test_mixed_content` confirms ASCII characters appear in the text column while non-ASCII are replaced, all of which the implementation handles correctly.
