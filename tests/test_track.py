from __future__ import annotations

import dataclasses

import chartparse.track
from chartparse.event import Event
from chartparse.sync import AnchorEvent, BPMEvent
from chartparse.tick import Tick
from chartparse.track import build_events_from_data, parse_data_from_chart_lines
from tests.helpers import defaults, testcase
from tests.helpers.fruit import Fruit
from tests.helpers.log import LogChecker
from tests.helpers.sync import BPMEventsWithDefaults

# TODO: typecheck the tests in this file by adding "-> None" annotations to each test function.


class TestBuildEventsFromData(object):
    @testcase.parametrize(
        ["data", "from_data_return_value", "want"],
        [
            testcase.new(
                "with_timestamp_getter",
                data=defaults.time_signature_event_parsed_data,
                from_data_return_value=defaults.time_signature_event,
                want=[defaults.time_signature_event],
            ),
            testcase.new(
                "with_None",
                data=defaults.anchor_event_parsed_data,
                from_data_return_value=defaults.anchor_event,
                want=[defaults.anchor_event],
            ),
            testcase.new(
                "with_resolution",
                data=defaults.bpm_event_parsed_data,
                from_data_return_value=defaults.bpm_event,
                want=BPMEventsWithDefaults(),
            ),
        ],
    )
    def test(
        self,
        mocker,
        invalid_chart_line,
        minimal_bpm_events_with_mock,
        data,
        from_data_return_value,
        want,
    ):
        from_data_fn_mock = mocker.Mock(return_value=from_data_return_value)
        if isinstance(from_data_return_value, BPMEvent):
            resolution_or_bpm_events_or_None = defaults.resolution
        elif isinstance(from_data_return_value, AnchorEvent):
            resolution_or_bpm_events_or_None = None
        else:
            resolution_or_bpm_events_or_None = minimal_bpm_events_with_mock

        got = build_events_from_data([data], from_data_fn_mock, resolution_or_bpm_events_or_None)

        assert got == want
        if isinstance(from_data_return_value, AnchorEvent):
            from_data_fn_mock.assert_called_once_with(data)
        else:
            from_data_fn_mock.assert_called_once_with(data, None, resolution_or_bpm_events_or_None)


class TestParseDataFromChartLines(object):
    @dataclasses.dataclass(kw_only=True, frozen=True)
    class ParsedData(Event.ParsedData):
        fruit: Fruit

        @classmethod
        def from_chart_line(cls, line):
            return cls(tick=int(line), fruit=Fruit(int(line)))

    @testcase.parametrize(
        ["types", "lines", "want"],
        [
            testcase.new(
                "two_typical_events",
                types=(ParsedData,),
                lines=["0", "1"],
                want={
                    ParsedData: [
                        ParsedData(tick=Tick(0), fruit=Fruit(0)),
                        ParsedData(tick=Tick(1), fruit=Fruit(1)),
                    ]
                },
            ),
        ],
    )
    def test(self, types, lines, want):
        got = parse_data_from_chart_lines(types, lines)
        assert got == want

    def test_no_suitable_parsers(self, mocker, caplog, invalid_chart_line):
        _ = parse_data_from_chart_lines(tuple(), [invalid_chart_line])
        logchecker = LogChecker(caplog)
        logchecker.assert_contains_string_in_one_line(
            chartparse.track._unparsable_line_msg_tmpl.format(invalid_chart_line, [])
        )
