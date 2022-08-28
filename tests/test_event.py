import pytest


class TestEvent(object):
    class TestInit(object):
        def test(self, all_events):
            assert all_events.tick == pytest.defaults.tick
            assert all_events.timestamp == pytest.defaults.timestamp
            assert all_events._proximal_bpm_event_index == pytest.defaults.proximal_bpm_event_index
