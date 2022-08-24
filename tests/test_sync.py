import datetime
import pytest
import unittest.mock
from contextlib import nullcontext as does_not_raise

from chartparse.exceptions import RegexNotMatchError
from chartparse.sync import SyncTrack, BPMEvent, TimeSignatureEvent

from tests.helpers.datastructures import AlreadySortedImmutableSortedList
from tests.helpers.lines import generate_bpm as generate_bpm_line
from tests.helpers.lines import generate_time_signature as generate_time_signature_line
from tests.helpers.sync import (
    TimeSignatureEventWithDefaults,
    BPMEventWithDefaults,
    SyncTrackWithDefaults,
)


class TestSyncTrack(object):
    class TestInit(object):
        def test(self):
            got = SyncTrackWithDefaults()
            assert got.time_signature_events == pytest.defaults.time_signature_events
            assert got.bpm_events == pytest.defaults.bpm_events

        def test_non_positive_resolution(self):
            with pytest.raises(ValueError):
                _ = SyncTrackWithDefaults(resolution=0)
            with pytest.raises(ValueError):
                _ = SyncTrackWithDefaults(resolution=-1)

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

        def test_empty_bpm_events(self):
            with pytest.raises(ValueError):
                _ = SyncTrackWithDefaults(bpm_events=[])

        def test_missing_first_bpm_event(self):
            with pytest.raises(ValueError):
                _ = SyncTrackWithDefaults(
                    bpm_events=[
                        BPMEventWithDefaults(
                            tick=1,
                            timestamp=datetime.timedelta(seconds=1),
                        )
                    ],
                )

    class TestFromChartLines(object):
        def test(self, mocker, minimal_string_iterator_getter):
            mock_parse_events = mocker.patch(
                "chartparse.track.parse_events_from_chart_lines",
                side_effect=[
                    pytest.defaults.bpm_events,
                    pytest.defaults.time_signature_events,
                ],
            )
            spy_init = mocker.spy(SyncTrack, "__init__")
            _ = SyncTrack.from_chart_lines(
                pytest.defaults.resolution, minimal_string_iterator_getter
            )
            mock_parse_events.assert_has_calls(
                [
                    unittest.mock.call(
                        minimal_string_iterator_getter(),
                        BPMEvent.from_chart_line,
                        pytest.defaults.resolution,
                    ),
                    unittest.mock.call(
                        minimal_string_iterator_getter(),
                        TimeSignatureEvent.from_chart_line,
                        unittest.mock.ANY,  # ignore object conjured locally
                    ),
                ]
            )
            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                pytest.defaults.resolution,
                pytest.defaults.time_signature_events,
                pytest.defaults.bpm_events,
            )

    class TestTimestampAtTick(object):
        def test_wrapper(self, mocker, bare_sync_track):
            bare_sync_track.resolution = pytest.defaults.resolution
            bare_sync_track.bpm_events = pytest.defaults.bpm_events

            mock_impl = mocker.patch.object(bare_sync_track, "_timestamp_at_tick")

            _ = bare_sync_track.timestamp_at_tick(pytest.defaults.tick, start_bpm_event_index=0)
            mock_impl.assert_called_once_with(
                pytest.defaults.bpm_events,
                pytest.defaults.tick,
                pytest.defaults.resolution,
                start_bpm_event_index=0,
            )

        # TODO: Figure out where proximal_bpm_event_idxs and start_bpm_event_idxs need to be
        # asserted.
        @pytest.mark.parametrize(
            "tick,want_timestamp,want_proximal_bpm_event_idx",
            [
                # TODO: Create helper that allows me to define pytest.param values by "name".
                pytest.param(100, datetime.timedelta(seconds=1), 1),
                pytest.param(120, datetime.timedelta(seconds=1.1), 1),
                pytest.param(400, datetime.timedelta(seconds=2.5), 2),
                pytest.param(1000, datetime.timedelta(seconds=5.166666), 3),
            ],
        )
        def test_impl(self, tick, want_timestamp, want_proximal_bpm_event_idx):
            resolution = 100
            event0 = BPMEvent.from_chart_line(generate_bpm_line(0, 60.000), None, resolution)
            event1 = BPMEvent.from_chart_line(generate_bpm_line(100, 120.000), event0, resolution)
            event2 = BPMEvent.from_chart_line(generate_bpm_line(400, 180.000), event1, resolution)
            event3 = BPMEvent.from_chart_line(generate_bpm_line(800, 90.000), event2, resolution)
            test_bpm_events = AlreadySortedImmutableSortedList([event0, event1, event2, event3])

            got_timestamp, got_proximal_bpm_event_idx = SyncTrack._timestamp_at_tick(
                test_bpm_events, tick, resolution
            )
            assert got_timestamp == want_timestamp
            assert got_proximal_bpm_event_idx == want_proximal_bpm_event_idx

    class TestIdxOfProximalBPMEvent(object):
        @pytest.mark.parametrize(
            "bpm_events,tick,want",
            [
                pytest.param(
                    AlreadySortedImmutableSortedList(
                        [
                            BPMEventWithDefaults(tick=0),
                            BPMEventWithDefaults(tick=100),
                        ],
                    ),
                    0,
                    0,
                    id="tick_coincides_with_first_event",
                ),
                pytest.param(
                    AlreadySortedImmutableSortedList(
                        [
                            BPMEventWithDefaults(tick=0),
                            BPMEventWithDefaults(tick=100),
                        ],
                    ),
                    50,
                    0,
                    id="tick_between_first_and_second_events",
                ),
                pytest.param(
                    AlreadySortedImmutableSortedList(
                        [
                            BPMEventWithDefaults(tick=0),
                            BPMEventWithDefaults(tick=100),
                            BPMEventWithDefaults(tick=200),
                        ],
                    ),
                    150,
                    1,
                    id="tick_between_second_and_third_events",
                ),
                pytest.param(
                    AlreadySortedImmutableSortedList(
                        [
                            BPMEventWithDefaults(tick=0),
                            BPMEventWithDefaults(tick=1),
                        ],
                    ),
                    2,
                    1,
                    id="tick_after_last_event",
                ),
            ],
        )
        def test(self, bare_sync_track, bpm_events, tick, want):
            got = bare_sync_track._idx_of_proximal_bpm_event(bpm_events, tick)
            assert got == want

        @pytest.mark.parametrize(
            "bpm_events,tick,start_idx",
            [
                pytest.param(
                    AlreadySortedImmutableSortedList([]),
                    0,
                    0,
                    id="no_bpm_events",
                ),
                pytest.param(
                    AlreadySortedImmutableSortedList([BPMEventWithDefaults()]),
                    0,
                    1,
                    id="start_idx_after_last_bpm_event",
                ),
                pytest.param(
                    AlreadySortedImmutableSortedList(
                        [
                            BPMEventWithDefaults(
                                tick=0,
                            ),
                            BPMEventWithDefaults(
                                tick=100,
                            ),
                        ],
                    ),
                    50,
                    1,
                    id="input_tick_before_tick_at_start_idx",
                ),
            ],
        )
        def test_raises(self, bare_sync_track, tick, start_idx, bpm_events):
            with pytest.raises(ValueError):
                _ = bare_sync_track._idx_of_proximal_bpm_event(
                    bpm_events, pytest.defaults.tick, start_idx=start_idx
                )


