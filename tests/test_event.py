import pytest

from chartparse.event import Event


class TestEvent(object):
    def test_init(self, tick_having_event):
        assert tick_having_event.tick == pytest.default_tick

    def test_init_with_timestamp(self):
        e = Event(pytest.default_tick, pytest.default_timestamp)
        assert e.timestamp == pytest.default_timestamp
