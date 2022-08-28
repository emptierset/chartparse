import pytest
import re
import unittest.mock

from chartparse.event import Event
from chartparse.exceptions import RegexNotMatchError
from chartparse.globalevents import (
    GlobalEventsTrack,
    GlobalEvent,
    TextEvent,
    SectionEvent,
    LyricEvent,
)

from tests.helpers.globalevents import GlobalEventWithDefaults, GlobalEventsTrackWithDefaults


class TestGlobalEventsTrack(object):
    class TestInit(object):
        def test(self, default_global_events_track):
            assert default_global_events_track.text_events == pytest.defaults.text_events
            assert default_global_events_track.section_events == pytest.defaults.section_events
            assert default_global_events_track.lyric_events == pytest.defaults.lyric_events

        @pytest.mark.parametrize("resolution", [0, -1])
        def test_non_positive_resolution(self, resolution):
            with pytest.raises(ValueError):
                _ = GlobalEventsTrackWithDefaults(resolution=resolution)

    def test_from_chart_lines(self, mocker, minimal_string_iterator_getter, default_tatter):
        mock_parse_events = mocker.patch(
            "chartparse.track.parse_events_from_chart_lines",
            side_effect=[
                pytest.defaults.text_events,
                pytest.defaults.section_events,
                pytest.defaults.lyric_events,
            ],
        )
        spy_init = mocker.spy(GlobalEventsTrack, "__init__")
        _ = GlobalEventsTrack.from_chart_lines(minimal_string_iterator_getter, default_tatter)
        mock_parse_events.assert_has_calls(
            [
                unittest.mock.call(
                    minimal_string_iterator_getter(), TextEvent.from_chart_line, default_tatter
                ),
                unittest.mock.call(
                    minimal_string_iterator_getter(), SectionEvent.from_chart_line, default_tatter
                ),
                unittest.mock.call(
                    minimal_string_iterator_getter(), LyricEvent.from_chart_line, default_tatter
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
        def test(self, mocker):
            want_proximal_bpm_event_index = 1
            want_value = "value"
            spy_init = mocker.spy(Event, "__init__")

            got = GlobalEventWithDefaults(
                value=want_value, proximal_bpm_event_index=want_proximal_bpm_event_index
            )

            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                pytest.defaults.tick,
                pytest.defaults.timestamp,
                proximal_bpm_event_index=want_proximal_bpm_event_index,
            )
            assert got.value == want_value

    class TestFromChartLine(object):
        test_regex = r"^T (\d+?) V (.*?)$"

        @pytest.mark.parametrize(
            "prev_event",
            [
                pytest.param(None, id="prev_event_none"),
                pytest.param(
                    GlobalEventWithDefaults(proximal_bpm_event_index=1), id="prev_event_present"
                ),
            ],
        )
        def test(self, mocker, default_tatter, prev_event):
            spy_init = mocker.spy(GlobalEvent, "__init__")

            _ = GlobalEvent.from_chart_line(
                f"T {pytest.defaults.tick} V {pytest.defaults.global_event_value}",
                prev_event,
                default_tatter,
            )

            default_tatter.spy.assert_called_once_with(
                pytest.defaults.tick,
                proximal_bpm_event_index=prev_event._proximal_bpm_event_index if prev_event else 0,
            )

            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                pytest.defaults.tick,
                pytest.defaults.default_tatter_timestamp,
                pytest.defaults.global_event_value,
                proximal_bpm_event_index=pytest.defaults.default_tatter_index,
            )

        def test_no_match(self, invalid_chart_line, default_tatter):
            with pytest.raises(RegexNotMatchError):
                _ = GlobalEvent.from_chart_line(invalid_chart_line, None, default_tatter)

        def setup_method(self):
            GlobalEvent.ParsedData._regex = self.test_regex
            GlobalEvent.ParsedData._regex_prog = re.compile(GlobalEvent.ParsedData._regex)

        def teardown_method(self):
            del GlobalEvent.ParsedData._regex
            del GlobalEvent.ParsedData._regex_prog


# TODO: Test regex?
class TestTextEvent(object):
    pass


# TODO: Test regex?
class TestSectionEvent(object):
    pass


# TODO: Test regex?
class TestLyricEvent(object):
    pass
