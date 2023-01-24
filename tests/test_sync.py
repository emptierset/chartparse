from __future__ import annotations

import datetime
import pytest
import unittest.mock

from chartparse.event import Event
from chartparse.exceptions import RegexNotMatchError
from chartparse.sync import SyncTrack, BPMEvent, BPMEvents, TimeSignatureEvent, AnchorEvent

from tests.helpers import defaults
from tests.helpers import unsafe
from tests.helpers.lines import generate_bpm as generate_bpm_line
from tests.helpers.lines import generate_time_signature as generate_time_signature_line
from tests.helpers.lines import generate_anchor_event as generate_anchor_line
from tests.helpers.sync import (
    TimeSignatureEventWithDefaults,
    TimeSignatureEventParsedDataWithDefaults,
    BPMEventWithDefaults,
    BPMEventsWithDefaults,
    BPMEventParsedDataWithDefaults,
    SyncTrackWithDefaults,
    AnchorEventWithDefaults,
    AnchorEventParsedDataWithDefaults,
)


class TestSyncTrack(object):
    # TODO: Remove testinits for dataclasses.
    class TestPostInit(object):
        def test_empty_time_signature_events(self):
            with pytest.raises(ValueError):
                _ = SyncTrackWithDefaults(time_signature_events=[])

        def test_missing_first_time_signature_event(self):
            with pytest.raises(ValueError):
                _ = SyncTrackWithDefaults(
                    time_signature_events=[
                        TimeSignatureEventWithDefaults(
                            tick=1,
                            timestamp=datetime.timedelta(seconds=1),
                        )
                    ],
                )

    class TestFromChartLines(object):
        def test(self, mocker, invalid_chart_line):
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
                        [defaults.bpm_event_parsed_data],
                        BPMEvent.from_parsed_data,
                        defaults.resolution,
                    ),
                    unittest.mock.call(
                        [defaults.time_signature_event_parsed_data],
                        TimeSignatureEvent.from_parsed_data,
                        unittest.mock.ANY,  # ignore object conjured locally
                    ),
                    unittest.mock.call(
                        [defaults.anchor_event_parsed_data],
                        AnchorEvent.from_parsed_data,
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
        @pytest.mark.parametrize(
            "prev_event",
            [
                pytest.param(None, id="prev_event_none"),
                pytest.param(
                    TimeSignatureEventWithDefaults(proximal_bpm_event_index=1),
                    id="prev_event_present",
                ),
            ],
        )
        @pytest.mark.parametrize(
            "data,want_lower",
            [
                pytest.param(
                    TimeSignatureEventParsedDataWithDefaults(),
                    TimeSignatureEvent._default_lower_numeral,
                    id="line_without_lower_specified",
                ),
                pytest.param(
                    TimeSignatureEventParsedDataWithDefaults(
                        lower=int(defaults.raw_lower_time_signature_numeral)
                    ),
                    defaults.lower_time_signature_numeral,
                    id="line_with_lower_specified",
                ),
            ],
        )
        def test(self, mocker, minimal_bpm_events_with_mock, prev_event, data, want_lower):
            spy_init = mocker.spy(TimeSignatureEvent, "__init__")

            _ = TimeSignatureEvent.from_parsed_data(data, prev_event, minimal_bpm_events_with_mock)

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

    class TestParsedData(object):
        class TestFromChartLine(object):
            @pytest.mark.parametrize(
                "line,want_lower",
                [
                    pytest.param(
                        generate_time_signature_line(
                            defaults.tick,
                            defaults.upper_time_signature_numeral,
                        ),
                        None,
                        id="line_without_lower_specified",
                    ),
                    pytest.param(
                        generate_time_signature_line(
                            defaults.tick,
                            defaults.upper_time_signature_numeral,
                            lower=defaults.raw_lower_time_signature_numeral,
                        ),
                        int(defaults.raw_lower_time_signature_numeral),
                        id="line_with_lower_specified",
                    ),
                ],
            )
            def test(self, mocker, line, want_lower):
                got = TimeSignatureEvent.ParsedData.from_chart_line(line)
                assert got.tick == defaults.tick
                assert got.upper == defaults.upper_time_signature_numeral
                assert got.lower == want_lower

            def test_no_match(self, invalid_chart_line):
                with pytest.raises(RegexNotMatchError):
                    _ = TimeSignatureEvent.ParsedData.from_chart_line(invalid_chart_line)


class TestBPMEvent(object):
    class TestPostInit(object):
        def test_more_than_three_decimal_places_error(self):
            with pytest.raises(ValueError):
                _ = BPMEventWithDefaults(bpm=120.0001)

    class TestFromParsedData(object):
        def test_prev_event_none(self, mocker):
            spy_init = mocker.spy(BPMEvent, "__init__")

            _ = BPMEvent.from_parsed_data(
                BPMEventParsedDataWithDefaults(tick=0), None, defaults.resolution
            )

            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                tick=0,
                timestamp=datetime.timedelta(0),
                bpm=defaults.bpm,
                _proximal_bpm_event_index=0,
            )

        def test_prev_event_present(self, mocker):
            data = BPMEventParsedDataWithDefaults(tick=3)

            prev_event = BPMEventWithDefaults(tick=1, timestamp=datetime.timedelta(seconds=1))

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
                timestamp=prev_event.timestamp + datetime.timedelta(seconds=seconds_since_prev),
                bpm=defaults.bpm,
                _proximal_bpm_event_index=1,
            )

        @pytest.mark.parametrize(
            "prev_event,data",
            [
                pytest.param(
                    BPMEventWithDefaults(tick=1),
                    BPMEventParsedDataWithDefaults(tick=0),
                    id="prev_event_after_current",
                ),
                pytest.param(
                    BPMEventWithDefaults(tick=0),
                    BPMEventParsedDataWithDefaults(tick=0),
                    id="prev_event_equal_to_current",
                ),
            ],
        )
        def test_wrongly_ordered_events(self, mocker, prev_event, data):
            with pytest.raises(ValueError):
                _ = BPMEvent.from_parsed_data(data, prev_event, defaults.resolution)

    class TestParsedData(object):
        class TestFromChartLine(object):
            def test(self):
                line = generate_bpm_line(defaults.tick, defaults.bpm)
                got = BPMEvent.ParsedData.from_chart_line(line)
                assert got.tick == defaults.tick
                assert got.raw_bpm == defaults.raw_bpm

            def test_no_match(self, invalid_chart_line):
                with pytest.raises(RegexNotMatchError):
                    _ = BPMEvent.ParsedData.from_chart_line(invalid_chart_line)


