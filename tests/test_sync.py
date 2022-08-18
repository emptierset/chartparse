import datetime
import pytest
import unittest.mock
from contextlib import nullcontext as does_not_raise

from chartparse.exceptions import RegexNotMatchError
from chartparse.sync import SyncTrack, BPMEvent, TimeSignatureEvent

from tests.helpers.lines import generate_bpm as generate_bpm_line
from tests.helpers.lines import generate_time_signature as generate_time_signature_line
from tests.helpers.constructors import TimeSignatureEventWithDefaults


class TestSyncTrack(object):
    class TestInit(object):
        def test_basic(self):
            got = SyncTrack(
                pytest.default_time_signature_event_list, pytest.default_bpm_event_list
            )
            assert got.time_signature_events == pytest.default_time_signature_event_list
            assert got.bpm_events == pytest.default_bpm_event_list

        def test_empty_time_signature_events(self):
            with pytest.raises(ValueError):
                _ = SyncTrack([], pytest.default_bpm_event_list)

        def test_missing_first_time_signature_event(self):
            noninitial_time_signature_event = TimeSignatureEventWithDefaults(
                tick=1,
                timestamp=datetime.timedelta(seconds=1),
            )
            with pytest.raises(ValueError):
                _ = SyncTrack([noninitial_time_signature_event], pytest.default_bpm_event_list)

        def test_empty_bpm_events(self):
            with pytest.raises(ValueError):
                _ = SyncTrack(pytest.default_time_signature_event_list, [])

        def test_missing_first_bpm_event(self):
            noninitial_bpm_event = BPMEvent(1, datetime.timedelta(seconds=1), pytest.default_bpm)
            with pytest.raises(ValueError):
                _ = SyncTrack(pytest.default_time_signature_event_list, [noninitial_bpm_event])

    class TestFromChartLines(object):
        def test_basic(self, mocker, minimal_string_iterator_getter):
            mock_parse_events = mocker.patch(
                "chartparse.track.parse_events_from_chart_lines",
                side_effect=[
                    pytest.default_bpm_event_list,
                    pytest.default_time_signature_event_list,
                ],
            )
            spy_init = mocker.spy(SyncTrack, "__init__")
            _ = SyncTrack.from_chart_lines(
                minimal_string_iterator_getter, pytest.default_resolution
            )
            mock_parse_events.assert_has_calls(
                [
                    unittest.mock.call(
                        pytest.default_resolution,
                        minimal_string_iterator_getter(),
                        BPMEvent.from_chart_line,
                    ),
                    unittest.mock.call(
                        pytest.default_resolution,
                        minimal_string_iterator_getter(),
                        TimeSignatureEvent.from_chart_line,
                        unittest.mock.ANY,
                    ),
                ]
            )
            spy_init.assert_called_once_with(
                unittest.mock.ANY,
                pytest.default_time_signature_event_list,
                pytest.default_bpm_event_list,
            )

    class TestTimestampAtTick(object):
        def test_wrapper(self, mocker, bare_sync_track):
            bare_sync_track.bpm_events = pytest.default_bpm_event_list
            mock = mocker.patch.object(bare_sync_track, "_timestamp_at_tick")
            _ = bare_sync_track.timestamp_at_tick(
                pytest.default_tick, pytest.default_resolution, start_bpm_event_index=0
            )
            mock.assert_called_once_with(
                pytest.default_bpm_event_list, pytest.default_tick, pytest.default_resolution, 0
            )

        event0 = BPMEvent.from_chart_line(generate_bpm_line(0, 60.000), None, 100)
        event1 = BPMEvent.from_chart_line(generate_bpm_line(100, 120.000), event0, 100)
        event2 = BPMEvent.from_chart_line(generate_bpm_line(400, 180.000), event1, 100)
        event3 = BPMEvent.from_chart_line(generate_bpm_line(800, 90.000), event2, 100)
        test_bpm_events = [event0, event1, event2, event3]

        @pytest.mark.parametrize(
            "resolution,tick,want_timestamp,want_proximal_bpm_event_idx",
            [
                # TODO: Create helper that allows me to define pytest.param values by "name".
                pytest.param(100, 100, datetime.timedelta(seconds=1), 1),
                pytest.param(100, 120, datetime.timedelta(seconds=1.1), 1),
                pytest.param(100, 400, datetime.timedelta(seconds=2.5), 2),
                pytest.param(100, 1000, datetime.timedelta(seconds=5.166666), 3),
            ],
        )
        def test_impl(self, resolution, tick, want_timestamp, want_proximal_bpm_event_idx):
            got_timestamp, got_proximal_bpm_event_idx = SyncTrack._timestamp_at_tick(
                self.test_bpm_events, tick, resolution
            )
            assert got_timestamp == want_timestamp
            assert got_proximal_bpm_event_idx == want_proximal_bpm_event_idx

    class TestIdxOfProximalBPMEvent(object):
        BPMEventFromTick = lambda tick: BPMEvent(
            tick, pytest.default_timestamp, pytest.default_bpm
        )

        @pytest.mark.parametrize(
            "tick,start_idx,bpm_events,want,expectation",
            [
                pytest.param(
                    1, 0, [BPMEventFromTick(0), BPMEventFromTick(2)], 0, does_not_raise()
                ),
                pytest.param(
                    2, 0, [BPMEventFromTick(0), BPMEventFromTick(2)], 1, does_not_raise()
                ),
                pytest.param(
                    2, 1, [BPMEventFromTick(0), BPMEventFromTick(2)], 1, does_not_raise()
                ),
                pytest.param(
                    3, 0, [BPMEventFromTick(0), BPMEventFromTick(2)], 1, does_not_raise()
                ),
                pytest.param(
                    3, 1, [BPMEventFromTick(0), BPMEventFromTick(2)], 1, does_not_raise()
                ),
                pytest.param(
                    pytest.default_tick, 0, [], unittest.mock.ANY, pytest.raises(ValueError)
                ),
                pytest.param(
                    pytest.default_tick,
                    1,
                    [BPMEventFromTick(0)],
                    unittest.mock.ANY,
                    pytest.raises(ValueError),
                ),
            ],
        )
        def test_basic(self, bare_sync_track, tick, start_idx, bpm_events, want, expectation):
            with expectation:
                got = bare_sync_track._idx_of_proximal_bpm_event(
                    bpm_events, tick, start_idx=start_idx
                )
                assert got == want


