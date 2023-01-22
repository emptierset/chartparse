from __future__ import annotations


from tests.helpers import defaults


class TestEvent(object):
    class TestInit(object):
        def test(self, all_events):
            assert all_events.tick == defaults.tick
            assert all_events.timestamp == defaults.timestamp
            assert all_events._proximal_bpm_event_index == defaults.proximal_bpm_event_index
