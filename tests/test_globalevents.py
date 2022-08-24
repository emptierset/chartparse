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

from tests.helpers.globalevents import GlobalEventWithDefaults


class TestGlobalEventsTrack(object):
    class TestInit(object):
        def test(self, default_global_events_track):
            assert default_global_events_track.text_events == pytest.defaults.text_events
            assert default_global_events_track.section_events == pytest.defaults.section_events
            assert default_global_events_track.lyric_events == pytest.defaults.lyric_events

        def test_non_positive_resolution(self):
            with pytest.raises(ValueError):
                # TODO: Add GlobalEventTrackWithDefaults (and other tracks)
                _ = GlobalEventsTrack(
                    0,
                    pytest.defaults.text_events,
                    pytest.defaults.section_events,
                    pytest.defaults.lyric_events,
                )
            with pytest.raises(ValueError):
                _ = GlobalEventsTrack(
                    -1,
                    pytest.defaults.text_events,
                    pytest.defaults.section_events,
                    pytest.defaults.lyric_events,
                )

    def test_from_chart_lines(self, mocker, minimal_string_iterator_getter, minimal_tatter):
        mock_parse_events = mocker.patch(
            "chartparse.track.parse_events_from_chart_lines",
            side_effect=[
                pytest.defaults.text_events,
                pytest.defaults.section_events,
                pytest.defaults.lyric_events,
            ],
        )
        spy_init = mocker.spy(GlobalEventsTrack, "__init__")
        _ = GlobalEventsTrack.from_chart_lines(minimal_string_iterator_getter, minimal_tatter)
        mock_parse_events.assert_has_calls(
            [
                unittest.mock.call(
                    minimal_string_iterator_getter(), TextEvent.from_chart_line, minimal_tatter
                ),
                unittest.mock.call(
                    minimal_string_iterator_getter(), SectionEvent.from_chart_line, minimal_tatter
                ),
                unittest.mock.call(
                    minimal_string_iterator_getter(), LyricEvent.from_chart_line, minimal_tatter
                ),
            ]
        )
        spy_init.assert_called_once_with(
            unittest.mock.ANY,  # ignore self
            pytest.defaults.resolution,
            pytest.defaults.text_events,
            pytest.defaults.section_events,
            pytest.defaults.lyric_events,
        )


class TestGlobalEvent(object):
    class TestInit(object):
        def test(self):
            got = GlobalEventWithDefaults()
            assert got.value == pytest.defaults.global_event_value

    class TestFromChartLine(object):
        test_regex = r"^T (\d+?) V (.*?)$"

        def setup_method(self):
            GlobalEvent._regex = self.test_regex
            GlobalEvent._regex_prog = re.compile(GlobalEvent._regex)

        def teardown_method(self):
            del GlobalEvent._regex
            del GlobalEvent._regex_prog

        def test(self, mocker, minimal_tatter):
            line = f"T {pytest.defaults.tick} V {pytest.defaults.global_event_value}"
            spy_calculate_timestamp = mocker.spy(GlobalEvent, "calculate_timestamp")
            got = GlobalEvent.from_chart_line(line, None, minimal_tatter)
            spy_calculate_timestamp.assert_called_once_with(
                pytest.defaults.tick, None, minimal_tatter
            )
            assert got.value == pytest.defaults.global_event_value

        def test_no_match(self, invalid_chart_line, minimal_tatter):
            with pytest.raises(RegexNotMatchError):
                _ = GlobalEvent.from_chart_line(invalid_chart_line, None, minimal_tatter)


# TODO: Test regex?
class TestTextEvent(object):
    pass


# TODO: Test regex?
class TestSectionEvent(object):
    pass


# TODO: Test regex?
class TestLyricEvent(object):
    pass
