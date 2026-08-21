from toolz import memoize


def test_memoize_kwargs():
    @memoize
    def f(x, y=3):
        return x

    for i in range(100000):  # noqa: B007
        f(3)
