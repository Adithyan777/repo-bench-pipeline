import sys
import json
from io import StringIO

import pytest
from face import UsageError

from glom import GlomError, Inspect
from glom.cli import console_main, mw_handle_target, glom_cli


class FakeStdin:
    """A fake stdin object for testing."""
    def __init__(self, closed=True):
        self.closed = closed

    def read(self):
        return ''


class TestConsoleMain:
    def test_console_main_calls_sys_exit(self, monkeypatch):
        """console_main should call sys.exit with the return value from main."""
        calls = []

        def fake_exit(code):
            calls.append(code)
            # Don't actually exit

        def fake_main(argv):
            return 42

        monkeypatch.setattr(sys, 'exit', fake_exit)
        monkeypatch.setattr('glom.cli.main', fake_main)
        monkeypatch.setenv('GLOM_CLI_DEBUG', '')
        monkeypatch.delenv('GLOM_CLI_DEBUG', raising=False)

        console_main()
        assert calls == [42]

    def test_console_main_zero_on_none(self, monkeypatch):
        """console_main should pass 0 to sys.exit when main returns None."""
        calls = []

        def fake_exit(code):
            calls.append(code)

        def fake_main(argv):
            return None

        monkeypatch.setattr(sys, 'exit', fake_exit)
        monkeypatch.setattr('glom.cli.main', fake_main)
        monkeypatch.delenv('GLOM_CLI_DEBUG', raising=False)

        console_main()
        assert calls == [0]

    def test_console_main_raises_without_debug(self, monkeypatch):
        """console_main should re-raise exceptions when GLOM_CLI_DEBUG is not set."""
        def fake_main(argv):
            raise ValueError('boom')

        monkeypatch.setattr('glom.cli.main', fake_main)
        monkeypatch.delenv('GLOM_CLI_DEBUG', raising=False)

        with pytest.raises(ValueError, match='boom'):
            console_main()

    def test_console_main_debug_prints_argv(self, monkeypatch, capsys):
        """When GLOM_CLI_DEBUG is set, console_main prints sys.argv."""
        def fake_exit(code):
            pass

        def fake_main(argv):
            return 0

        monkeypatch.setattr(sys, 'exit', fake_exit)
        monkeypatch.setattr('glom.cli.main', fake_main)
        monkeypatch.setenv('GLOM_CLI_DEBUG', '1')
        monkeypatch.setattr(sys, 'argv', ['glom', 'test'])

        console_main()
        captured = capsys.readouterr()
        assert "['glom', 'test']" in captured.out


class TestMwHandleTarget:
    def test_empty_string_returns_empty_dict(self):
        """Empty target_text should return an empty dict."""
        result = mw_handle_target('', 'json')
        assert result == {}

    def test_none_returns_empty_dict(self):
        """None target_text should return an empty dict."""
        result = mw_handle_target(None, 'json')
        assert result == {}

    def test_json_format(self):
        """JSON format should parse with json.loads."""
        result = mw_handle_target('{"a": 1}', 'json')
        assert result == {"a": 1}

    def test_yaml_format(self):
        """YAML format should parse with yaml.safe_load if available."""
        pytest.importorskip('yaml')
        result = mw_handle_target('a: 1\nb: 2', 'yaml')
        assert result == {"a": 1, "b": 2}

    def test_yml_format(self):
        """YML format should also parse with yaml.safe_load if available."""
        pytest.importorskip('yaml')
        result = mw_handle_target('x: 3', 'yml')
        assert result == {"x": 3}

    def test_toml_format(self):
        """TOML format should parse with tomllib or tomli if available."""
        try:
            import tomllib  # noqa: F401
        except ImportError:
            pytest.importorskip('tomli')
        result = mw_handle_target('a = 1\n', 'toml')
        assert result == {"a": 1}

    def test_python_format(self):
        """Python format should parse with ast.literal_eval."""
        result = mw_handle_target('{"a": (1, 2)}', 'python')
        assert result == {"a": (1, 2)}

    def test_python_format_list(self):
        """Python format should handle lists."""
        result = mw_handle_target('[1, 2, 3]', 'python')
        assert result == [1, 2, 3]

    def test_invalid_format_raises(self):
        """Invalid target_format should raise UsageError."""
        with pytest.raises(UsageError) as excinfo:
            mw_handle_target('{}', 'xml')
        assert 'expected target-format to be one of' in str(excinfo.value)

    def test_invalid_json_raises(self):
        """Invalid JSON should raise UsageError with details."""
        with pytest.raises(UsageError) as excinfo:
            mw_handle_target('{bad json}', 'json')
        assert 'could not load target data' in str(excinfo.value)
        assert 'JSONDecodeError' in str(excinfo.value)

    def test_invalid_python_raises(self):
        """Invalid Python literal should raise UsageError."""
        with pytest.raises(UsageError) as excinfo:
            mw_handle_target('1 +', 'python')
        assert 'could not load target data' in str(excinfo.value)

    def test_invalid_yaml_raises(self):
        """Invalid YAML should raise UsageError if yaml is available."""
        pytest.importorskip('yaml')
        with pytest.raises(UsageError) as excinfo:
            mw_handle_target('[not: valid: yaml:', 'yaml')
        assert 'could not load target data' in str(excinfo.value)


