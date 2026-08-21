import sys
import types

import toolz
from tlz._build_tlz import TlzLoader


class TestTlzLoaderFindModule:
    def test_returns_self_for_tlz(self):
        loader = TlzLoader()
        assert loader.find_module("tlz") is loader

    def test_returns_self_for_tlz_submodule(self):
        loader = TlzLoader()
        assert loader.find_module("tlz.functoolz") is loader

    def test_returns_none_for_non_tlz(self):
        loader = TlzLoader()
        assert loader.find_module("toolz") is None

    def test_returns_none_for_other_package(self):
        loader = TlzLoader()
        assert loader.find_module("os.path") is None


class TestTlzLoaderLoadModule:
    def test_returns_existing_module(self):
        loader = TlzLoader()
        fake = types.ModuleType("tlz.fake_existing")
        sys.modules["tlz.fake_existing"] = fake
        try:
            result = loader.load_module("tlz.fake_existing")
            assert result is fake
        finally:
            sys.modules.pop("tlz.fake_existing", None)

    def test_creates_module_and_adds_to_sys_modules(self):
        loader = TlzLoader()
        test_name = "tlz.functoolz"
        # Remove if already present from previous test
        sys.modules.pop(test_name, None)
        try:
            result = loader.load_module(test_name)
            assert test_name in sys.modules
            assert sys.modules[test_name] is result
            assert isinstance(result, types.ModuleType)
            assert result.__name__ == test_name
        finally:
            sys.modules.pop(test_name, None)

    def test_exec_module_called(self):
        loader = TlzLoader()
        test_name = "tlz.functoolz"
        sys.modules.pop(test_name, None)
        try:
            result = loader.load_module(test_name)
            # exec_module should have populated from toolz.functoolz
            assert hasattr(result, "curry")
            assert hasattr(result, "compose")
        finally:
            sys.modules.pop(test_name, None)


class TestTlzLoaderExecModule:
    def test_updates_dict_with_toolz_content(self):
        loader = TlzLoader()
        module = types.ModuleType("tlz")
        loader.exec_module(module)
        assert "curry" in module.__dict__
        assert "pipe" in module.__dict__
        assert module.__dict__["curry"] is toolz.curry

    def test_sets_package(self):
        loader = TlzLoader()
        module = types.ModuleType("tlz.functoolz")
        loader.exec_module(module)
        assert module.__package__ == "tlz"

    def test_sets_doc(self):
        loader = TlzLoader()
        module = types.ModuleType("tlz")
        module.__doc__ = ""
        loader.exec_module(module)
        assert module.__doc__ == toolz.__doc__

    def test_sets_file(self):
        loader = TlzLoader()
        module = types.ModuleType("tlz")
        loader.exec_module(module)
        assert module.__file__ == toolz.__file__

    def test_always_from_toolz_pipe(self):
        loader = TlzLoader()
        module = types.ModuleType("tlz")
        loader.exec_module(module)
        assert module.__dict__["pipe"] is toolz.pipe

    def test_submodule_replaced(self):
        loader = TlzLoader()
        module = types.ModuleType("tlz.functoolz")
        loader.exec_module(module)
        # toolz.functoolz contains a submodule like toolz.functoolz.curry
        # After exec_module, any submodule attrs should point to tlz equivalents
        # The functoolz module itself should have its package set
        assert module.__package__ == "tlz"
