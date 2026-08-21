# Golden solution: minidump.common_structs.MinidumpMemorySegment.search

Restores the original body of `search(self, pattern, file_handler, find_first=False, chunksize=50 * 1024)` in `minidump/common_structs.py` (lines 175-214); the excised input raises `raise NotImplementedError("excised")` in its place.

```diff
--- input/minidump/common_structs.py
+++ solution/minidump/common_structs.py
@@ -173,7 +173,45 @@
         return data
 
     def search(self, pattern, file_handler, find_first=False, chunksize=50 * 1024):
-        raise NotImplementedError("excised")
+        if len(pattern) > self.size:
+            return []
+        pos = file_handler.tell()
+        file_handler.seek(self.start_file_address, 0)
+        fl = []
+        if find_first is True:
+            chunksize = min(chunksize, self.size)
+            data = b""
+            i = 0
+            while len(data) < self.size:
+                i += 1
+                if chunksize > (self.size - len(data)):
+                    chunksize = self.size - len(data)
+                data += file_handler.read(chunksize)
+                marker = data.find(pattern)
+                if marker != -1:
+                    # print('FOUND! size: %s i: %s read: %s perc: %s' % (self.size, i, i*chunksize, 100*((i*chunksize)/self.size)))  # noqa: E501
+                    file_handler.seek(pos, 0)
+                    return [self.start_virtual_address + marker]
+
+            # print('NOTFOUND! size: %s i: %s read: %s perc %s' % (self.size, i, len(data), 100*(len(data)/self.size) ))  # noqa: E501
+
+        else:
+            data = file_handler.read(self.size)
+            file_handler.seek(pos, 0)
+
+            offset = 0
+            while len(data) > len(pattern):
+                marker = data.find(pattern)
+                if marker == -1:
+                    return fl
+                fl.append(marker + offset + self.start_virtual_address)
+                data = data[marker + 1 :]
+                offset += marker + 1
+                if find_first is True:
+                    return fl
+
+        file_handler.seek(pos, 0)
+        return fl
 
     async def asearch(
         self, pattern, file_handler, find_first=False, chunksize=50 * 1024
```

## Why correct

The restored implementation replaces the `NotImplementedError` with a working search that matches the verifier tests. It first guards against patterns longer than the segment, then branches based on `find_first`: when `find_first` is true it reads the segment in configurable chunks and returns immediately upon finding the first match, which satisfies `test_search_find_first` and `test_search_chunksize_boundary`; when false it reads the entire segment and collects all match offsets, which satisfies `test_search_find_all`. In both branches it preserves and restores the file handler position with `tell`/`seek`, which satisfies `test_search_restores_position`, and returns an empty list when no match is found, which satisfies `test_search_not_found` and `test_search_pattern_too_long`.
