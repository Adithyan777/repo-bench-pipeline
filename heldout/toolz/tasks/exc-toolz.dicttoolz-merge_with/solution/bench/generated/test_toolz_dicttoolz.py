from collections import OrderedDict

import pytest

from toolz.dicttoolz import dissoc, get_in


class TestGetIn:
    def test_basic_dict_access(self):
        d = {"a": {"b": {"c": 1}}}
        assert get_in(["a", "b", "c"], d) == 1

    def test_single_key(self):
        d = {"name": "Alice"}
        assert get_in(["name"], d) == "Alice"

    def test_nested_list_access(self):
        d = {"purchase": {"items": ["Apple", "Orange"]}}
        assert get_in(["purchase", "items", 0], d) == "Apple"
        assert get_in(["purchase", "items", 1], d) == "Orange"

    def test_missing_key_returns_none(self):
        d = {"x": 1}
        assert get_in(["y"], d) is None

    def test_missing_key_returns_custom_default(self):
        d = {"x": 1}
        assert get_in(["y"], d, default=0) == 0
        assert get_in(["y"], d, default="fallback") == "fallback"

    def test_missing_nested_key(self):
        transaction = {
            "name": "Alice",
            "purchase": {"items": ["Apple", "Orange"], "costs": [0.50, 1.25]},
        }
        assert get_in(["purchase", "total"], transaction) is None
        assert get_in(["purchase", "total"], transaction, 0) == 0

    def test_missing_index(self):
        d = {"items": ["Apple"]}
        assert get_in(["items", 10], d) is None
        assert get_in(["items", 10], d, default="out") == "out"

    def test_no_default_raises_keyerror(self):
        with pytest.raises(KeyError):
            get_in(["y"], {}, no_default=True)

    def test_no_default_raises_indexerror(self):
        with pytest.raises(IndexError):
            get_in(["items", 10], {"items": ["Apple"]}, no_default=True)

    def test_no_default_raises_typeerror(self):
        with pytest.raises(TypeError):
            get_in(["x", "y"], {"x": 42}, no_default=True)

    def test_empty_keys_returns_coll(self):
        d = {"a": 1}
        assert get_in([], d) == {"a": 1}

    def test_tuple_keys(self):
        d = {("a", "b"): 1}
        assert get_in([("a", "b")], d) == 1


class TestDissoc:
    def test_remove_single_key(self):
        d = {"x": 1, "y": 2}
        assert dissoc(d, "y") == {"x": 1}

    def test_remove_multiple_keys(self):
        d = {"x": 1, "y": 2, "z": 3}
        assert dissoc(d, "y", "z") == {"x": 1}

    def test_remove_all_keys(self):
        d = {"x": 1, "y": 2}
        assert dissoc(d, "x", "y") == {}

    def test_remove_missing_key(self):
        d = {"x": 1}
        assert dissoc(d, "y") == {"x": 1}

    def test_original_unchanged(self):
        d = {"x": 1, "y": 2}
        result = dissoc(d, "y")
        assert d == {"x": 1, "y": 2}
        assert result is not d

    def test_with_ordereddict_factory(self):
        d = OrderedDict([("x", 1), ("y", 2), ("z", 3)])
        result = dissoc(d, "y", factory=OrderedDict)
        assert isinstance(result, OrderedDict)
        assert list(result.keys()) == ["x", "z"]
        assert result == {"x": 1, "z": 3}

    def test_many_keys_uses_remaining_path(self):
        d = {"a": 1, "b": 2, "c": 3}
        assert dissoc(d, "a", "b", "c") == {}

    def test_few_keys_uses_delete_path(self):
        d = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
        assert dissoc(d, "a") == {"b": 2, "c": 3, "d": 4, "e": 5}

    def test_unexpected_kwargs_raises(self):
        d = {"x": 1}
        with pytest.raises(TypeError, match="unexpected keyword argument"):
            dissoc(d, "x", bad_kwarg=True)