class TestTimeSignatureEvent(object):
    class TestInit(object):
        def test_basic(self):
            event = TimeSignatureEventWithDefaults()
            assert event.upper_numeral == pytest.default_upper_time_signature_numeral
            assert event.lower_numeral == pytest.default_lower_time_signature_numeral

    class TestFromChartLine(object):
        def test_shortform(self, mocker, minimal_timestamp_getter):
            spy_calculate_timestamp = mocker.spy(TimeSignatureEvent, "calculate_timestamp")
            line = generate_time_signature_line(
                pytest.default_tick, pytest.default_upper_time_signature_numeral
            )
            event = TimeSignatureEvent.from_chart_line(
                line,
                None,
                minimal_timestamp_getter,
                pytest.default_resolution,
            )
            spy_calculate_timestamp.assert_called_once_with(
                pytest.default_tick, None, minimal_timestamp_getter, pytest.default_resolution
            )
            assert event.upper_numeral == pytest.default_upper_time_signature_numeral
            assert event.lower_numeral == TimeSignatureEvent._default_lower_numeral

        def test_longform(self, mocker, minimal_timestamp_getter):
            spy_calculate_timestamp = mocker.spy(TimeSignatureEvent, "calculate_timestamp")
            line = generate_time_signature_line(
                pytest.default_tick,
                pytest.default_upper_time_signature_numeral,
                pytest.default_lower_time_signature_numeral,
            )
            event = TimeSignatureEvent.from_chart_line(
                line,
                None,
                minimal_timestamp_getter,
                pytest.default_resolution,
            )
            spy_calculate_timestamp.assert_called_once_with(
                pytest.default_tick, None, minimal_timestamp_getter, pytest.default_resolution
            )
            assert event.upper_numeral == pytest.default_upper_time_signature_numeral
            assert event.lower_numeral == pytest.default_lower_time_signature_numeral

        def test_no_match(self, invalid_chart_line, minimal_timestamp_getter):
            with pytest.raises(RegexNotMatchError):
                _ = TimeSignatureEvent.from_chart_line(
                    invalid_chart_line,
                    None,
                    minimal_timestamp_getter,
                    pytest.default_resolution,
                )


class TestBPMEvent(object):
    class TestInit(object):
        def test_basic(self, default_bpm_event):
            assert default_bpm_event.bpm == pytest.default_bpm

        def test_more_than_three_decimal_places_error(self):
            with pytest.raises(ValueError):
                _ = BPMEvent(pytest.default_tick, pytest.default_timestamp, 120.0001)

    class TestFromChartLine(object):
        @pytest.mark.parametrize(
            "prev_event_tick,current_event_tick,expectation",
            [
                pytest.param(
                    None,
                    pytest.default_tick,
                    does_not_raise(),
                    id="None prev event",
                ),
                pytest.param(
                    pytest.default_tick,
                    pytest.default_tick + 1,
                    does_not_raise(),
                    id="Present prev event",
                ),
                pytest.param(
                    pytest.default_tick + 1,
                    pytest.default_tick,
                    pytest.raises(ValueError),
                    id="Prev event after current",
                ),
                pytest.param(
                    pytest.default_tick,
                    pytest.default_tick,
                    pytest.raises(ValueError),
                    id="Prev event equal to current",
                ),
            ],
        )
        def test_basic(self, mocker, prev_event_tick, current_event_tick, expectation):
            if prev_event_tick is None:
                prev_event = None
            else:
                prev_event = BPMEvent(
                    prev_event_tick, pytest.default_timestamp, pytest.default_bpm
                )

            current_line = generate_bpm_line(current_event_tick, pytest.default_bpm)
            spy_calculate_timestamp = mocker.spy(BPMEvent, "calculate_timestamp")
            with expectation:
                current_event = BPMEvent.from_chart_line(
                    current_line, prev_event, pytest.default_resolution
                )
                assert current_event.bpm == pytest.default_bpm
            # Use ANY to match the function defined within ``from_chart_line``.
            spy_calculate_timestamp.assert_called_once_with(
                current_event_tick,
                prev_event,
                unittest.mock.ANY,
                pytest.default_resolution,
            )

        def test_no_match(self, generate_valid_short_time_signature_line):
            line = generate_valid_short_time_signature_line()
            with pytest.raises(RegexNotMatchError):
                _ = BPMEvent.from_chart_line(line, None, pytest.default_resolution)
