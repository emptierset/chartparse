import pytest

from chartparse.eventstrack import Events, EventsEvent
from chartparse.exceptions import RegexFatalNotMatchError


class TestEvents(object):
    def test_init(self, basic_events_track):
        assert basic_events_track.events == pytest.default_events_event_list


class TestEventsEvent(object):
    def test_init(self, events_event):
        assert events_event.command == pytest.default_events_event_command
        assert events_event.params == pytest.default_events_event_params

    def test_from_chart_line(self, generate_valid_events_line):

        line = generate_valid_events_line(params=pytest.default_events_event_params)
        event = EventsEvent.from_chart_line(line)
        assert event.tick == pytest.default_tick
        assert event.command == pytest.default_events_event_command
        assert event.params == pytest.default_events_event_params

    def test_from_chart_line_no_match(self):
        line = "asdf"
        with pytest.raises(RegexFatalNotMatchError):
            _ = EventsEvent.from_chart_line(line)
