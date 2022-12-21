from __future__ import annotations

import dataclasses
import pytest

import chartparse.track
from chartparse.event import Event
from chartparse.track import build_events_from_data, parse_data_from_chart_lines
from chartparse.sync import BPMEvent

from tests.helpers.fruit import Fruit
from tests.helpers.log import LogChecker


class TestBuildEventsFromData(object):
    @pytest.mark.parametrize(
        "from_data_return_value,want",
        [
            pytest.param(
                pytest.defaults.time_signature_event,
                [pytest.defaults.time_signature_event],
                id="with_timestamp_getter",
            ),
            pytest.param(
                pytest.defaults.bpm_event,
                [pytest.defaults.bpm_event],
                id="without_timestamp_getter",
            ),
        ],
    )
    def test(
        self,
        mocker,
        invalid_chart_line,
        default_tatter,
        from_data_return_value,
        want,
    ):
        from_data_fn_mock = mocker.Mock(return_value=from_data_return_value)
        if isinstance(from_data_return_value, BPMEvent):
            resolution_or_tatter = pytest.defaults.resolution
        else:
            resolution_or_tatter = default_tatter

        got = build_events_from_data(
            pytest.invalid_chart_lines, from_data_fn_mock, resolution_or_tatter
        )

        assert got == want
        from_data_fn_mock.assert_called_once_with(invalid_chart_line, None, resolution_or_tatter)


class TestParseDataFromChartLines(object):
    @dataclasses.dataclass
    class ParsedData(Event.ParsedData):
        fruit: Fruit

        @classmethod
        def from_chart_line(cls, line):
            return cls(tick=int(line), fruit=Fruit(int(line)))

    @dataclasses.dataclass
    class CoalescableParsedData(ParsedData, Event.CoalescableParsedData):
        def coalesce_from_other(self, other):
            self.fruit = Fruit(other.fruit.value + self.fruit.value)

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
            pytest.param(
                (CoalescableParsedData,),
                ["2", "2"],
                {
                    CoalescableParsedData: [
                        CoalescableParsedData(tick=2, fruit=Fruit(4)),
                    ]
                },
                id="two_coalesced_events",
            ),
        ],
    )
    def test(self, types, lines, want):
        got = parse_data_from_chart_lines(types, lines)
        assert got == want

    def test_simultaneous_uncoalescable_events(self):
        with pytest.raises(ValueError):
            _ = parse_data_from_chart_lines((self.ParsedData,), ["0", "0"])

    def test_no_suitable_parsers(self, mocker, caplog):
        _ = parse_data_from_chart_lines(tuple(), pytest.invalid_chart_lines)
        logchecker = LogChecker(caplog)
        logchecker.assert_contains_string_in_one_line(
            chartparse.track._unparsable_line_msg_tmpl.format(pytest.invalid_chart_line, [])
        )
