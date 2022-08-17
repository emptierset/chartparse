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

    def test_from_chart_lines(
        self, mocker, minimal_string_iterator_getter, minimal_timestamp_getter
    ):
        mock_parse_events = mocker.patch(
            "chartparse.track.parse_events_from_chart_lines",
            side_effect=[
                pytest.default_text_event_list,
                pytest.default_section_event_list,
                pytest.default_lyric_event_list,
            ],
        )
        spy_init = mocker.spy(GlobalEventsTrack, "__init__")
        _ = GlobalEventsTrack.from_chart_lines(
            minimal_string_iterator_getter,
            minimal_timestamp_getter,
            pytest.default_resolution,
        )
        mock_parse_events.assert_has_calls(
            [
                unittest.mock.call(
                    pytest.default_resolution,
                    minimal_string_iterator_getter(),
                    TextEvent.from_chart_line,
                    minimal_timestamp_getter,
                ),
                unittest.mock.call(
                    pytest.default_resolution,
                    minimal_string_iterator_getter(),
                    SectionEvent.from_chart_line,
                    minimal_timestamp_getter,
                ),
                unittest.mock.call(
                    pytest.default_resolution,
                    minimal_string_iterator_getter(),
                    LyricEvent.from_chart_line,
                    minimal_timestamp_getter,
                ),
            ]
        )
        spy_init.assert_called_once_with(
            unittest.mock.ANY,
            pytest.default_text_event_list,
            pytest.default_section_event_list,
            pytest.default_lyric_event_list,
        )


class TestGlobalEvent(object):
    class TestInit(object):
        def test_basic(self):
            event = GlobalEvent(
                pytest.default_tick, pytest.default_global_event_value, pytest.default_timestamp
            )
            assert event.value == pytest.default_global_event_value

    class TestFromChartLine(object):
        test_regex = r"^T (\d+?) V (.*?)$"

        def setup_method(self):
            GlobalEvent._regex = self.test_regex
            GlobalEvent._regex_prog = re.compile(GlobalEvent._regex)

        def teardown_method(self):
            del GlobalEvent._regex
            del GlobalEvent._regex_prog

        def test_basic(self, mocker, minimal_timestamp_getter):
            line = f"T {pytest.default_tick} V {pytest.default_global_event_value}"
            spy_calculate_timestamp = mocker.spy(GlobalEvent, "calculate_timestamp")
            e = GlobalEvent.from_chart_line(
                line,
                None,
                minimal_timestamp_getter,
                pytest.default_resolution,
            )
            spy_calculate_timestamp.assert_called_once_with(
                pytest.default_tick, None, minimal_timestamp_getter, pytest.default_resolution
            )
            assert e.value == pytest.default_global_event_value

        def test_no_match(self, invalid_chart_line, minimal_timestamp_getter):
            with pytest.raises(RegexNotMatchError):
                _ = GlobalEvent.from_chart_line(
                    invalid_chart_line,
                    None,
                    minimal_timestamp_getter,
                    pytest.default_resolution,
                )


# TODO: Test regex?
class TestTextEvent(object):
    pass


# TODO: Test regex?
class TestSectionEvent(object):
    pass


# TODO: Test regex?
class TestLyricEvent(object):
    pass
