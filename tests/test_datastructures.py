from __future__ import annotations

import pytest

from chartparse.datastructures import ImmutableList, ImmutableSortedList


_default_list = [3, 2, 1]
_default_sorted_list = [1, 2, 3]
_default_tuple_list = [(1, 3), (2, 2), (3, 1)]


@pytest.fixture
def default_sorted_list():
    return _default_sorted_list


@pytest.fixture
def default_list():
    return _default_list


@pytest.fixture
def alternate_default_list():
    return _default_list


@pytest.fixture
def default_tuple_list():
    return _default_tuple_list


@pytest.fixture
def default_immutable_list(default_list):
    return ImmutableList(default_list)


@pytest.fixture
def alternate_default_immutable_list(alternate_default_list):
    return ImmutableList(alternate_default_list)


class TestImmutableList(object):
    def test_init(self, default_immutable_list, default_list):
        assert default_immutable_list._seq == default_list

        from_iterable = ImmutableList(iter(default_list))
        assert from_iterable == default_list

    def test_getitem(self, default_immutable_list, default_list):
        assert default_immutable_list[0] == default_list[0]

    def test_iter_len(self, default_immutable_list, default_list):
        assert len(default_immutable_list) == len(default_list)
        for a, b in zip(default_immutable_list, default_list):
            assert a == b

    def test_eq(self, default_immutable_list, default_list, alternate_default_immutable_list):
        # Mismatched types
        assert default_immutable_list == default_list
        assert default_list == default_immutable_list

        # Both immutable
        assert default_immutable_list == alternate_default_immutable_list
        assert alternate_default_immutable_list == default_immutable_list

        # NotImplemented
        assert default_immutable_list != 1
        assert 1 != default_immutable_list

    def test_contains(self, default_immutable_list, default_list):
        for x in default_list:
            assert x in default_immutable_list

    def test_reversed(self, default_immutable_list, default_list):
        assert list(reversed(default_immutable_list)) == list(reversed(default_list))


class TestImmutableSortedList(object):
    class TestInit(object):
        def test(self, default_list):
            assert ImmutableSortedList(default_list) == sorted(default_list)

        def test_with_key(self, default_tuple_list):
            key = lambda x: x[1]
            assert ImmutableSortedList(default_tuple_list, key=key) == sorted(
                default_tuple_list, key=key
            )

        def test_already_sorted(self, default_sorted_list):
            got = ImmutableSortedList(default_sorted_list, already_sorted=True)
            assert got == sorted(default_sorted_list)

    class TestBinarySearch(object):
        xs = [0, 2, 4, 4, 9, 10]

        @pytest.mark.parametrize("x,want", [(0, 0), (2, 1), (4, 2), (9, 4), (10, 5)])
        def test_present(self, x, want):
            xsi = ImmutableSortedList(self.xs, already_sorted=True)
            got = xsi.binary_search(x)
            assert got == want

        @pytest.mark.parametrize("x", [-1, 1, 3, 5, 6, 7, 8, 11])
        def test_absent(self, x):
            xsi = ImmutableSortedList(self.xs, already_sorted=True)
            got = xsi.binary_search(x)
            assert got is None

    class TestFindLe(object):
        xs = [0, 2, 4, 4, 9, 10]

        @pytest.mark.parametrize(
            "x,want",
            [
                (0, 0),
                (1, 0),
                (2, 1),
                (3, 1),
                (4, 3),
                (5, 3),
                (6, 3),
                (7, 3),
                (8, 3),
                (9, 4),
                (10, 5),
                (11, 5),
            ],
        )
        def test(self, x, want):
            xsi = ImmutableSortedList(self.xs, already_sorted=True)
            got = xsi.find_le(x)
            assert got == want

        def test_does_not_exist(self):
            xsi = ImmutableSortedList(self.xs, already_sorted=True)
            with pytest.raises(ValueError):
                _ = xsi.find_le(-1)
