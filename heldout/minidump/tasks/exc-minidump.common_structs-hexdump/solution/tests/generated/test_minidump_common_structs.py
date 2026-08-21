import asyncio

import pytest

from minidump.common_structs import MinidumpMemorySegment, construct_table, hexdump


def run_async(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


class TestHexdump:
    def test_empty(self):
        assert hexdump(b"") == ""

    def test_single_byte(self):
        result = hexdump(b"\x41")
        assert (
            result
            == "00000000:  41                                                 |A|"
        )

    def test_ascii_string(self):
        result = hexdump(b"Hello")
        assert (
            result
            == "00000000:  48 65 6c 6c 6f                                     |Hello|"
        )

    def test_non_ascii_bytes(self):
        result = hexdump(b"\x00\x01\x02\x03")
        assert (
            result
            == "00000000:  00 01 02 03                                        |....|"
        )

    def test_custom_sep(self):
        result = hexdump(b"\x00\x01", sep="?")
        assert (
            result
            == "00000000:  00 01                                              |??|"
        )

    def test_start_offset(self):
        result = hexdump(b"AB", start=0x1000)
        assert (
            result
            == "00001000(+0000):  41 42                                              |AB|"  # noqa: E501
        )

    def test_multiple_rows(self):
        result = hexdump(b"A" * 32)
        lines = result.split("\n")
        assert len(lines) == 2
        assert lines[0].startswith("00000000:")
        assert lines[1].startswith("00000010:")

    def test_odd_length(self):
        result = hexdump(b"\x01\x02\x03", length=2)
        lines = result.split("\n")
        assert len(lines) == 2

    def test_hex_formatting_single_digit(self):
        result = hexdump(b"\x0f")
        assert "0f" in result

    def test_mixed_content(self):
        result = hexdump(b"Hi\x00!")
        assert "Hi" in result
        assert "!" in result


class TestConstructTable:
    def test_basic(self):
        lines = [["Name", "Age"], ["Alice", "30"]]
        result = construct_table(lines)
        assert "Name" in result
        assert "Alice" in result
        assert "---" in result  # separator line

    def test_no_separate_head(self):
        lines = [["Name", "Age"], ["Alice", "30"]]
        result = construct_table(lines, separate_head=False)
        assert "---" not in result

    def test_empty_lines(self):
        result = construct_table([])
        assert result is None

    def test_multiple_columns(self):
        lines = [["A", "BB", "CCC"], ["DD", "E", "FFFF"]]
        result = construct_table(lines)
        lines_out = result.strip().split("\n")
        assert len(lines_out) == 3  # header + separator + data

    def test_single_row(self):
        lines = [["Only", "Row"]]
        result = construct_table(lines)
        assert "Only" in result
        assert "Row" in result
        # With separate_head=True (default), even a single row gets a separator
        assert "---" in result

    def test_single_row_no_separator(self):
        lines = [["Only", "Row"]]
        result = construct_table(lines, separate_head=False)
        assert "Only" in result
        assert "Row" in result
        assert "---" not in result

    def test_column_padding(self):
        lines = [["X", "YYYYY"], ["ZZZZZ", "A"]]
        result = construct_table(lines)
        assert "X" in result
        assert "YYYYY" in result


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


class TestMinidumpMemorySegmentRead:
    def test_read_success(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        data = b"ABCDEFGH" * 32  # 256 bytes
        fh = FakeFileHandler(data)

        result = seg.read(0x1000, 8, fh)
        assert result == b"ABCDEFGH"

    def test_read_offset(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        data = b"01234567" * 32
        fh = FakeFileHandler(data)

        result = seg.read(0x1004, 4, fh)
        assert result == b"4567"

    def test_read_wrong_segment_raises(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        fh = FakeFileHandler(b"x" * 256)

        with pytest.raises(Exception, match="Reading from wrong segment"):
            seg.read(0x2000, 4, fh)

    def test_read_cross_boundary_raises(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        fh = FakeFileHandler(b"x" * 256)

        with pytest.raises(Exception, match="Read would cross boundaries"):
            seg.read(0x10F0, 0x20, fh)

    def test_read_restores_position(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        data = b"01234567" * 32
        fh = FakeFileHandler(data)
        fh.seek(42, 0)

        seg.read(0x1000, 4, fh)
        assert fh.tell() == 42


class TestMinidumpMemorySegmentAread:
    def test_aread_success(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        data = b"ABCDEFGH" * 32
        fh = AsyncFakeFileHandler(data)

        result = run_async(seg.aread(0x1000, 8, fh))
        assert result == b"ABCDEFGH"

    def test_aread_offset(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        data = b"01234567" * 32
        fh = AsyncFakeFileHandler(data)

        result = run_async(seg.aread(0x1004, 4, fh))
        assert result == b"4567"

    def test_aread_wrong_segment_raises(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        fh = AsyncFakeFileHandler(b"x" * 256)

        with pytest.raises(Exception, match="Reading from wrong segment"):
            run_async(seg.aread(0x2000, 4, fh))

    def test_aread_cross_boundary_raises(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        fh = AsyncFakeFileHandler(b"x" * 256)

        with pytest.raises(Exception, match="Read would cross boundaries"):
            run_async(seg.aread(0x10F0, 0x20, fh))

    def test_aread_restores_position(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        data = b"01234567" * 32
        fh = AsyncFakeFileHandler(data)
        run_async(fh.seek(42, 0))

        run_async(seg.aread(0x1000, 4, fh))
        assert fh.tell() == 42


class TestMinidumpMemorySegmentSearch:
    def test_search_find_all(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        data = b"X" * 10 + b"PATTERN" + b"Y" * 20 + b"PATTERN" + b"Z" * 200
        fh = FakeFileHandler(data)

        result = seg.search(b"PATTERN", fh)
        assert len(result) == 2
        assert result[0] == 0x1000 + 10
        assert result[1] == 0x1000 + 10 + 7 + 20

    def test_search_find_first(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        data = b"X" * 10 + b"PATTERN" + b"Y" * 20 + b"PATTERN" + b"Z" * 200
        fh = FakeFileHandler(data)

        result = seg.search(b"PATTERN", fh, find_first=True)
        assert result == [0x1000 + 10]

    def test_search_not_found(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        data = b"X" * 256
        fh = FakeFileHandler(data)

        result = seg.search(b"PATTERN", fh)
        assert result == []

    def test_search_pattern_too_long(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x10
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1010

        fh = FakeFileHandler(b"X" * 16)

        result = seg.search(b"PATTERN_TOO_LONG", fh)
        assert result == []

    def test_search_restores_position(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        data = b"X" * 256
        fh = FakeFileHandler(data)
        fh.seek(42, 0)

        seg.search(b"NOTFOUND", fh)
        assert fh.tell() == 42

    def test_search_chunksize_boundary(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        # Pattern spans across a small chunksize boundary
        data = b"A" * 30 + b"PATTERN" + b"B" * 219
        fh = FakeFileHandler(data)

        result = seg.search(b"PATTERN", fh, find_first=True, chunksize=32)
        assert result == [0x1000 + 30]


class TestMinidumpMemorySegmentAsearch:
    def test_asearch_find_all(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        data = b"X" * 10 + b"PATTERN" + b"Y" * 20 + b"PATTERN" + b"Z" * 200
        fh = AsyncFakeFileHandler(data)

        result = run_async(seg.asearch(b"PATTERN", fh))
        assert len(result) == 2
        assert result[0] == 0x1000 + 10
        assert result[1] == 0x1000 + 10 + 7 + 20

    def test_asearch_find_first(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        data = b"X" * 10 + b"PATTERN" + b"Y" * 20 + b"PATTERN" + b"Z" * 200
        fh = AsyncFakeFileHandler(data)

        result = run_async(seg.asearch(b"PATTERN", fh, find_first=True))
        assert result == [0x1000 + 10]

    def test_asearch_not_found(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        data = b"X" * 256
        fh = AsyncFakeFileHandler(data)

        result = run_async(seg.asearch(b"PATTERN", fh))
        assert result == []

    def test_asearch_pattern_too_long(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x10
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1010

        fh = AsyncFakeFileHandler(b"X" * 16)

        result = run_async(seg.asearch(b"PATTERN_TOO_LONG", fh))
        assert result == []

    def test_asearch_restores_position(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        data = b"X" * 256
        fh = AsyncFakeFileHandler(data)
        run_async(fh.seek(42, 0))

        run_async(seg.asearch(b"NOTFOUND", fh))
        assert fh.tell() == 42

    def test_asearch_chunksize_boundary(self):
        seg = MinidumpMemorySegment()
        seg.start_virtual_address = 0x1000
        seg.size = 0x100
        seg.start_file_address = 0x0
        seg.end_virtual_address = 0x1100

        data = b"A" * 30 + b"PATTERN" + b"B" * 219
        fh = AsyncFakeFileHandler(data)

        result = run_async(seg.asearch(b"PATTERN", fh, find_first=True, chunksize=32))
        assert result == [0x1000 + 30]