class TestTimeSignatureEvent(object):
    class TestInit(object):
        def test(self):
            got = TimeSignatureEventWithDefaults()
            assert got.upper_numeral == pytest.defaults.upper_time_signature_numeral
            assert got.lower_numeral == pytest.defaults.lower_time_signature_numeral

    class TestFromChartLine(object):
        def test_shortform(self, mocker, minimal_tatter):
            spy_calculate_timestamp = mocker.spy(TimeSignatureEvent, "calculate_timestamp")
            line = generate_time_signature_line(
                pytest.defaults.tick, pytest.defaults.upper_time_signature_numeral
            )
            got = TimeSignatureEvent.from_chart_line(line, None, minimal_tatter)
            spy_calculate_timestamp.assert_called_once_with(
                pytest.defaults.tick, None, minimal_tatter
            )
            assert got.upper_numeral == pytest.defaults.upper_time_signature_numeral
            assert got.lower_numeral == TimeSignatureEvent._default_lower_numeral

        def test_longform(self, mocker, minimal_tatter):
            spy_calculate_timestamp = mocker.spy(TimeSignatureEvent, "calculate_timestamp")
            line = generate_time_signature_line(
                pytest.defaults.tick,
                pytest.defaults.upper_time_signature_numeral,
                pytest.defaults.lower_time_signature_numeral,
            )
            got = TimeSignatureEvent.from_chart_line(line, None, minimal_tatter)
            spy_calculate_timestamp.assert_called_once_with(
                pytest.defaults.tick, None, minimal_tatter
            )
            assert got.upper_numeral == pytest.defaults.upper_time_signature_numeral
            assert got.lower_numeral == pytest.defaults.lower_time_signature_numeral

        def test_no_match(self, invalid_chart_line, minimal_tatter):
            with pytest.raises(RegexNotMatchError):
                _ = TimeSignatureEvent.from_chart_line(invalid_chart_line, None, minimal_tatter)


class TestBPMEvent(object):
    class TestInit(object):
        def test(self, default_bpm_event):
            assert default_bpm_event.bpm == pytest.defaults.bpm

        def test_more_than_three_decimal_places_error(self):
            with pytest.raises(ValueError):
                _ = BPMEventWithDefaults(bpm=120.0001)

    class TestFromChartLine(object):
        @pytest.mark.parametrize(
            "prev_event_tick,current_event_tick,expectation",
            [
                pytest.param(
                    None,
                    pytest.defaults.tick,
                    does_not_raise(),
                    id="None prev event",
                ),
                pytest.param(
                    pytest.defaults.tick,
                    pytest.defaults.tick + 1,
                    does_not_raise(),
                    id="Present prev event",
                ),
                pytest.param(
                    pytest.defaults.tick + 1,
                    pytest.defaults.tick,
                    pytest.raises(ValueError),
                    id="Prev event after current",
                ),
                pytest.param(
                    pytest.defaults.tick,
                    pytest.defaults.tick,
                    pytest.raises(ValueError),
                    id="Prev event equal to current",
                ),
            ],
        )
        def test(self, mocker, prev_event_tick, current_event_tick, expectation):
            prev_event = (
                BPMEventWithDefaults(tick=prev_event_tick) if prev_event_tick is not None else None
            )

            current_line = generate_bpm_line(current_event_tick, pytest.defaults.bpm)
            spy_calculate_timestamp = mocker.spy(BPMEvent, "calculate_timestamp")
            with expectation:
                got = BPMEvent.from_chart_line(
                    current_line, prev_event, pytest.defaults.resolution
                )
                assert got.bpm == pytest.defaults.bpm
            spy_calculate_timestamp.assert_called_once_with(
                current_event_tick,
                prev_event,
                unittest.mock.ANY,  # ignore locally conjured object
            )

        def test_no_match(self):
            with pytest.raises(RegexNotMatchError):
                _ = BPMEvent.from_chart_line(
                    pytest.invalid_chart_line, None, pytest.defaults.resolution
                )
