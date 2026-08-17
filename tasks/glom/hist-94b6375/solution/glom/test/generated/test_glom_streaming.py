import pytest

from glom import glom, Iter


def test_chunked_basic_exact_division():
    """Elements divide evenly into chunks."""
    target = range(6)
    spec = Iter().chunked(3)
    result = list(glom(target, spec))
    assert result == [[0, 1, 2], [3, 4, 5]]


def test_chunked_with_remainder_no_fill():
    """Final chunk is shorter when no fill is provided."""
    target = range(10)
    spec = Iter().chunked(3)
    result = list(glom(target, spec))
    assert result == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]


def test_chunked_with_fill():
    """Final chunk is padded when fill is provided."""
    target = range(10)
    spec = Iter().chunked(3, fill=None)
    result = list(glom(target, spec))
    assert result == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, None, None]]


def test_chunked_empty_iterable():
    """Empty iterable produces empty result."""
    target = []
    spec = Iter().chunked(3)
    result = list(glom(target, spec))
    assert result == []


def test_chunked_single_element():
    """Single element produces one chunk of length 1."""
    target = [42]
    spec = Iter().chunked(3)
    result = list(glom(target, spec))
    assert result == [[42]]


def test_chunked_size_larger_than_iterable():
    """When chunk size exceeds iterable length, one short chunk is returned."""
    target = range(4)
    spec = Iter().chunked(10)
    result = list(glom(target, spec))
    assert result == [[0, 1, 2, 3]]


def test_chunked_size_larger_with_fill():
    """When chunk size exceeds iterable length and fill is provided, pad to size."""
    target = range(4)
    spec = Iter().chunked(10, fill='x')
    result = list(glom(target, spec))
    assert result == [[0, 1, 2, 3, 'x', 'x', 'x', 'x', 'x', 'x']]


def test_chunked_size_one():
    """Chunk size of 1 produces single-element chunks."""
    target = range(4)
    spec = Iter().chunked(1)
    result = list(glom(target, spec))
    assert result == [[0], [1], [2], [3]]


def test_chunked_returns_iter_spec():
    """chunked() returns an Iter instance (a spec)."""
    spec = Iter().chunked(3)
    assert isinstance(spec, Iter)


def test_chunked_repr():
    """Repr shows the chained call."""
    spec = Iter().chunked(3)
    assert repr(spec) == 'Iter().chunked(3)'


def test_chunked_repr_with_fill():
    """Repr includes fill argument as keyword when provided."""
    spec = Iter().chunked(3, fill=None)
    assert repr(spec) == 'Iter().chunked(size=3, fill=None)'
