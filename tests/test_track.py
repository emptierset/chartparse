from __future__ import annotations

import dataclasses
import typing as typ
from collections.abc import Sequence

import pytest

import chartparse.track
from chartparse.event import Event
from chartparse.sync import AnchorEvent, BPMEvent, BPMEvents, TimeSignatureEvent
from chartparse.tick import Tick
from chartparse.track import build_events_from_data, parse_data_from_chart_lines
from tests.helpers import defaults, testcase
from tests.helpers.fruit import Fruit
from tests.helpers.log import LogChecker
from tests.helpers.sync import BPMEventsWithDefaults, BPMEventsWithMock


class TestBuildEventsFromData(object):
    def with_bpm_events_getter(
        self,
        mocker: typ.Any,
        invalid_chart_line: str,
        minimal_bpm_events_with_mock: BPMEventsWithMock,
    ) -> None:
        mocker.patch.object(
            TimeSignatureEvent, "from_parsed_data", return_value=defaults.time_signature_event
        )

        want = [defaults.time_signature_event]
        got = build_events_from_data(
            TimeSignatureEvent,
            [defaults.time_signature_event_parsed_data],
            typ.cast(BPMEvents, minimal_bpm_events_with_mock),
        )

        assert got == want
        TimeSignatureEvent.from_parsed_data.assert_called_once_with(  # type: ignore[attr-defined]
            defaults.time_signature_event_parsed_data, None, minimal_bpm_events_with_mock
        )

    def test_with_none(
        self,
        mocker: typ.Any,
        invalid_chart_line: str,
    ) -> None:
        mocker.patch.object(AnchorEvent, "from_parsed_data", return_value=defaults.anchor_event)

        want = [defaults.anchor_event]
        got = build_events_from_data(AnchorEvent, [defaults.anchor_event_parsed_data])

        assert got == want
        AnchorEvent.from_parsed_data.assert_called_once_with(  # type: ignore[attr-defined]
            defaults.anchor_event_parsed_data
        )

    def test_with_resolution(
        self,
        mocker: typ.Any,
        invalid_chart_line: str,
    ) -> None:
        mocker.patch.object(BPMEvent, "from_parsed_data", return_value=defaults.bpm_event)

        want = BPMEventsWithDefaults()
        got = build_events_from_data(
            BPMEvent,
            [defaults.bpm_event_parsed_data],
            defaults.resolution,
        )

        assert got == want
        BPMEvent.from_parsed_data.assert_called_once_with(  # type: ignore[attr-defined]
            defaults.bpm_event_parsed_data, None, defaults.resolution
        )


class TestParseDataFromChartLines(object):
    @dataclasses.dataclass(kw_only=True, frozen=True)
    class ParsedData(Event.ParsedData):
        _Self = typ.TypeVar("_Self", bound="TestParseDataFromChartLines.ParsedData")

        fruit: Fruit

        @classmethod
        def from_chart_line(cls: type[_Self], line: str) -> _Self:
            return cls(tick=Tick(int(line)), fruit=Fruit(int(line)))

    _ParsedDataT = typ.TypeVar("_ParsedDataT", bound=Event.ParsedData)

    @testcase.parametrize(
        ["types", "lines", "want_dict"],
        [
            testcase.new(
                "two_consecutive_events",
                types=(ParsedData,),
                lines=["0", "1"],
                want_dict={
                    ParsedData: [
                        ParsedData(tick=Tick(0), fruit=Fruit(0)),
                        ParsedData(tick=Tick(1), fruit=Fruit(1)),
                    ]
                },
            ),
            # TODO(P1): Add test case with multiple `types`.
        ],
    )
    def test(
        self,
        types: Sequence[type[_ParsedDataT]],
        lines: Sequence[str],
        want_dict: dict[type[_ParsedDataT], Sequence[_ParsedDataT]],
    ) -> None:
        got = parse_data_from_chart_lines(types, lines)
        assert got._dict == want_dict

    def test_no_suitable_parsers(
        self, mocker: typ.Any, caplog: pytest.LogCaptureFixture, invalid_chart_line: str
    ) -> None:
        _ = parse_data_from_chart_lines(tuple(), [invalid_chart_line])
        logchecker = LogChecker(caplog)
        logchecker.assert_contains_string_in_one_line(
            chartparse.track._unparsable_line_msg_tmpl.format(invalid_chart_line, [])
        )
