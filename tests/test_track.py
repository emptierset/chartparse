from __future__ import annotations

import dataclasses
import typing as typ

import chartparse.track
from chartparse.event import Event
from chartparse.sync import BPMEvent
from chartparse.tick import Tick, Ticks
from chartparse.track import build_events_from_data, parse_data_from_chart_lines
from tests.helpers import defaults, testcase
from tests.helpers.fruit import Fruit
from tests.helpers.log import LogChecker
from tests.helpers.sync import BPMEventsWithDefaults


class TestBuildEventsFromData(object):
    def with_bpm_events_getter(
        self,
        mocker,
        invalid_chart_line,
        minimal_bpm_events_with_mock,
    ) -> None:
        from_data_fn_mock = mocker.Mock(return_value=defaults.time_signature_event)

        want = [defaults.time_signature_event]
        got = build_events_from_data(
            [defaults.time_signature_event_parsed_data],
            from_data_fn_mock,
            minimal_bpm_events_with_mock,
        )

        assert got == want
        from_data_fn_mock.assert_called_once_with(
            defaults.time_signature_event_parsed_data, None, minimal_bpm_events_with_mock
        )

    def test_with_none(
        self,
        mocker,
        invalid_chart_line,
        minimal_bpm_events_with_mock,
    ) -> None:
        from_data_fn_mock = mocker.Mock(return_value=defaults.anchor_event)

        want = [defaults.anchor_event]
        got = build_events_from_data([defaults.anchor_event_parsed_data], from_data_fn_mock)

        assert got == want
        from_data_fn_mock.assert_called_once_with(defaults.anchor_event_parsed_data)

    def test_with_resolution(
        self,
        mocker,
        invalid_chart_line,
        minimal_bpm_events_with_mock,
    ) -> None:
        from_data_fn_mock = mocker.Mock(return_value=defaults.bpm_event)

        want = BPMEventsWithDefaults()
        got = build_events_from_data(
            [defaults.bpm_event_parsed_data],
            typ.cast(
                typ.Callable[[BPMEvent.ParsedData, typ.Optional[BPMEvent], Ticks], BPMEvent],
                from_data_fn_mock,
            ),
            typ.cast(Ticks, defaults.resolution),
        )

        assert got == want
        from_data_fn_mock.assert_called_once_with(
            defaults.bpm_event_parsed_data, None, defaults.resolution
        )


class TestParseDataFromChartLines(object):
    @dataclasses.dataclass(kw_only=True, frozen=True)
    class ParsedData(Event.ParsedData):
        fruit: Fruit

        @classmethod
        def from_chart_line(cls, line):
            return cls(tick=int(line), fruit=Fruit(int(line)))

    @testcase.parametrize(
        ["types", "lines", "want_dict"],
        [
            testcase.new(
                "two_typical_events",
                types=(ParsedData,),
                lines=["0", "1"],
                want_dict={
                    ParsedData: [
                        ParsedData(tick=Tick(0), fruit=Fruit(0)),
                        ParsedData(tick=Tick(1), fruit=Fruit(1)),
                    ]
                },
            ),
        ],
    )
    def test(self, types, lines, want_dict) -> None:
        got = parse_data_from_chart_lines(types, lines)
        assert got._dict == want_dict

    def test_no_suitable_parsers(self, mocker, caplog, invalid_chart_line) -> None:
        _ = parse_data_from_chart_lines(tuple(), [invalid_chart_line])
        logchecker = LogChecker(caplog)
        logchecker.assert_contains_string_in_one_line(
            chartparse.track._unparsable_line_msg_tmpl.format(invalid_chart_line, [])
        )
