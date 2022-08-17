import pytest

from chartparse.datastructures import ImmutableList, ImmutableSortedList


_default_list = [3, 2, 1]
_default_sorted_list = [1, 2, 3]
_default_tuple_list = [(1, 3), (2, 2), (3, 1)]


@pytest.fixture
def basic_sorted_list():
    return _default_sorted_list


@pytest.fixture
def basic_list():
    return _default_list


@pytest.fixture
def alternate_basic_list():
    return _default_list


@pytest.fixture
def basic_tuple_list():
    return _default_tuple_list


@pytest.fixture
def basic_immutable_list(basic_list):
    return ImmutableList(basic_list)


@pytest.fixture
def alternate_basic_immutable_list(alternate_basic_list):
    return ImmutableList(alternate_basic_list)


@pytest.fixture
def basic_immutable_sorted_list(basic_list):
    return ImmutableSortedList(basic_list)


class TestImmutableList(object):
    def test_init(self, basic_immutable_list, basic_list):
        assert basic_immutable_list._seq == basic_list

        from_iterable = ImmutableList(iter(basic_list))
        assert from_iterable == basic_list

    def test_getitem(self, basic_immutable_list, basic_list):
        assert basic_immutable_list[0] == basic_list[0]

    def test_iter_len(self, basic_immutable_list, basic_list):
        assert len(basic_immutable_list) == len(basic_list)
        for a, b in zip(basic_immutable_list, basic_list):
            assert a == b

    def test_eq(self, basic_immutable_list, basic_list, alternate_basic_immutable_list):
        # Mismatched types
        assert basic_immutable_list == basic_list
        assert basic_list == basic_immutable_list

        # Both immutable
        assert basic_immutable_list == alternate_basic_immutable_list
        assert alternate_basic_immutable_list == basic_immutable_list

        assert basic_immutable_list != 1
        assert 1 != basic_immutable_list

    def test_contains(self, basic_immutable_list, basic_list):
        for x in basic_list:
            assert x in basic_immutable_list

    def test_reversed(self, basic_immutable_list, basic_list):
        assert list(reversed(basic_immutable_list)) == list(reversed(basic_list))


class TestImmutableSortedList(object):
    class TestInit(object):
        def test_basic(self, basic_list):
            assert ImmutableSortedList(basic_list) == sorted(basic_list)

        def test_with_key(self, basic_tuple_list):
            key = lambda x: x[1]
            assert ImmutableSortedList(basic_tuple_list, key=key) == sorted(
                basic_tuple_list, key=key
            )

        def test_already_sorted(self, basic_sorted_list):
            assert ImmutableSortedList(basic_sorted_list, already_sorted=True) == sorted(
                basic_sorted_list
            )
