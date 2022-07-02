from chartparse.util import DictPropertiesEqMixin


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

    def test_eq(self):
        foo1 = self.Foo(1, 2)
        foo2 = self.Foo(1, 2)
        foo3 = self.Foo(1, 3)
        baz = self.Baz(1, 2)
        assert foo1 == foo2
        assert foo2 == foo1
        assert foo1 != foo3
        assert foo3 != foo1
        assert foo1 == baz
        assert baz == foo1

    def test_eq_unimplemented(self):
        foo = self.Foo(1, 2)
        bar = self.Bar(1, 2)
        assert foo != bar
        assert bar != foo
