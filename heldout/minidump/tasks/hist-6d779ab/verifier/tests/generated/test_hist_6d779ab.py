import asyncio

import pytest

from minidump.common_structs import MinidumpMemorySegment


def run_async(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


class FakeFileHandler:
    """A synchronous fake file handler for testing."""

    def __init__(self, data):
        self._data = data
        self._pos = 0

    def tell(self):
        return self._pos

    def seek(self, pos, whence=0):
        if whence == 0:
            self._pos = pos
        elif whence == 1:
            self._pos += pos
        elif whence == 2:
            self._pos = len(self._data) + pos

    def read(self, size):
        data = self._data[self._pos : self._pos + size]
        self._pos += len(data)
        return data


class AsyncFakeFileHandler:
    """An async fake file handler for testing."""

    def __init__(self, data):
        self._data = data
        self._pos = 0

    def tell(self):
        return self._pos

    async def seek(self, pos, whence=0):
        if whence == 0:
            self._pos = pos
        elif whence == 1:
            self._pos += pos
        elif whence == 2:
            self._pos = len(self._data) + pos

    async def read(self, size):
        data = self._data[self._pos : self._pos + size]
        self._pos += len(data)
        return data


class TestSearchOffsetAccumulation:
    """Tests that search offset accumulates correctly across multiple matches.

    Before the fix, ``offset = marker + 1`` reset the offset instead of
    accumulating it (``offset += marker + 1``), causing second and
    subsequent matches to report incorrect virtual addresses.
    """

    def test_search_three_matches_correct_addresses(self):
        """Three matches: bug would misreport second and third addresses."""
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        # Three occurrences of "PAT" at known offsets
        data = b"A" * 5 + b"PAT" + b"B" * 5 + b"PAT" + b"C" * 5 + b"PAT" + b"D" * 200
        fh = FakeFileHandler(data)

        result = seg.search(b"PAT", fh)
        assert len(result) == 3
        assert result[0] == 0x1000 + 5
        assert result[1] == 0x1000 + 5 + 3 + 5
        assert result[2] == 0x1000 + 5 + 3 + 5 + 3 + 5

    def test_asearch_three_matches_correct_addresses(self):
        """Async version: three matches must have correct addresses."""
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        data = b"A" * 5 + b"PAT" + b"B" * 5 + b"PAT" + b"C" * 5 + b"PAT" + b"D" * 200
        fh = AsyncFakeFileHandler(data)

        result = run_async(seg.asearch(b"PAT", fh))
        assert len(result) == 3
        assert result[0] == 0x1000 + 5
        assert result[1] == 0x1000 + 5 + 3 + 5
        assert result[2] == 0x1000 + 5 + 3 + 5 + 3 + 5

    def test_search_five_matches_progressive_addresses(self):
        """Five matches: bug would produce same wrong address for later hits."""
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x2000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x2100

        data = b"X" * 4 + b"HI" + b"Y" * 4 + b"HI" + b"Z" * 4 + b"HI" + b"W" * 4 + b"HI" + b"V" * 4 + b"HI" + b"U" * 200
        fh = FakeFileHandler(data)

        result = seg.search(b"HI", fh)
        assert len(result) == 5
        expected = [
            0x2000 + 4,
            0x2000 + 4 + 2 + 4,
            0x2000 + 4 + 2 + 4 + 2 + 4,
            0x2000 + 4 + 2 + 4 + 2 + 4 + 2 + 4,
            0x2000 + 4 + 2 + 4 + 2 + 4 + 2 + 4 + 2 + 4,
        ]
        assert result == expected

    def test_asearch_five_matches_progressive_addresses(self):
        """Async version: five matches must all have distinct correct addresses."""
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x2000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x2100

        data = b"X" * 4 + b"HI" + b"Y" * 4 + b"HI" + b"Z" * 4 + b"HI" + b"W" * 4 + b"HI" + b"V" * 4 + b"HI" + b"U" * 200
        fh = AsyncFakeFileHandler(data)

        result = run_async(seg.asearch(b"HI", fh))
        assert len(result) == 5
        expected = [
            0x2000 + 4,
            0x2000 + 4 + 2 + 4,
            0x2000 + 4 + 2 + 4 + 2 + 4,
            0x2000 + 4 + 2 + 4 + 2 + 4 + 2 + 4,
            0x2000 + 4 + 2 + 4 + 2 + 4 + 2 + 4 + 2 + 4,
        ]
        assert result == expected

    def test_search_adjacent_patterns(self):
        """Adjacent patterns: ``PAT`` immediately followed by ``PAT``."""
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x3000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x3100

        data = b"A" * 8 + b"PAT" * 3 + b"B" * 200
        fh = FakeFileHandler(data)

        result = seg.search(b"PAT", fh)
        assert len(result) == 3
        assert result[0] == 0x3000 + 8
        assert result[1] == 0x3000 + 8 + 3
        assert result[2] == 0x3000 + 8 + 3 + 3

    def test_asearch_adjacent_patterns(self):
        """Async adjacent patterns must all be found at correct offsets."""
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x3000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x3100

        data = b"A" * 8 + b"PAT" * 3 + b"B" * 200
        fh = AsyncFakeFileHandler(data)

        result = run_async(seg.asearch(b"PAT", fh))
        assert len(result) == 3
        assert result[0] == 0x3000 + 8
        assert result[1] == 0x3000 + 8 + 3
        assert result[2] == 0x3000 + 8 + 3 + 3
