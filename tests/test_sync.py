from __future__ import annotations

import typing as typ
import unittest.mock
from collections.abc import Sequence
from datetime import timedelta

import pytest

from chartparse.exceptions import RegexNotMatchError
from chartparse.sync import AnchorEvent, BPMEvent, BPMEvents, SyncTrack, TimeSignatureEvent
from chartparse.tick import Tick, Ticks
from tests.helpers import defaults, testcase, unsafe
from tests.helpers.lines import (
    generate_anchor_line,
    generate_bpm_line,
    generate_time_signature_line,
)
from tests.helpers.sync import (
    AnchorEventParsedDataWithDefaults,
    BPMEventParsedDataWithDefaults,
    BPMEventsWithDefaults,
    BPMEventsWithMock,
    BPMEventWithDefaults,
    SyncTrackWithDefaults,
    TimeSignatureEventParsedDataWithDefaults,
    TimeSignatureEventWithDefaults,
)


class TestSyncTrack(object):
    class TestPostInit(object):
        def test_empty_time_signature_events(self) -> None:
            with pytest.raises(ValueError):
                _ = SyncTrackWithDefaults(time_signature_events=[])

        def test_missing_first_time_signature_event(self) -> None:
            with pytest.raises(ValueError):
                _ = SyncTrackWithDefaults(
                    time_signature_events=[
                        TimeSignatureEventWithDefaults(
                            tick=1,
                            timestamp=timedelta(seconds=1),
                        )
                    ],
                )

    class TestFromChartLines(object):
        def test(self, mocker: typ.Any, invalid_chart_line: str) -> None:
            mock_parse_data = mocker.patch.object(
                SyncTrack,
                "_parse_data_from_chart_lines",
                return_value=(
                    [defaults.time_signature_event_parsed_data],
                    [defaults.bpm_event_parsed_data],
                    [defaults.anchor_event_parsed_data],
                ),
            )
            mock_build_events = mocker.patch(
                "chartparse.track.build_events_from_data",
                side_effect=[
                    [defaults.bpm_event],
                    [defaults.time_signature_event],
                    [defaults.anchor_event],
                ],
            )
            spy_init = mocker.spy(SyncTrack, "__init__")
            _ = SyncTrack.from_chart_lines(defaults.resolution, [invalid_chart_line])

            mock_parse_data.assert_called_once_with([invalid_chart_line])
            mock_build_events.assert_has_calls(
                [
                    unittest.mock.call(
                        BPMEvent,
                        [defaults.bpm_event_parsed_data],
                        defaults.resolution,
                    ),
                    unittest.mock.call(
                        TimeSignatureEvent,
                        [defaults.time_signature_event_parsed_data],
                        unittest.mock.ANY,  # ignore object conjured locally
                    ),
                    unittest.mock.call(
                        AnchorEvent,
                        [defaults.anchor_event_parsed_data],
                    ),
                ]
            )
            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                time_signature_events=[defaults.time_signature_event],
                bpm_events=[defaults.bpm_event],
                anchor_events=[defaults.anchor_event],
            )


