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

from tests.helpers.globalevents import (
    GlobalEventWithDefaults,
    GlobalEventsTrackWithDefaults,
    GlobalEventParsedDataWithDefaults,
    TextEventParsedDataWithDefaults,
    SectionEventParsedDataWithDefaults,
    LyricEventParsedDataWithDefaults,
)


class TestGlobalEventsTrack(object):
    class TestInit(object):
        def test(self, default_global_events_track):
            # TODO: Construct GlobalEventsTrack manually.
            assert default_global_events_track.text_events == pytest.defaults.text_events
            assert default_global_events_track.section_events == pytest.defaults.section_events
            assert default_global_events_track.lyric_events == pytest.defaults.lyric_events

        @pytest.mark.parametrize("resolution", [0, -1])
        def test_non_positive_resolution(self, resolution):
            with pytest.raises(ValueError):
                _ = GlobalEventsTrackWithDefaults(resolution=resolution)

    def test_from_chart_lines(self, mocker, default_tatter):
        mock_parse_data = mocker.patch.object(
            GlobalEventsTrack,
            "_parse_data_from_chart_lines",
            return_value=(
                pytest.defaults.text_event_parsed_datas,
                pytest.defaults.section_event_parsed_datas,
                pytest.defaults.lyric_event_parsed_datas,
            ),
        )
        mock_parse_events = mocker.patch(
            "chartparse.track.parse_events_from_data",
            side_effect=[
                pytest.defaults.text_events,
                pytest.defaults.section_events,
                pytest.defaults.lyric_events,
            ],
        )
        spy_init = mocker.spy(GlobalEventsTrack, "__init__")

        _ = GlobalEventsTrack.from_chart_lines(pytest.invalid_chart_lines, default_tatter)

        mock_parse_data.assert_called_once_with(pytest.invalid_chart_lines)
        mock_parse_events.assert_has_calls(
            [
                unittest.mock.call(
                    [TextEventParsedDataWithDefaults()], TextEvent.from_parsed_data, default_tatter
                ),
                unittest.mock.call(
                    [SectionEventParsedDataWithDefaults()],
                    SectionEvent.from_parsed_data,
                    default_tatter,
                ),
                unittest.mock.call(
                    [LyricEventParsedDataWithDefaults()],
                    LyricEvent.from_parsed_data,
                    default_tatter,
                ),
            ],
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

    class TestFromParsedData(object):
        @pytest.mark.parametrize(
            "prev_event",
            [
                pytest.param(
                    None,
                    id="prev_event_none",
                ),
                pytest.param(
                    GlobalEventWithDefaults(proximal_bpm_event_index=1),
                    id="prev_event_present",
                ),
            ],
        )
        def test(self, mocker, default_tatter, prev_event):
            spy_init = mocker.spy(GlobalEvent, "__init__")

            _ = GlobalEvent.from_parsed_data(
                GlobalEventParsedDataWithDefaults(),
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

    class TestParsedData(object):
        class TestFromChartLine(object):
            test_regex = r"^T (\d+?) V (.*?)$"

            def test(self, mocker):
                got = GlobalEvent.ParsedData.from_chart_line(
                    f"T {pytest.defaults.tick} V {pytest.defaults.global_event_value}"
                )
                assert got.tick == pytest.defaults.tick
                assert got.value == pytest.defaults.global_event_value

            def test_no_match(self, invalid_chart_line):
                with pytest.raises(RegexNotMatchError):
                    _ = GlobalEvent.ParsedData.from_chart_line(invalid_chart_line)

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
