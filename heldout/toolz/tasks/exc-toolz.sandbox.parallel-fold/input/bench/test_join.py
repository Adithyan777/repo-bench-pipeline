from toolz.curried import *  # noqa: F403

try:
    xrange  # noqa: B018, F405
except NameError:
    xrange = range


def burn(seq):
    for item in seq:  # noqa: B007
        pass


small = [(i, str(i)) for i in range(100)] * 10
big = pipe([110] * 10000, map(range), concat, list)  # noqa: F405


def test_many_to_many_large():
    burn(join(get(0), small, identity, big))  # noqa: F405


def test_one_to_one_tiny():
    A = list(range(20))
    B = A[::2] + A[1::2][::-1]

    for i in xrange(50000):  # noqa: B007
        burn(join(identity, A, identity, B))  # noqa: F405


def test_one_to_many():
    A = list(range(20))
    B = pipe([20] * 1000, map(range), concat, list)  # noqa: F405

    for i in xrange(100):  # noqa: B007
        burn(join(identity, A, identity, B))  # noqa: F405
