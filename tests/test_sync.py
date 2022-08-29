import datetime
import pytest
import unittest.mock

from chartparse.event import Event
from chartparse.exceptions import RegexNotMatchError
from chartparse.sync import SyncTrack, BPMEvent, TimeSignatureEvent

from tests.helpers.datastructures import AlreadySortedImmutableSortedList
from tests.helpers.lines import generate_bpm as generate_bpm_line
from tests.helpers.lines import generate_time_signature as generate_time_signature_line
from tests.helpers.sync import (
    TimeSignatureEventWithDefaults,
    TimeSignatureEventParsedDataWithDefaults,
    BPMEventWithDefaults,
    BPMEventParsedDataWithDefaults,
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
        def test(self, mocker):
            mock_parse_data = mocker.patch.object(
                SyncTrack,
                "_parse_data_from_chart_lines",
                return_value=(
                    pytest.defaults.time_signature_event_parsed_datas,
                    pytest.defaults.bpm_event_parsed_datas,
                ),
            )
            mock_parse_events = mocker.patch(
                "chartparse.track.parse_events_from_data",
                side_effect=[
                    pytest.defaults.bpm_events,
                    pytest.defaults.time_signature_events,
                ],
            )
            spy_init = mocker.spy(SyncTrack, "__init__")
            _ = SyncTrack.from_chart_lines(pytest.defaults.resolution, pytest.invalid_chart_lines)

            mock_parse_data.assert_called_once_with(pytest.invalid_chart_lines)
            mock_parse_events.assert_has_calls(
                [
                    unittest.mock.call(
                        pytest.defaults.bpm_event_parsed_datas,
                        BPMEvent.from_parsed_data,
                        pytest.defaults.resolution,
                    ),
                    unittest.mock.call(
                        pytest.defaults.time_signature_event_parsed_datas,
                        TimeSignatureEvent.from_parsed_data,
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

            _ = bare_sync_track.timestamp_at_tick(pytest.defaults.tick, proximal_bpm_event_index=0)
            mock_impl.assert_called_once_with(
                pytest.defaults.bpm_events,
                pytest.defaults.tick,
                pytest.defaults.resolution,
                proximal_bpm_event_index=0,
            )

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
        def test_impl(self, tick, want_timestamp, want_proximal_bpm_event_index):
            resolution = 100
            event0 = BPMEvent.from_parsed_data(BPMEvent.ParsedData(0, "60000"), None, resolution)
            event1 = BPMEvent.from_parsed_data(
                BPMEvent.ParsedData(100, "120000"), event0, resolution
            )
            event2 = BPMEvent.from_parsed_data(
                BPMEvent.ParsedData(400, "180000"), event1, resolution
            )
            event3 = BPMEvent.from_parsed_data(
                BPMEvent.ParsedData(800, "90000"), event2, resolution
            )
            test_bpm_events = AlreadySortedImmutableSortedList([event0, event1, event2, event3])

            got_timestamp, got_proximal_bpm_event_index = SyncTrack._timestamp_at_tick(
                test_bpm_events, tick, resolution
            )
            assert got_timestamp == want_timestamp
            assert got_proximal_bpm_event_index == want_proximal_bpm_event_index

    class TestindexOfProximalBPMEvent(object):
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
            got = bare_sync_track._index_of_proximal_bpm_event(bpm_events, tick)
            assert got == want

        @pytest.mark.parametrize(
            "bpm_events,tick,proximal_bpm_event_index",
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
                    id="proximal_bpm_event_index_after_last_bpm_event",
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
                    id="input_tick_before_tick_at_proximal_bpm_event_index",
                ),
            ],
        )
        def test_raises(self, bare_sync_track, tick, proximal_bpm_event_index, bpm_events):
            with pytest.raises(ValueError):
                _ = bare_sync_track._index_of_proximal_bpm_event(
                    bpm_events,
                    pytest.defaults.tick,
                    proximal_bpm_event_index=proximal_bpm_event_index,
                )


class TestTimeSignatureEvent(object):
    class TestInit(object):
        def test(self, mocker):
            want_upper_numeral = 1
            want_lower_numeral = 2
            want_proximal_bpm_event_index = 3

            spy_init = mocker.spy(Event, "__init__")

            got = TimeSignatureEventWithDefaults(
                upper_numeral=want_upper_numeral,
                lower_numeral=want_lower_numeral,
                proximal_bpm_event_index=want_proximal_bpm_event_index,
            )

            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                pytest.defaults.tick,
                pytest.defaults.timestamp,
                proximal_bpm_event_index=want_proximal_bpm_event_index,
            )

            assert got.upper_numeral == want_upper_numeral
            assert got.lower_numeral == want_lower_numeral

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
                        lower=pytest.defaults.raw_lower_time_signature_numeral
                    ),
                    pytest.defaults.lower_time_signature_numeral,
                    id="line_with_lower_specified",
                ),
            ],
        )
        def test(self, mocker, default_tatter, prev_event, data, want_lower):
            spy_init = mocker.spy(TimeSignatureEvent, "__init__")

            _ = TimeSignatureEvent.from_parsed_data(data, prev_event, default_tatter)

            default_tatter.spy.assert_called_once_with(
                pytest.defaults.tick,
                proximal_bpm_event_index=prev_event._proximal_bpm_event_index if prev_event else 0,
            )
            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                pytest.defaults.tick,
                pytest.defaults.default_tatter_timestamp,
                pytest.defaults.upper_time_signature_numeral,
                want_lower,
                proximal_bpm_event_index=pytest.defaults.default_tatter_index,
            )

    class TestParsedData(object):
        class TestFromChartLine(object):
            @pytest.mark.parametrize(
                "line,want_lower",
                [
                    pytest.param(
                        generate_time_signature_line(
                            pytest.defaults.tick,
                            pytest.defaults.upper_time_signature_numeral,
                        ),
                        None,
                        id="line_without_lower_specified",
                    ),
                    pytest.param(
                        generate_time_signature_line(
                            pytest.defaults.tick,
                            pytest.defaults.upper_time_signature_numeral,
                            lower=pytest.defaults.raw_lower_time_signature_numeral,
                        ),
                        pytest.defaults.raw_lower_time_signature_numeral,
                        id="line_with_lower_specified",
                    ),
                ],
            )
            def test(self, mocker, line, want_lower):
                got = TimeSignatureEvent.ParsedData.from_chart_line(line)
                assert got.tick == pytest.defaults.tick
                assert got.upper == pytest.defaults.upper_time_signature_numeral
                assert got.lower == want_lower

            def test_no_match(self, invalid_chart_line, default_tatter):
                with pytest.raises(RegexNotMatchError):
                    _ = TimeSignatureEvent.ParsedData.from_chart_line(invalid_chart_line)