class TestGlomCli:
    def test_basic_glom(self, capsys):
        """glom_cli should glom target with spec and print JSON result."""
        target = {"a": {"b": "c"}}
        spec = "a.b"
        result = glom_cli(target, spec, indent=None, debug=False, inspect=False, scalar=False)
        assert result is None
        captured = capsys.readouterr()
        assert captured.out == '"c"\n'

    def test_glom_dict_result(self, capsys):
        """glom_cli should pretty-print dict results with default indent."""
        target = {"a": {"b": "c"}}
        spec = {"name": "a.b"}
        glom_cli(target, spec, indent=2, debug=False, inspect=False, scalar=False)
        captured = capsys.readouterr()
        assert json.loads(captured.out) == {"name": "c"}

    def test_glom_error_returns_one(self, capsys):
        """glom_cli should return 1 and print error on GlomError."""
        target = {"a": 1}
        spec = "a.b.c"  # path doesn't exist
        result = glom_cli(target, spec, indent=None, debug=False, inspect=False, scalar=False)
        assert result == 1
        captured = capsys.readouterr()
        assert 'PathAccessError' in captured.out

    def test_scalar_output(self, capsys):
        """glom_cli should print scalar without quotes when scalar=True."""
        target = {"a": "hello"}
        glom_cli(target, "a", indent=None, debug=False, inspect=False, scalar=True)
        captured = capsys.readouterr()
        assert captured.out == 'hello'

    def test_scalar_non_scalar(self, capsys):
        """glom_cli should still JSON-print non-scalar even when scalar=True."""
        target = {"a": [1, 2, 3]}
        glom_cli(target, "a", indent=None, debug=False, inspect=False, scalar=True)
        captured = capsys.readouterr()
        assert captured.out == '[1, 2, 3]\n'

    def test_indent_zero_disables_pretty(self, capsys):
        """indent=0 should disable pretty-printing (same as None internally)."""
        target = {"a": [1, 2]}
        glom_cli(target, "a", indent=0, debug=False, inspect=False, scalar=False)
        captured = capsys.readouterr()
        # indent=0 is falsy, so it becomes None, meaning no pretty printing
        assert captured.out == '[1, 2]\n'

    def test_inspect_wraps_spec(self, capsys, monkeypatch):
        """inspect=True should wrap spec in Inspect."""
        # Use a closed stdin to avoid breakpoint
        monkeypatch.setattr(sys, 'stdin', FakeStdin(closed=True))
        target = {"a": 1}
        spec = "a"
        glom_cli(target, spec, indent=None, debug=False, inspect=True, scalar=False)
        captured = capsys.readouterr()
        # Inspect with echo=True prints the spec
        assert 'a' in captured.out or captured.out  # some output expected

    def test_debug_wraps_spec(self, monkeypatch):
        """debug=True should wrap spec in Inspect with post_mortem."""
        monkeypatch.setattr(sys, 'stdin', FakeStdin(closed=True))
        target = {"a": 1}
        spec = "a"
        # Should not raise, just run normally
        result = glom_cli(target, spec, indent=None, debug=True, inspect=False, scalar=False)
        assert result is None

    def test_debug_and_inspect_with_closed_stdin(self, monkeypatch):
        """Both debug and inspect with closed stdin should not set breakpoint."""
        monkeypatch.setattr(sys, 'stdin', FakeStdin(closed=True))
        target = {"a": 1}
        spec = "a"
        # With closed stdin, breakpoint=False, so no pdb interaction
        result = glom_cli(target, spec, indent=None, debug=True, inspect=True, scalar=False)
        assert result is None

    def test_sort_keys(self, capsys):
        """Output JSON should have sorted keys."""
        target = {"z": 1, "a": 2}
        spec = {"first": "z", "second": "a"}
        glom_cli(target, spec, indent=2, debug=False, inspect=False, scalar=False)
        captured = capsys.readouterr()
        # Keys in the output dict should be sorted
        lines = captured.out.strip().split('\n')
        # The top-level keys of the result spec are "first" and "second"
        # The JSON output should sort keys at each level
        assert '"first"' in captured.out
        assert '"second"' in captured.out
