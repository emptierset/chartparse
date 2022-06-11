import pytest

from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.globalevents import GlobalEvent


class TestGlobalEvent(object):
    def test_init(self, global_event):
        assert global_event.command == pytest.default_global_event_command
        assert global_event.params == pytest.default_global_event_params

    def test_from_chart_line(self, generate_valid_events_line):

        line = generate_valid_events_line(params=pytest.default_global_event_params)
        event = GlobalEvent.from_chart_line(line)
        assert event.tick == pytest.default_tick
        assert event.command == pytest.default_global_event_command
        assert event.params == pytest.default_global_event_params

    def test_from_chart_line_no_match(self):
        line = "asdf"
        with pytest.raises(RegexFatalNotMatchError):
            _ = GlobalEvent.from_chart_line(line)
