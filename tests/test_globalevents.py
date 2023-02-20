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
from chartparse.tick import Tick
from tests.helpers import defaults, testcase
from tests.helpers.globalevents import (
    GlobalEventParsedDataWithDefaults,
    GlobalEventWithDefaults,
    LyricEventParsedDataWithDefaults,
    SectionEventParsedDataWithDefaults,
    TextEventParsedDataWithDefaults,
)
from tests.helpers.lines import generate_lyric as generate_lyric_line
from tests.helpers.lines import generate_section as generate_section_line
from tests.helpers.lines import generate_text as generate_text_line
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


class TestTextEvent(object):
    class TestParsedData(object):
        class TestRegex(object):
            @testcase.parametrize(
                ["tick"],
                [
                    testcase.new_anonymous(tick=1),
                    testcase.new_anonymous(tick=11),
                    testcase.new_anonymous(tick=13435),
                ],
            )
            @testcase.parametrize(
                ["value"],
                [
                    testcase.new_anonymous(value="oneword"),
                    testcase.new_anonymous(value="one_word"),
                    testcase.new_anonymous(value="56numbers34"),
                    testcase.new_anonymous(value="$%%symbols*#&$"),
                ],
            )
            def test_match(self, tick: int, value: str) -> None:
                line = generate_text_line(Tick(tick), value)
                m = TextEvent.ParsedData._regex_prog.match(line)
                assert m is not None
                got_tick, got_value = m.groups()

                want_tick = str(tick)
                want_value = value

                assert got_tick == want_tick
                assert got_value == want_value

            @testcase.parametrize(
                ["tick", "value"],
                [
                    # TODO: Check documentation. Is this really supposed to not match?
                    testcase.new_anonymous(tick=1, value="two words"),
                ],
            )
            def test_no_match(self, tick: int, value: str) -> None:
                line = generate_text_line(Tick(tick), value)
                m = TextEvent.ParsedData._regex_prog.match(line)
                assert m is None


class TestSectionEvent(object):
    class TestParsedData(object):
        class TestRegex(object):
            @testcase.parametrize(
                ["tick"],
                [
                    testcase.new_anonymous(tick=1),
                    testcase.new_anonymous(tick=11),
                    testcase.new_anonymous(tick=13435),
                ],
            )
            @testcase.parametrize(
                ["value"],
                [
                    testcase.new_anonymous(value="oneword"),
                    testcase.new_anonymous(value="one_word"),
                    testcase.new_anonymous(value="56numbers34"),
                    testcase.new_anonymous(value="$%%symbols*#&$"),
                ],
            )
            # ^\s*?(\d+?) = E \"section (.*?)\"\s*?$
            # TODO: Validate this regexes. Can sections actually have spaces?
            def test_match(self, tick: int, value: str) -> None:
                line = generate_section_line(Tick(tick), value)
                m = SectionEvent.ParsedData._regex_prog.match(line)
                assert m is not None
                got_tick, got_value = m.groups()

                want_tick = str(tick)
                want_value = value

                assert got_tick == want_tick
                assert got_value == want_value


class TestLyricEvent(object):
    class TestParsedData(object):
        class TestRegex(object):
            @testcase.parametrize(
                ["tick"],
                [
                    testcase.new_anonymous(tick=1),
                    testcase.new_anonymous(tick=11),
                    testcase.new_anonymous(tick=13435),
                ],
            )
            @testcase.parametrize(
                ["value"],
                [
                    testcase.new_anonymous(value="oneword"),
                    testcase.new_anonymous(value="one_word"),
                    testcase.new_anonymous(value="56numbers34"),
                    testcase.new_anonymous(value="$%%symbols*#&$"),
                ],
            )
            # TODO: Validate this regexes. Can lyrics actually have spaces?
            # ^\s*?(\d+?) = E \"lyric (.*?)\"\s*?$
            def test_match(self, tick: int, value: str) -> None:
                line = generate_lyric_line(Tick(tick), value)
                m = LyricEvent.ParsedData._regex_prog.match(line)
                assert m is not None
                got_tick, got_value = m.groups()

                want_tick = str(tick)
                want_value = value

                assert got_tick == want_tick
                assert got_value == want_value
