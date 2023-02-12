from __future__ import annotations

import re
import typing as typ
import unittest.mock

import pytest

from chartparse.exceptions import RegexNotMatchError
from chartparse.globalevents import (
    GlobalEvent,
    GlobalEventsTrack,
    LyricEvent,
    SectionEvent,
    TextEvent,
)
from chartparse.sync import BPMEvents
from tests.helpers import defaults, testcase
from tests.helpers.globalevents import (
    GlobalEventParsedDataWithDefaults,
    GlobalEventWithDefaults,
    LyricEventParsedDataWithDefaults,
    SectionEventParsedDataWithDefaults,
    TextEventParsedDataWithDefaults,
)
from tests.helpers.sync import BPMEventsWithMock


class TestGlobalEventsTrack(object):
    class TestFromChartLines(object):
        def test(
            self, mocker: typ.Any, minimal_bpm_events: BPMEvents, invalid_chart_line: str
        ) -> None:
            mock_parse_data = mocker.patch.object(
                GlobalEventsTrack,
                "_parse_data_from_chart_lines",
                return_value=(
                    [defaults.text_event_parsed_data],
                    [defaults.section_event_parsed_data],
                    [defaults.lyric_event_parsed_data],
                ),
            )
            mock_build_events = mocker.patch(
                "chartparse.track.build_events_from_data",
                side_effect=[
                    [defaults.text_event],
                    [defaults.section_event],
                    [defaults.lyric_event],
                ],
            )
            spy_init = mocker.spy(GlobalEventsTrack, "__init__")

            _ = GlobalEventsTrack.from_chart_lines([invalid_chart_line], minimal_bpm_events)

            mock_parse_data.assert_called_once_with([invalid_chart_line])
            mock_build_events.assert_has_calls(
                [
                    unittest.mock.call(
                        TextEvent,
                        [TextEventParsedDataWithDefaults()],
                        minimal_bpm_events,
                    ),
                    unittest.mock.call(
                        SectionEvent,
                        [SectionEventParsedDataWithDefaults()],
                        minimal_bpm_events,
                    ),
                    unittest.mock.call(
                        LyricEvent,
                        [LyricEventParsedDataWithDefaults()],
                        minimal_bpm_events,
                    ),
                ],
            )
            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                text_events=[defaults.text_event],
                section_events=[defaults.section_event],
                lyric_events=[defaults.lyric_event],
            )


class TestGlobalEvent(object):
    class TestFromParsedData(object):
        @testcase.parametrize(
            ["prev_event"],
            [
                testcase.new(
                    "prev_event_none",
                    prev_event=None,
                ),
                testcase.new(
                    "prev_event_present",
                    prev_event=GlobalEventWithDefaults(_proximal_bpm_event_index=1),
                ),
            ],
        )
        def test(
            self,
            mocker: typ.Any,
            minimal_bpm_events_with_mock: BPMEventsWithMock,
            prev_event: GlobalEvent | None,
        ) -> None:
            spy_init = mocker.spy(GlobalEvent, "__init__")

            _ = GlobalEvent.from_parsed_data(
                GlobalEventParsedDataWithDefaults(),
                prev_event,
                typ.cast(BPMEvents, minimal_bpm_events_with_mock),
            )

            minimal_bpm_events_with_mock.timestamp_at_tick_mock.assert_called_once_with(
                defaults.tick,
                start_iteration_index=prev_event._proximal_bpm_event_index if prev_event else 0,
            )

            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                tick=defaults.tick,
                timestamp=minimal_bpm_events_with_mock.timestamp,
                value=defaults.global_event_value,
                _proximal_bpm_event_index=minimal_bpm_events_with_mock.proximal_bpm_event_index,
            )

    class TestStr(object):
        # This just exercises the path; asserting the output is irksome and unnecessary.
        def test(self) -> None:
            e = GlobalEventWithDefaults()
            str(e)

    class TestParsedData(object):
        class TestFromChartLine(object):
            test_regex = r"^T (\d+?) V (.*?)$"

            def test(self, mocker: typ.Any) -> None:
                got = GlobalEvent.ParsedData.from_chart_line(
                    f"T {defaults.tick} V {defaults.global_event_value}"
                )
                assert got.tick == defaults.tick
                assert got.value == defaults.global_event_value

            def test_no_match(self, invalid_chart_line: str) -> None:
                with pytest.raises(RegexNotMatchError):
                    _ = GlobalEvent.ParsedData.from_chart_line(invalid_chart_line)

            def setup_method(self) -> None:
                GlobalEvent.ParsedData._regex = self.test_regex
                GlobalEvent.ParsedData._regex_prog = re.compile(GlobalEvent.ParsedData._regex)

            def teardown_method(self) -> None:
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
