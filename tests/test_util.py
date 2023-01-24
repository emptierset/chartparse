from __future__ import annotations

from chartparse.util import (
    AllValuesGettableEnum,
    DictPropertiesEqMixin,
    DictReprMixin,
    DictReprTruncatedSequencesMixin,
)
from tests.helpers import testcase


class TestDictPropertiesEqMixin(object):
    class Foo(DictPropertiesEqMixin):
        def __init__(self, x, y):
            self.x = x
            self.y = y

    class Bar(object):
        def __init__(self, x, y):
            self.x = x
            self.y = y

    class Baz(DictPropertiesEqMixin):
        def __init__(self, x, y):
            self.x = x
            self.y = y

    class TestEq(object):
        def test(self):
            foo1 = TestDictPropertiesEqMixin.Foo(1, 2)
            foo2 = TestDictPropertiesEqMixin.Foo(1, 2)
            foo3 = TestDictPropertiesEqMixin.Foo(1, 3)
            baz = TestDictPropertiesEqMixin.Baz(1, 2)
            assert foo1 == foo2
            assert foo2 == foo1
            assert foo1 != foo3
            assert foo3 != foo1
            assert foo1 == baz
            assert baz == foo1

        def test_unimplemented(self):
            foo = TestDictPropertiesEqMixin.Foo(1, 2)
            bar = TestDictPropertiesEqMixin.Bar(1, 2)
            assert foo != bar
            assert bar != foo


class TestAllValuesGettableEnum(object):
    class TrinketEnum(AllValuesGettableEnum):
        ONE = 1
        TWO = 2
        TOO = 2

    class TrinketEnumWithAlias(AllValuesGettableEnum):
        ONE = 1
        TWO = 2
        TOO = 2

    class TestAllValues(object):
        def test(self):
            assert TestAllValuesGettableEnum.TrinketEnum.all_values() == [1, 2]

        def test_does_not_get_aliases(self):
            assert TestAllValuesGettableEnum.TrinketEnumWithAlias.all_values() == [1, 2]


class TestDictReprMixin(object):
    class TrinketClass(DictReprMixin):
        def __init__(self, x):
            self.x = x

    class TestRepr(object):
        # This just exercises the path; asserting the output is irksome and unnecessary.
        def test(self):
            f = TestDictReprMixin.TrinketClass(1)
            str(f)


class TestDictReprTruncatedSequencesMixin(object):
    class TrinketClass(DictReprTruncatedSequencesMixin):
        def __init__(self, x):
            self.x = x

    @testcase.parametrize(
        ["x"],
        [
            testcase.new(
                "non-sequence",
                x=1,
            ),
            testcase.new(
                "sequence",
                x=[3, 1],
            ),
        ],
    )
    class TestRepr(object):
        # This just exercises the path; asserting the output is irksome and unnecessary.
        def test(self, x):
            f = TestDictReprTruncatedSequencesMixin.TrinketClass(x)
            str(f)
