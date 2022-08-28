import pytest


class TestEvent(object):
    class TestInit(object):
        def test(self, tick_having_event):
            assert tick_having_event.tick == pytest.defaults.tick
