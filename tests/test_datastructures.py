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
            assert ImmutableSortedList(default_sorted_list, already_sorted=True) == sorted(
                default_sorted_list
            )