class TestTimeSignatureEvent(object):
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
                    prev_event=TimeSignatureEventWithDefaults(_proximal_bpm_event_index=1),
                ),
            ],
        )
        @testcase.parametrize(
            ["data", "want_lower"],
            [
                testcase.new(
                    "line_without_lower_specified",
                    data=TimeSignatureEventParsedDataWithDefaults(),
                    want_lower=TimeSignatureEvent._default_lower_numeral,
                ),
                testcase.new(
                    "line_with_lower_specified",
                    data=TimeSignatureEventParsedDataWithDefaults(
                        lower=int(defaults.raw_lower_time_signature_numeral)
                    ),
                    want_lower=defaults.lower_time_signature_numeral,
                ),
            ],
        )
        def test(
            self,
            mocker: typ.Any,
            minimal_bpm_events_with_mock: BPMEventsWithMock,
            prev_event: TimeSignatureEvent | None,
            data: TimeSignatureEvent.ParsedData,
            want_lower: int,
        ) -> None:
            spy_init = mocker.spy(TimeSignatureEvent, "__init__")

            _ = TimeSignatureEvent.from_parsed_data(
                data, prev_event, typ.cast(BPMEvents, minimal_bpm_events_with_mock)
            )

            minimal_bpm_events_with_mock.timestamp_at_tick_mock.assert_called_once_with(
                defaults.tick,
                start_iteration_index=prev_event._proximal_bpm_event_index if prev_event else 0,
            )
            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                tick=defaults.tick,
                timestamp=minimal_bpm_events_with_mock.timestamp,
                upper_numeral=defaults.upper_time_signature_numeral,
                lower_numeral=want_lower,
                _proximal_bpm_event_index=minimal_bpm_events_with_mock.proximal_bpm_event_index,
            )

    class TestStr(object):
        def test(self) -> None:
            e = TimeSignatureEventWithDefaults()
            str(e)

    class TestParsedData(object):
        class TestFromChartLine(object):
            @testcase.parametrize(
                ["line", "want_lower"],
                [
                    testcase.new(
                        "line_without_lower_specified",
                        line=generate_time_signature_line(
                            defaults.tick,
                            defaults.upper_time_signature_numeral,
                        ),
                        want_lower=None,
                    ),
                    testcase.new(
                        "line_with_lower_specified",
                        line=generate_time_signature_line(
                            defaults.tick,
                            defaults.upper_time_signature_numeral,
                            lower=int(defaults.raw_lower_time_signature_numeral),
                        ),
                        want_lower=int(defaults.raw_lower_time_signature_numeral),
                    ),
                ],
            )
            def test(self, mocker: typ.Any, line: str, want_lower: int) -> None:
                got = TimeSignatureEvent.ParsedData.from_chart_line(line)
                assert got.tick == defaults.tick
                assert got.upper == defaults.upper_time_signature_numeral
                assert got.lower == want_lower

            def test_no_match(self, invalid_chart_line: str) -> None:
                with pytest.raises(RegexNotMatchError):
                    _ = TimeSignatureEvent.ParsedData.from_chart_line(invalid_chart_line)


class TestBPMEvent(object):
    class TestPostInit(object):
        def test_more_than_three_decimal_places_error(self) -> None:
            with pytest.raises(ValueError):
                _ = BPMEventWithDefaults(bpm=120.0001)

    class TestFromParsedData(object):
        def test_prev_event_none(self, mocker: typ.Any) -> None:
            spy_init = mocker.spy(BPMEvent, "__init__")

            _ = BPMEvent.from_parsed_data(
                BPMEventParsedDataWithDefaults(tick=0), None, defaults.resolution
            )

            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                tick=0,
                timestamp=timedelta(0),
                bpm=defaults.bpm,
                _proximal_bpm_event_index=0,
            )

        def test_prev_event_present(self, mocker: typ.Any) -> None:
            data = BPMEventParsedDataWithDefaults(tick=3)

            prev_event = BPMEventWithDefaults(tick=1, timestamp=timedelta(seconds=1))

            spy_init = mocker.spy(BPMEvent, "__init__")

            # NOTE: this value is clearly not the result of truthful arithmetic; a unique value was
            # chosen to ensure the right values are passed to the right places.
            seconds_since_prev = 4
            mock_seconds_from_ticks_at_bpm = mocker.patch(
                "chartparse.tick.seconds_from_ticks_at_bpm", return_value=seconds_since_prev
            )

            _ = BPMEvent.from_parsed_data(data, prev_event, defaults.resolution)

            mock_seconds_from_ticks_at_bpm.assert_called_once_with(
                data.tick - prev_event.tick,
                defaults.bpm,
                defaults.resolution,
            )

            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                tick=data.tick,
                timestamp=prev_event.timestamp + timedelta(seconds=seconds_since_prev),
                bpm=defaults.bpm,
                _proximal_bpm_event_index=1,
            )

        @testcase.parametrize(
            ["prev_event", "data"],
            [
                testcase.new(
                    "prev_event_after_current",
                    prev_event=BPMEventWithDefaults(tick=1),
                    data=BPMEventParsedDataWithDefaults(tick=0),
                ),
                testcase.new(
                    "prev_event_equal_to_current",
                    prev_event=BPMEventWithDefaults(tick=0),
                    data=BPMEventParsedDataWithDefaults(tick=0),
                ),
            ],
        )
        def test_wrongly_ordered_events(
            self, mocker: typ.Any, prev_event: BPMEvent | None, data: BPMEvent.ParsedData
        ) -> None:
            with pytest.raises(ValueError):
                _ = BPMEvent.from_parsed_data(data, prev_event, defaults.resolution)

    class TestStr(object):
        def test(self) -> None:
            e = BPMEventWithDefaults()
            str(e)

    class TestParsedData(object):
        class TestFromChartLine(object):
            def test(self) -> None:
                line = generate_bpm_line(defaults.tick, defaults.bpm)
                got = BPMEvent.ParsedData.from_chart_line(line)
                assert got.tick == defaults.tick
                assert got.raw_bpm == defaults.raw_bpm

            def test_no_match(self, invalid_chart_line: str) -> None:
                with pytest.raises(RegexNotMatchError):
                    _ = BPMEvent.ParsedData.from_chart_line(invalid_chart_line)


