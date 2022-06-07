import pytest
import re
import unittest.mock

from chartparse.enums import Note, NoteTrackIndex
from chartparse.event import BPMEvent, TimeSignatureEvent, StarPowerEvent, NoteEvent
from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.track import Events, InstrumentTrack, SyncTrack, _parse_events_from_iterable

from tests.conftest import (
    generate_valid_note_line_fn,
    generate_valid_star_power_line_fn,
    generate_valid_bpm_line_fn,
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


class TestEvents(object):
    def test_init(self, basic_events_track):
        assert basic_events_track.events == pytest.default_events_event_list


class TestInstrumentTrack(object):
    def test_init(self, mocker, basic_instrument_track):
        assert basic_instrument_track.instrument == pytest.default_instrument
        assert basic_instrument_track.difficulty == pytest.default_difficulty
        assert basic_instrument_track.note_events == pytest.default_note_event_list
        assert basic_instrument_track.star_power_events == pytest.default_star_power_event_list

    @pytest.mark.parametrize(
        "lines, want_note_events, want_star_power_events",
        [
            pytest.param(
                [generate_valid_note_line_fn(0, NoteTrackIndex.OPEN.value)],
                [NoteEvent(0, Note.OPEN)],
                [],
                id="open_note",
            ),
            pytest.param(
                [generate_valid_note_line_fn(0, NoteTrackIndex.G.value)],
                [NoteEvent(0, Note.G)],
                [],
                id="green_note",
            ),
            pytest.param(
                [generate_valid_note_line_fn(0, NoteTrackIndex.R.value)],
                [NoteEvent(0, Note.R)],
                [],
                id="red_note",
            ),
            pytest.param(
                [generate_valid_note_line_fn(0, NoteTrackIndex.Y.value)],
                [NoteEvent(0, Note.Y)],
                [],
                id="yellow_note",
            ),
            pytest.param(
                [generate_valid_note_line_fn(0, NoteTrackIndex.B.value)],
                [NoteEvent(0, Note.B)],
                [],
                id="blue_note",
            ),
            pytest.param(
                [generate_valid_note_line_fn(0, NoteTrackIndex.O.value)],
                [NoteEvent(0, Note.O)],
                [],
                id="orange_note",
            ),
            pytest.param(
                [
                    generate_valid_note_line_fn(0, NoteTrackIndex.G.value),
                    generate_valid_note_line_fn(1, NoteTrackIndex.R.value),
                    generate_valid_note_line_fn(1, NoteTrackIndex.Y.value),
                    generate_valid_note_line_fn(2, NoteTrackIndex.B.value),
                    generate_valid_note_line_fn(3, NoteTrackIndex.FORCED.value),
                    generate_valid_note_line_fn(3, NoteTrackIndex.Y.value),
                ],
                [
                    NoteEvent(0, Note.G),
                    NoteEvent(1, Note.RY),
                    NoteEvent(2, Note.B),
                    NoteEvent(3, Note.Y, is_forced=True),
                ],
                [],
                id="note_sequence",
            ),
            pytest.param([generate_valid_bpm_line_fn()], [], [], id="errant_bpm_event"),
            pytest.param(
                [
                    generate_valid_note_line_fn(0, NoteTrackIndex.G.value),
                    generate_valid_note_line_fn(0, NoteTrackIndex.R.value),
                ],
                [NoteEvent(0, Note.GR)],
                [],
                id="chord",
            ),
            pytest.param(
                [
                    generate_valid_note_line_fn(0, NoteTrackIndex.G.value),
                    generate_valid_note_line_fn(0, NoteTrackIndex.R.value),
                    generate_valid_note_line_fn(0, NoteTrackIndex.TAP.value),
                    generate_valid_note_line_fn(0, NoteTrackIndex.FORCED.value),
                ],
                [NoteEvent(0, Note.GR, is_forced=True, is_tap=True)],
                [],
                id="chord_tap_forced",
            ),
            pytest.param(
                [
                    generate_valid_note_line_fn(0, NoteTrackIndex.G.value, duration=100),
                    generate_valid_note_line_fn(0, NoteTrackIndex.R.value, duration=100),
                ],
                [NoteEvent(0, Note.GR, duration=100)],
                [],
                id="basic_duration",
            ),
            pytest.param(
                [
                    generate_valid_note_line_fn(0, NoteTrackIndex.G.value, duration=100),
                    generate_valid_note_line_fn(0, NoteTrackIndex.R.value),
                ],
                [NoteEvent(0, Note.GR, duration=[100, 0, None, None, None])],
                [],
                id="nonuniform_durations",
            ),
            pytest.param(
                [generate_valid_star_power_line_fn(0, 100)],
                [],
                [StarPowerEvent(0, 100)],
                id="single_star_power_phrase",
            ),
            pytest.param(
                [
                    generate_valid_note_line_fn(0, NoteTrackIndex.G.value, duration=100),
                    generate_valid_star_power_line_fn(0, 100),
                    generate_valid_note_line_fn(2000, NoteTrackIndex.R.value, duration=50),
                    generate_valid_star_power_line_fn(2000, 100),
                ],
                [NoteEvent(0, Note.G, duration=100), NoteEvent(2000, Note.R, duration=50)],
                [StarPowerEvent(0, 100), StarPowerEvent(2000, 100)],
                id="mix_of_notes_and_star_power",
            ),
        ],
    )
    def test_parse_note_events_from_iterable(
        self, lines, want_note_events, want_star_power_events
    ):
        lines_iterator_getter = lambda: iter(lines)
        instrument_track = InstrumentTrack(
            pytest.default_instrument, pytest.default_difficulty, lines_iterator_getter
        )
        assert instrument_track.instrument == pytest.default_instrument
        assert instrument_track.difficulty == pytest.default_difficulty
        assert instrument_track.note_events == want_note_events
        assert instrument_track.star_power_events == want_star_power_events


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
    def test_idx_of_proximal_bpm_event(self, basic_sync_track, tick, start_idx, bpm_events, want):
        basic_sync_track.bpm_events = bpm_events
        assert basic_sync_track.idx_of_proximal_bpm_event(tick, start_idx=start_idx) == want

    @pytest.mark.parametrize(
        "start_idx,bpm_events",
        [
            pytest.param(0, []),
            pytest.param(1, [BPMEvent(0, pytest.default_bpm)]),
        ],
    )
    def test_idx_of_proximal_bpm_event_raises_ValueError(
        self, basic_sync_track, start_idx, bpm_events
    ):
        basic_sync_track.bpm_events = bpm_events
        with pytest.raises(ValueError):
            _ = basic_sync_track.idx_of_proximal_bpm_event(0, start_idx=start_idx)
