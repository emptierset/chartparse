import datetime
import pytest
import unittest.mock

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
        @pytest.mark.parametrize(
            "line,want_lower",
            [
                pytest.param(
                    generate_time_signature_line(
                        pytest.defaults.tick, pytest.defaults.upper_time_signature_numeral
                    ),
                    TimeSignatureEvent._default_lower_numeral,
                    id="line_without_lower_specified",
                ),
                pytest.param(
                    generate_time_signature_line(
                        pytest.defaults.tick,
                        pytest.defaults.upper_time_signature_numeral,
                        pytest.defaults.lower_time_signature_numeral,
                    ),
                    pytest.defaults.lower_time_signature_numeral,
                    id="line_with_lower_specified",
                ),
            ],
        )
        def test(self, mocker, minimal_tatter, line, want_lower):
            spy_init = mocker.spy(TimeSignatureEvent, "__init__")

            _ = TimeSignatureEvent.from_chart_line(line, None, minimal_tatter)

            minimal_tatter.spy.assert_called_once_with(
                pytest.defaults.tick, start_bpm_event_index=0
            )
            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                pytest.defaults.tick,
                pytest.defaults.timestamp,
                pytest.defaults.upper_time_signature_numeral,
                want_lower,
                proximal_bpm_event_idx=0,
            )

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
        def test_prev_event_none(self, mocker):
            spy_init = mocker.spy(BPMEvent, "__init__")

            current_line = generate_bpm_line(0, pytest.defaults.bpm)
            _ = BPMEvent.from_chart_line(current_line, None, pytest.defaults.resolution)

            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                0,
                datetime.timedelta(0),
                pytest.defaults.bpm,
                proximal_bpm_event_idx=0,
            )

        def test_prev_event_present(self, mocker):
            current_event_tick = 3
            current_line = generate_bpm_line(current_event_tick, pytest.defaults.bpm)

            prev_event = BPMEventWithDefaults(tick=1, timestamp=datetime.timedelta(seconds=1))

            spy_init = mocker.spy(BPMEvent, "__init__")

            # NOTE: this value is clearly not the result of truthful arithmetic; a unique value was
            # chosen to ensure the right values are passed to the right places.
            seconds_since_prev = 4
            mock_seconds_from_ticks_at_bpm = mocker.patch(
                "chartparse.tick.seconds_from_ticks_at_bpm", return_value=seconds_since_prev
            )

            _ = BPMEvent.from_chart_line(current_line, prev_event, pytest.defaults.resolution)

            mock_seconds_from_ticks_at_bpm.assert_called_once_with(
                current_event_tick - prev_event.tick,
                pytest.defaults.bpm,
                pytest.defaults.resolution,
            )

            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                current_event_tick,
                prev_event.timestamp + datetime.timedelta(seconds=seconds_since_prev),
                pytest.defaults.bpm,
                proximal_bpm_event_idx=None,
            )

        @pytest.mark.parametrize(
            "prev_event,current_event_tick",
            [
                pytest.param(BPMEventWithDefaults(tick=1), 0, id="prev_event_after_current"),
                pytest.param(BPMEventWithDefaults(tick=0), 0, id="prev_event_equal_to_current"),
            ],
        )
        def test_wrongly_ordered_events(self, mocker, prev_event, current_event_tick):
            current_line = generate_bpm_line(current_event_tick, pytest.defaults.bpm)
            with pytest.raises(ValueError):
                _ = BPMEvent.from_chart_line(current_line, prev_event, pytest.defaults.resolution)

        def test_no_match(self):
            with pytest.raises(RegexNotMatchError):
                _ = BPMEvent.from_chart_line(
                    pytest.invalid_chart_line, None, pytest.defaults.resolution
                )
