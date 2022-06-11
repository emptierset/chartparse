import pytest

from chartparse.event import BPMEvent, TimeSignatureEvent
from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.track import (
    SyncTrack,
    _parse_events_from_iterable,
)


class TestParseEventsFromIterable(object):
    def test_parse_events_from_iterable(self, generate_valid_bpm_line):
        lines = [generate_valid_bpm_line()]

        def fake_from_chart_line_fn(_):
            return pytest.default_bpm_event

        assert _parse_events_from_iterable(lines, fake_from_chart_line_fn) == [
            pytest.default_bpm_event
        ]

    def test_parse_events_from_iterable_regex_no_match(
        self, invalid_chart_line, unmatchable_regex
    ):
        def fake_from_chart_line(_):
            raise RegexFatalNotMatchError(unmatchable_regex, invalid_chart_line)

        assert _parse_events_from_iterable([invalid_chart_line], fake_from_chart_line) == []


class TestGlobalEventsTrack(object):
    def test_init(self, basic_global_events_track):
        assert basic_global_events_track.events == pytest.default_global_event_list


class TestSyncTrack(object):
    def test_init(self, basic_sync_track):
        assert basic_sync_track.time_signature_events == pytest.default_time_signature_event_list
        assert basic_sync_track.bpm_events == pytest.default_bpm_event_list

    def test_init_missing_first_time_signature_event(
        self, mocker, placeholder_string_iterator_getter
    ):
        mocker.patch(
            "chartparse.track._parse_events_from_iterable",
            return_value=[
                TimeSignatureEvent(
                    1,
                    pytest.default_upper_time_signature_numeral,
                    pytest.default_lower_time_signature_numeral,
                )
            ],
        )
        with pytest.raises(ValueError):
            _ = SyncTrack(placeholder_string_iterator_getter)

    def test_init_missing_first_bpm_event(self, mocker, placeholder_string_iterator_getter):
        mocker.patch(
            "chartparse.track._parse_events_from_iterable",
            side_effect=[
                pytest.default_time_signature_event_list,
                [BPMEvent(1, pytest.default_bpm)],
            ],
        )
        with pytest.raises(ValueError):
            _ = SyncTrack(placeholder_string_iterator_getter)

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
    def test_idx_of_proximal_bpm_event_raises_ValueError(
        self, bare_sync_track, start_idx, bpm_events
    ):
        bare_sync_track.bpm_events = bpm_events
        with pytest.raises(ValueError):
            _ = bare_sync_track.idx_of_proximal_bpm_event(0, start_idx=start_idx)
