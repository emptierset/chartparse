import pytest
import unittest.mock

from chartparse.exceptions import RegexNotMatchError
from chartparse.sync import SyncTrack, BPMEvent, TimeSignatureEvent


class TestSyncTrack(object):
    def test_init(self, basic_sync_track):
        assert basic_sync_track.time_signature_events == pytest.default_time_signature_event_list
        assert basic_sync_track.bpm_events == pytest.default_bpm_event_list

    def test_init_empty_time_signature_events(self):
        with pytest.raises(ValueError):
            _ = SyncTrack([], pytest.default_bpm_event_list)

    def test_init_missing_first_time_signature_event(self, noninitial_time_signature_event):
        with pytest.raises(ValueError):
            _ = SyncTrack([noninitial_time_signature_event], pytest.default_bpm_event_list)

    def test_init_empty_bpm_events(self):
        with pytest.raises(ValueError):
            _ = SyncTrack(pytest.default_time_signature_event_list, [])

    def test_init_missing_first_bpm_event(self, noninitial_bpm_event):
        with pytest.raises(ValueError):
            _ = SyncTrack(pytest.default_time_signature_event_list, [noninitial_bpm_event])

    def test_from_chart_lines(self, mocker, placeholder_string_iterator_getter):
        mock_parse_events = mocker.patch(
            "chartparse.sync.SyncTrack._parse_events_from_chart_lines",
            side_effect=[
                pytest.default_time_signature_event_list,
                pytest.default_bpm_event_list,
            ],
        )
        init_spy = mocker.spy(SyncTrack, "__init__")
        _ = SyncTrack.from_chart_lines(placeholder_string_iterator_getter)
        mock_parse_events.assert_has_calls(
            [
                unittest.mock.call(
                    placeholder_string_iterator_getter(), TimeSignatureEvent.from_chart_line
                ),
                unittest.mock.call(placeholder_string_iterator_getter(), BPMEvent.from_chart_line),
            ]
        )
        init_spy.assert_called_once_with(
            unittest.mock.ANY,
            pytest.default_time_signature_event_list,
            pytest.default_bpm_event_list,
        )

    @pytest.mark.parametrize(
        "tick,start_idx,bpm_events,want",
        [
            pytest.param(
                1, 0, [BPMEvent(0, pytest.default_bpm), BPMEvent(2, pytest.default_bpm)], 0
            ),
            pytest.param(
                2, 0, [BPMEvent(0, pytest.default_bpm), BPMEvent(2, pytest.default_bpm)], 1
            ),
            pytest.param(
                2, 1, [BPMEvent(0, pytest.default_bpm), BPMEvent(2, pytest.default_bpm)], 1
            ),
            pytest.param(
                3, 0, [BPMEvent(0, pytest.default_bpm), BPMEvent(2, pytest.default_bpm)], 1
            ),
            pytest.param(
                3, 1, [BPMEvent(0, pytest.default_bpm), BPMEvent(2, pytest.default_bpm)], 1
            ),
        ],
    )
    def test_idx_of_proximal_bpm_event(self, bare_sync_track, tick, start_idx, bpm_events, want):
        bare_sync_track.bpm_events = bpm_events
        assert bare_sync_track.idx_of_proximal_bpm_event(tick, start_idx=start_idx) == want

    @pytest.mark.parametrize(
        "start_idx,bpm_events",
        [
            pytest.param(0, []),
            pytest.param(1, [BPMEvent(0, pytest.default_bpm)]),
        ],
    )
    def test_idx_of_proximal_bpm_event_raises(self, bare_sync_track, start_idx, bpm_events):
        bare_sync_track.bpm_events = bpm_events
        with pytest.raises(ValueError):
            _ = bare_sync_track.idx_of_proximal_bpm_event(0, start_idx=start_idx)


class TestTimeSignatureEvent(object):
    def test_init(self, time_signature_event):
        assert time_signature_event.upper_numeral == pytest.default_upper_time_signature_numeral
        assert time_signature_event.lower_numeral == pytest.default_lower_time_signature_numeral

    def test_from_chart_line_short(self, generate_valid_short_time_signature_line):
        line = generate_valid_short_time_signature_line()
        event = TimeSignatureEvent.from_chart_line(line)
        assert event.upper_numeral == pytest.default_upper_time_signature_numeral

    def test_from_chart_line_long(self, generate_valid_long_time_signature_line):
        line = generate_valid_long_time_signature_line()
        event = TimeSignatureEvent.from_chart_line(line)
        assert event.upper_numeral == pytest.default_upper_time_signature_numeral
        assert event.lower_numeral == pytest.default_lower_time_signature_numeral

    def test_from_chart_line_no_match(self, invalid_chart_line):
        with pytest.raises(RegexNotMatchError):
            _ = TimeSignatureEvent.from_chart_line(invalid_chart_line)


class TestBPMEvent(object):
    def test_init(self, bpm_event):
        assert bpm_event.bpm == pytest.default_bpm

    def test_init_more_than_three_decimal_places_error(self):
        with pytest.raises(ValueError):
            _ = BPMEvent(pytest.default_tick, 120.0001)

    def test_from_chart_line(self, generate_valid_bpm_line):
        line = generate_valid_bpm_line()
        event = BPMEvent.from_chart_line(line)
        assert event.bpm == pytest.default_bpm

    def test_from_chart_line_no_match(self, generate_valid_short_time_signature_line):
        line = generate_valid_short_time_signature_line()
        with pytest.raises(RegexNotMatchError):
            _ = BPMEvent.from_chart_line(line)
