import pytest

from chartparse.eventstrack import Events
from chartparse.exceptions import RegexFatalNotMatchError


class TestEvents(object):
    def test_init(self, basic_events_track):
        assert basic_events_track.events == pytest.default_events_event_list
