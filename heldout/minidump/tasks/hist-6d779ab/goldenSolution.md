# Golden solution: 6d779ab

Commit `6d779ab2e1cbcba36a88933cf9712082e5d4e7ee` (parent `4e9c80ff2a05e8bde6e22f0e652cda807e3089da`): Merge pull request #21 from ThePwn1sher/master

The historical change, applied to `input/` gives `solution/` exactly (hygiene overlay files aside).

```diff
diff --git a/minidump/common_structs.py b/minidump/common_structs.py
index 52e14cd..8d6f7a4 100644
--- a/minidump/common_structs.py
+++ b/minidump/common_structs.py
@@ -190,7 +190,7 @@ class MinidumpMemorySegment:
 					return fl
 				fl.append(marker + offset + self.start_virtual_address)
 				data = data[marker+1:]
-				offset = marker + 1
+				offset += marker + 1
 				if find_first is True:
 					return fl
 		
@@ -232,7 +232,7 @@ class MinidumpMemorySegment:
 					return fl
 				fl.append(marker + offset + self.start_virtual_address)
 				data = data[marker+1:]
-				offset = marker + 1
+				offset += marker + 1
 				if find_first is True:
 					return fl
 		
```

## Why correct

The bug was that after finding a match, `offset` was being assigned `marker + 1` instead of accumulated with `offset += marker + 1`. This meant that on each subsequent match, the offset was calculated relative to the start of the current `data` slice rather than the original memory segment, causing wrong virtual addresses to be reported for second and later matches. By changing to `+=`, the offset now correctly tracks the total distance from the start of the segment, so `marker + offset + self.start_virtual_address` produces the true virtual address for every occurrence. The tests verify this by checking that multiple matches—whether three, five, or adjacent—are all returned at progressively correct addresses rather than repeated or incorrect ones.
