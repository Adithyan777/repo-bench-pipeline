from unittest.mock import MagicMock

import pytest

from minidump.minidumpshell import MinidumpShell, args2int


class TestArgs2Int:
    def test_int_input_returns_same(self):
        assert args2int(42) == 42
        assert args2int(0) == 0
        assert args2int(-5) == -5

    def test_decimal_string(self):
        assert args2int("123") == 123
        assert args2int("0") == 0
        assert args2int("-7") == -7

    def test_hex_string_lowercase_prefix(self):
        assert args2int("0x1a") == 26
        assert args2int("0xFF") == 255
        assert args2int("0x0") == 0

    def test_hex_string_uppercase_prefix(self):
        assert args2int("0X1a") == 26
        assert args2int("0XFF") == 255

    def test_binary_string(self):
        assert args2int("0b1010") == 10
        assert args2int("0B1111") == 15
        assert args2int("0b0") == 0

    def test_unknown_format_raises(self):
        with pytest.raises(Exception, match="Unknown integer format!"):
            args2int([1, 2, 3])
        with pytest.raises(Exception, match="Unknown integer format!"):
            args2int(None)
        with pytest.raises(Exception, match="Unknown integer format!"):
            args2int({"a": 1})


class TestMinidumpShellDoMemory:
    def test_do_memory_prints_segments(self, capsys):
        shell = MinidumpShell()
        shell.mini = MagicMock()
        shell.mini.memory_segments = "seg32"
        shell.mini.memory_segments_64 = "seg64"
        shell.mini.memory_info = "meminfo"

        shell.do_memory("")
        captured = capsys.readouterr()
        assert "seg32" in captured.out
        assert "seg64" in captured.out
        assert "meminfo" in captured.out

    def test_do_memory_skips_none(self, capsys):
        shell = MinidumpShell()
        shell.mini = MagicMock()
        shell.mini.memory_segments = None
        shell.mini.memory_segments_64 = "seg64"
        shell.mini.memory_info = None

        shell.do_memory("")
        captured = capsys.readouterr()
        assert "seg64" in captured.out
        assert captured.out.count("None") == 0


class TestMinidumpShellDoThreads:
    def test_do_threads_prints_threads(self, capsys):
        shell = MinidumpShell()
        shell.mini = MagicMock()
        shell.mini.threads = "threads"
        shell.mini.threads_ex = "threads_ex"
        shell.mini.thread_info = "thread_info"

        shell.do_threads("")
        captured = capsys.readouterr()
        assert "threads" in captured.out
        assert "threads_ex" in captured.out
        assert "thread_info" in captured.out

    def test_do_threads_skips_none(self, capsys):
        shell = MinidumpShell()
        shell.mini = MagicMock()
        shell.mini.threads = None
        shell.mini.threads_ex = "threads_ex"
        shell.mini.thread_info = None

        shell.do_threads("")
        captured = capsys.readouterr()
        assert "threads_ex" in captured.out
        assert captured.out.count("None") == 0


class TestMinidumpShellDoComments:
    def test_do_comments_prints_comments(self, capsys):
        shell = MinidumpShell()
        shell.mini = MagicMock()
        shell.mini.comment_a = "comment_a"
        shell.mini.comment_w = "comment_w"

        shell.do_comments("")
        captured = capsys.readouterr()
        assert "comment_a" in captured.out
        assert "comment_w" in captured.out

    def test_do_comments_skips_none(self, capsys):
        shell = MinidumpShell()
        shell.mini = MagicMock()
        shell.mini.comment_a = None
        shell.mini.comment_w = "comment_w"

        shell.do_comments("")
        captured = capsys.readouterr()
        assert "comment_w" in captured.out
        assert captured.out.count("None") == 0


class TestMinidumpShellDoModules:
    def test_do_modules_prints_modules(self, capsys):
        shell = MinidumpShell()
        shell.mini = MagicMock()
        shell.mini.modules = "modules"
        shell.mini.unloaded_modules = "unloaded"

        shell.do_modules("")
        captured = capsys.readouterr()
        assert "modules" in captured.out
        assert "unloaded" in captured.out

    def test_do_modules_skips_none(self, capsys):
        shell = MinidumpShell()
        shell.mini = MagicMock()
        shell.mini.modules = None
        shell.mini.unloaded_modules = "unloaded"

        shell.do_modules("")
        captured = capsys.readouterr()
        assert "unloaded" in captured.out
        assert captured.out.count("None") == 0


class TestMinidumpShellDoTell:
    def test_do_tell_prints_hex_position(self, capsys):
        shell = MinidumpShell()
        shell.reader = MagicMock()
        shell.reader.tell.return_value = 0x1234

        shell.do_tell("")
        captured = capsys.readouterr()
        assert "0x1234" in captured.out

    def test_do_tell_none_prints_warning_then_raises(self, capsys):
        shell = MinidumpShell()
        shell.reader = MagicMock()
        shell.reader.tell.return_value = None

        with pytest.raises(TypeError):
            shell.do_tell("")
        captured = capsys.readouterr()
        assert "Reader not yet positioned" in captured.out