class TestBPMEvent(object):
    class TestInit(object):
        def test(self, mocker):
            want_proximal_bpm_event_index = 1

            spy_init = mocker.spy(Event, "__init__")

            got = BPMEventWithDefaults(proximal_bpm_event_index=want_proximal_bpm_event_index)

            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                pytest.defaults.tick,
                pytest.defaults.timestamp,
                proximal_bpm_event_index=want_proximal_bpm_event_index,
            )

            assert got.bpm == pytest.defaults.bpm

        def test_more_than_three_decimal_places_error(self):
            with pytest.raises(ValueError):
                _ = BPMEventWithDefaults(bpm=120.0001)

    class TestFromParsedData(object):
        def test_prev_event_none(self, mocker):
            spy_init = mocker.spy(BPMEvent, "__init__")

            _ = BPMEvent.from_parsed_data(
                BPMEventParsedDataWithDefaults(tick=0), None, pytest.defaults.resolution
            )

            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                0,
                datetime.timedelta(0),
                pytest.defaults.bpm,
                proximal_bpm_event_index=0,
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

            _ = BPMEvent.from_parsed_data(data, prev_event, pytest.defaults.resolution)

            mock_seconds_from_ticks_at_bpm.assert_called_once_with(
                data.tick - prev_event.tick,
                pytest.defaults.bpm,
                pytest.defaults.resolution,
            )

            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                data.tick,
                prev_event.timestamp + datetime.timedelta(seconds=seconds_since_prev),
                pytest.defaults.bpm,
                proximal_bpm_event_index=pytest.defaults.proximal_bpm_event_index,
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
                _ = BPMEvent.from_parsed_data(data, prev_event, pytest.defaults.resolution)

    class TestParsedData(object):
        class TestFromChartLine(object):
            def test(self):
                line = generate_bpm_line(pytest.defaults.tick, pytest.defaults.bpm)
                got = BPMEvent.ParsedData.from_chart_line(line)
                assert got.tick == pytest.defaults.tick
                assert got.raw_bpm == pytest.defaults.raw_bpm

            def test_no_match(self):
                with pytest.raises(RegexNotMatchError):
                    _ = BPMEvent.ParsedData.from_chart_line(pytest.invalid_chart_line)
