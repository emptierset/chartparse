import pytest
import re
import unittest.mock

from chartparse.exceptions import RegexNotMatchError
from chartparse.globalevents import (
    GlobalEventsTrack,
    GlobalEvent,
    TextEvent,
    SectionEvent,
    LyricEvent,
)


class TestGlobalEventsTrack(object):
    def test_init(self, basic_global_events_track):
        assert basic_global_events_track.text_events == pytest.default_text_event_list
        assert basic_global_events_track.section_events == pytest.default_section_event_list
        assert basic_global_events_track.lyric_events == pytest.default_lyric_event_list

    def test_from_chart_lines(self, mocker, placeholder_string_iterator_getter):
        mock_parse_events = mocker.patch(
            "chartparse.globalevents.GlobalEventsTrack._parse_events_from_chart_lines",
            side_effect=[
                pytest.default_text_event_list,
                pytest.default_section_event_list,
                pytest.default_lyric_event_list,
            ],
        )
        init_spy = mocker.spy(GlobalEventsTrack, "__init__")
        _ = GlobalEventsTrack.from_chart_lines(placeholder_string_iterator_getter)
        mock_parse_events.assert_has_calls(
            [
                unittest.mock.call(
                    placeholder_string_iterator_getter(), TextEvent.from_chart_line
                ),
                unittest.mock.call(
                    placeholder_string_iterator_getter(), SectionEvent.from_chart_line
                ),
                unittest.mock.call(
                    placeholder_string_iterator_getter(), LyricEvent.from_chart_line
                ),
            ]
        )
        init_spy.assert_called_once_with(
            unittest.mock.ANY,
            pytest.default_text_event_list,
            pytest.default_section_event_list,
            pytest.default_lyric_event_list,
        )


class TestGlobalEvent(object):
    test_regex = r"^T (\d+?) V (.*?)$"

    def teardown_method(self):
        try:
            del GlobalEvent._regex
            del GlobalEvent._regex_prog
        except AttributeError:
            pass

    def test_init(self):
        event = GlobalEvent(pytest.default_tick, pytest.default_global_event_value)
        assert event.value == pytest.default_global_event_value

    def test_from_chart_line(self, bare_global_event):
        GlobalEvent._regex = self.test_regex
        GlobalEvent._regex_prog = re.compile(GlobalEvent._regex)

        bare_global_event.tick = pytest.default_tick
        bare_global_event.timestamp = pytest.default_timestamp
        bare_global_event.value = pytest.default_global_event_value
        line = f"T {pytest.default_tick} V {pytest.default_global_event_value}"
        e = GlobalEvent.from_chart_line(line)
        assert e.value == pytest.default_global_event_value

    def test_from_chart_line_no_match(self, invalid_chart_line):
        GlobalEvent._regex = self.test_regex
        GlobalEvent._regex_prog = re.compile(GlobalEvent._regex)

        with pytest.raises(RegexNotMatchError):
            _ = GlobalEvent.from_chart_line(invalid_chart_line)


# TODO: Test regex?
class TestTextEvent(object):
    pass


# TODO: Test regex?
class TestSectionEvent(object):
    pass


# TODO: Test regex?
class TestLyricEvent(object):
    pass