class TestBPMEvents(object):
    class TestPostInit(object):
        def test_non_positive_resolution(self) -> None:
            with pytest.raises(ValueError):
                _ = BPMEventsWithDefaults(resolution=0)
            with pytest.raises(ValueError):
                _ = BPMEventsWithDefaults(resolution=-1)

        def test_empty_bpm_events(self) -> None:
            with pytest.raises(ValueError):
                _ = BPMEventsWithDefaults(events=[])

        def test_missing_first_bpm_event(self) -> None:
            with pytest.raises(ValueError):
                _ = BPMEventsWithDefaults(
                    events=[
                        BPMEventWithDefaults(
                            tick=1,
                            timestamp=timedelta(seconds=1),
                        )
                    ]
                )

    class TestLen(object):
        def test(self) -> None:
            events = BPMEventsWithDefaults(events=[BPMEventWithDefaults(), BPMEventWithDefaults()])
            got = len(events)
            assert got == 2

    class TestGetItem(object):
        def test(self) -> None:
            want = BPMEventWithDefaults(tick=5)
            events = BPMEventsWithDefaults(events=[BPMEventWithDefaults(tick=0), want])
            got = events[1]
            assert got == want

    class TestTimestampAtTick(object):
        @testcase.parametrize(
            ["tick", "want_timestamp", "want_proximal_bpm_event_index"],
            [
                testcase.new_anonymous(
                    tick=100,
                    want_timestamp=timedelta(seconds=1),
                    want_proximal_bpm_event_index=1,
                ),
                testcase.new_anonymous(
                    tick=120,
                    want_timestamp=timedelta(seconds=1.1),
                    want_proximal_bpm_event_index=1,
                ),
                testcase.new_anonymous(
                    tick=400,
                    want_timestamp=timedelta(seconds=2.5),
                    want_proximal_bpm_event_index=2,
                ),
                testcase.new_anonymous(
                    tick=1000,
                    want_timestamp=timedelta(seconds=5.166666),
                    want_proximal_bpm_event_index=3,
                ),
            ],
        )
        def test(
            self, tick: int, want_timestamp: timedelta, want_proximal_bpm_event_index: int
        ) -> None:
            resolution = Ticks(100)
            event0 = BPMEvent.from_parsed_data(
                BPMEvent.ParsedData(tick=Tick(0), raw_bpm="60000"), None, resolution
            )
            event1 = BPMEvent.from_parsed_data(
                BPMEvent.ParsedData(tick=Tick(100), raw_bpm="120000"), event0, resolution
            )
            event2 = BPMEvent.from_parsed_data(
                BPMEvent.ParsedData(tick=Tick(400), raw_bpm="180000"), event1, resolution
            )
            event3 = BPMEvent.from_parsed_data(
                BPMEvent.ParsedData(tick=Tick(800), raw_bpm="90000"), event2, resolution
            )
            test_bpm_events = BPMEvents(
                events=[event0, event1, event2, event3], resolution=resolution
            )

            got_timestamp, got_proximal_bpm_event_index = test_bpm_events.timestamp_at_tick(
                Tick(tick)
            )
            assert got_timestamp == want_timestamp
            assert got_proximal_bpm_event_index == want_proximal_bpm_event_index

    class TestTimestampAtTickNoOptimizeReturn(object):
        def test(self, mocker: typ.Any, minimal_bpm_events_with_mock: BPMEventsWithMock) -> None:
            tick = Tick(451)
            _ = minimal_bpm_events_with_mock.timestamp_at_tick_no_optimize_return(tick)
            minimal_bpm_events_with_mock.timestamp_at_tick_mock.assert_called_once_with(tick)

    class TestIndexOfProximalEvent(object):
        @testcase.parametrize(
            ["bpm_event_list", "tick", "want"],
            [
                testcase.new(
                    "tick_coincides_with_first_event",
                    bpm_event_list=[
                        BPMEventWithDefaults(tick=Tick(0)),
                        BPMEventWithDefaults(tick=Tick(100)),
                    ],
                    tick=0,
                    want=0,
                ),
                testcase.new(
                    "tick_between_first_and_second_events",
                    bpm_event_list=[
                        BPMEventWithDefaults(tick=Tick(0)),
                        BPMEventWithDefaults(tick=Tick(100)),
                    ],
                    tick=50,
                    want=0,
                ),
                testcase.new(
                    "tick_between_second_and_third_events",
                    bpm_event_list=[
                        BPMEventWithDefaults(tick=Tick(0)),
                        BPMEventWithDefaults(tick=Tick(100)),
                        BPMEventWithDefaults(tick=Tick(200)),
                    ],
                    tick=150,
                    want=1,
                ),
                testcase.new(
                    "tick_after_last_event",
                    bpm_event_list=[
                        BPMEventWithDefaults(tick=Tick(0)),
                        BPMEventWithDefaults(tick=Tick(1)),
                    ],
                    tick=2,
                    want=1,
                ),
            ],
        )
        def test(
            self,
            minimal_bpm_events: BPMEvents,
            bpm_event_list: Sequence[BPMEvent],
            tick: int,
            want: int,
        ) -> None:
            unsafe.setattr(minimal_bpm_events, "events", bpm_event_list)
            unsafe.setattr(minimal_bpm_events, "resolution", defaults.resolution)
            got = minimal_bpm_events._index_of_proximal_event(Tick(tick))
            assert got == want

        @testcase.parametrize(
            ["bpm_event_list", "tick", "start_iteration_index"],
            [
                testcase.new(
                    "no_events",
                    bpm_event_list=[],
                    tick=0,
                    start_iteration_index=0,
                ),
                testcase.new(
                    "proximal_event_index_after_last_event",
                    bpm_event_list=[BPMEventWithDefaults()],
                    tick=0,
                    start_iteration_index=1,
                ),
                testcase.new(
                    "input_tick_before_tick_at_proximal_event_index",
                    bpm_event_list=[
                        BPMEventWithDefaults(
                            tick=0,
                        ),
                        BPMEventWithDefaults(
                            tick=100,
                        ),
                    ],
                    tick=50,
                    start_iteration_index=1,
                ),
            ],
        )
        def test_raises(
            self,
            minimal_bpm_events: BPMEvents,
            tick: int,
            start_iteration_index: int,
            bpm_event_list: Sequence[BPMEvent],
        ) -> None:
            unsafe.setattr(minimal_bpm_events, "events", bpm_event_list)
            unsafe.setattr(minimal_bpm_events, "resolution", defaults.resolution)
            with pytest.raises(ValueError):
                _ = minimal_bpm_events._index_of_proximal_event(
                    defaults.tick,
                    start_iteration_index=start_iteration_index,
                )


class TestAnchorEvent(object):
    class TestFromParsedData(object):
        def test(self, mocker: typ.Any) -> None:
            spy_init = mocker.spy(AnchorEvent, "__init__")

            data = AnchorEventParsedDataWithDefaults()
            _ = AnchorEvent.from_parsed_data(data)

            spy_init.assert_called_once_with(
                unittest.mock.ANY,
                tick=defaults.tick,
                timestamp=defaults.timestamp,  # ignore self
            )

    class TestParsedData(object):
        class TestFromChartLine(object):
            def test(self) -> None:
                line = generate_anchor_line(defaults.tick, defaults.microseconds)
                got = AnchorEvent.ParsedData.from_chart_line(line)
                assert got.tick == defaults.tick
                assert got.microseconds == defaults.microseconds

            def test_no_match(self, invalid_chart_line: str) -> None:
                with pytest.raises(RegexNotMatchError):
                    _ = AnchorEvent.ParsedData.from_chart_line(invalid_chart_line)