class TestBPMEvents(object):
    class TestPostInit(object):
        def test_non_positive_resolution(self):
            with pytest.raises(ValueError):
                _ = BPMEventsWithDefaults(resolution=0)
            with pytest.raises(ValueError):
                _ = BPMEventsWithDefaults(resolution=-1)

        def test_empty_bpm_events(self):
            with pytest.raises(ValueError):
                _ = BPMEventsWithDefaults(events=[])

        def test_missing_first_bpm_event(self):
            with pytest.raises(ValueError):
                _ = BPMEventsWithDefaults(
                    events=[
                        BPMEventWithDefaults(
                            tick=1,
                            timestamp=datetime.timedelta(seconds=1),
                        )
                    ]
                )

    class TestLen(object):
        def test(self):
            events = BPMEventsWithDefaults(events=[BPMEventWithDefaults(), BPMEventWithDefaults()])
            got = len(events)
            assert got == 2

    class TestGetItem(object):
        def test(self):
            want = BPMEventWithDefaults(tick=5)
            events = BPMEventsWithDefaults(events=[BPMEventWithDefaults(tick=0), want])
            got = events[1]
            assert got == want

    class TestTimestampAtTick(object):
        @pytest.mark.parametrize(
            "tick,want_timestamp,want_proximal_bpm_event_index",
            [
                # TODO: Create helper that allows me to define pytest.param values by "name".
                pytest.param(100, datetime.timedelta(seconds=1), 1),
                pytest.param(120, datetime.timedelta(seconds=1.1), 1),
                pytest.param(400, datetime.timedelta(seconds=2.5), 2),
                pytest.param(1000, datetime.timedelta(seconds=5.166666), 3),
            ],
        )
        def test(self, tick, want_timestamp, want_proximal_bpm_event_index):
            resolution = 100
            event0 = BPMEvent.from_parsed_data(
                BPMEvent.ParsedData(tick=0, raw_bpm="60000"), None, resolution
            )
            event1 = BPMEvent.from_parsed_data(
                BPMEvent.ParsedData(tick=100, raw_bpm="120000"), event0, resolution
            )
            event2 = BPMEvent.from_parsed_data(
                BPMEvent.ParsedData(tick=400, raw_bpm="180000"), event1, resolution
            )
            event3 = BPMEvent.from_parsed_data(
                BPMEvent.ParsedData(tick=800, raw_bpm="90000"), event2, resolution
            )
            test_bpm_events = BPMEvents(
                events=[event0, event1, event2, event3], resolution=resolution
            )

            got_timestamp, got_proximal_bpm_event_index = test_bpm_events.timestamp_at_tick(tick)
            assert got_timestamp == want_timestamp
            assert got_proximal_bpm_event_index == want_proximal_bpm_event_index

    class TestIndexOfProximalEvent(object):
        @pytest.mark.parametrize(
            "bpm_event_list,tick,want",
            [
                pytest.param(
                    [
                        BPMEventWithDefaults(tick=0),
                        BPMEventWithDefaults(tick=100),
                    ],
                    0,
                    0,
                    id="tick_coincides_with_first_event",
                ),
                pytest.param(
                    [
                        BPMEventWithDefaults(tick=0),
                        BPMEventWithDefaults(tick=100),
                    ],
                    50,
                    0,
                    id="tick_between_first_and_second_events",
                ),
                pytest.param(
                    [
                        BPMEventWithDefaults(tick=0),
                        BPMEventWithDefaults(tick=100),
                        BPMEventWithDefaults(tick=200),
                    ],
                    150,
                    1,
                    id="tick_between_second_and_third_events",
                ),
                pytest.param(
                    [
                        BPMEventWithDefaults(tick=0),
                        BPMEventWithDefaults(tick=1),
                    ],
                    2,
                    1,
                    id="tick_after_last_event",
                ),
            ],
        )
        def test(self, bare_bpm_events, bpm_event_list, tick, want):
            unsafe.setattr(bare_bpm_events, "events", bpm_event_list)
            got = bare_bpm_events._index_of_proximal_event(tick)
            assert got == want

        @pytest.mark.parametrize(
            "bpm_event_list,tick,start_iteration_index",
            [
                pytest.param(
                    [],
                    0,
                    0,
                    id="no_events",
                ),
                pytest.param(
                    [BPMEventWithDefaults()],
                    0,
                    1,
                    id="proximal_event_index_after_last_event",
                ),
                pytest.param(
                    [
                        BPMEventWithDefaults(
                            tick=0,
                        ),
                        BPMEventWithDefaults(
                            tick=100,
                        ),
                    ],
                    50,
                    1,
                    id="input_tick_before_tick_at_proximal_event_index",
                ),
            ],
        )
        def test_raises(self, bare_bpm_events, tick, start_iteration_index, bpm_event_list):
            unsafe.setattr(bare_bpm_events, "events", bpm_event_list)
            with pytest.raises(ValueError):
                _ = bare_bpm_events._index_of_proximal_event(
                    defaults.tick,
                    start_iteration_index=start_iteration_index,
                )


class TestAnchorEvent(object):
    class TestInit(object):
        def test(self, mocker):
            spy_init = mocker.spy(Event, "__init__")

            _ = AnchorEventWithDefaults()

            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                tick=defaults.tick,
                timestamp=defaults.timestamp,
            )

    class TestFromParsedData(object):
        def test(self, mocker):
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
            def test(self):
                line = generate_anchor_line(defaults.tick, defaults.microseconds)
                got = AnchorEvent.ParsedData.from_chart_line(line)
                assert got.tick == defaults.tick
                assert got.microseconds == defaults.microseconds

            def test_no_match(self, invalid_chart_line):
                with pytest.raises(RegexNotMatchError):
                    _ = AnchorEvent.ParsedData.from_chart_line(invalid_chart_line)
