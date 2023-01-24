from __future__ import annotations

import dataclasses
import pytest

import chartparse.track
from chartparse.event import Event
from chartparse.track import build_events_from_data, parse_data_from_chart_lines
from chartparse.sync import BPMEvent, AnchorEvent

from tests.helpers import defaults
from tests.helpers.fruit import Fruit
from tests.helpers.log import LogChecker
from tests.helpers.sync import BPMEventsWithDefaults


class TestBuildEventsFromData(object):
    @pytest.mark.parametrize(
        "data,from_data_return_value,want",
        [
            pytest.param(
                defaults.time_signature_event_parsed_data,
                defaults.time_signature_event,
                [defaults.time_signature_event],
                id="with_timestamp_getter",
            ),
            pytest.param(
                defaults.anchor_event_parsed_data,
                defaults.anchor_event,
                [defaults.anchor_event],
                id="with_None",
            ),
            pytest.param(
                defaults.bpm_event_parsed_data,
                defaults.bpm_event,
                BPMEventsWithDefaults(),
                id="with_resolution",
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

    @pytest.mark.parametrize(
        "types,lines,want",
        [
            pytest.param(
                (ParsedData,),
                ["0", "1"],
                {
                    ParsedData: [
                        ParsedData(tick=0, fruit=Fruit(0)),
                        ParsedData(tick=1, fruit=Fruit(1)),
                    ]
                },
                id="two_typical_events",
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
