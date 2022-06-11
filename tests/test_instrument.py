import pytest

from chartparse.enums import Note, NoteTrackIndex
from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.instrument import InstrumentTrack, StarPowerEvent, NoteEvent

from tests.conftest import (
    generate_valid_note_line_fn,
    generate_valid_star_power_line_fn,
)


class TestInstrumentTrack(object):
    def test_init(self, mocker, basic_instrument_track):
        assert basic_instrument_track.instrument == pytest.default_instrument
        assert basic_instrument_track.difficulty == pytest.default_difficulty
        assert basic_instrument_track.note_events == pytest.default_note_event_list
        assert basic_instrument_track.star_power_events == pytest.default_star_power_event_list

    @pytest.mark.parametrize(
        "lines, want_note_events, want_star_power_events",
        [
            pytest.param([pytest.invalid_chart_line], [], [], id="skip_invalid_line"),
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
                    generate_valid_note_line_fn(0, NoteTrackIndex.TAP.value),
                ],
                [NoteEvent(0, Note.G, is_tap=True)],
                [],
                id="tap_green_note",
            ),
            pytest.param(
                [
                    generate_valid_note_line_fn(0, NoteTrackIndex.G.value),
                    generate_valid_note_line_fn(0, NoteTrackIndex.FORCED.value),
                ],
                [NoteEvent(0, Note.G, is_forced=True)],
                [],
                id="forced_green_note",
            ),
            pytest.param(
                [
                    generate_valid_note_line_fn(0, NoteTrackIndex.G.value, duration=100),
                ],
                [NoteEvent(0, Note.G, duration=100)],
                [],
                id="green_with_duration",
            ),
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
                    generate_valid_note_line_fn(2075, NoteTrackIndex.Y.value),
                    generate_valid_note_line_fn(2075, NoteTrackIndex.B.value),
                    generate_valid_star_power_line_fn(2000, 80),
                    generate_valid_note_line_fn(2100, NoteTrackIndex.O.value),
                    generate_valid_note_line_fn(2100, NoteTrackIndex.FORCED.value),
                    generate_valid_note_line_fn(2200, NoteTrackIndex.B.value),
                    generate_valid_note_line_fn(2200, NoteTrackIndex.TAP.value),
                    generate_valid_note_line_fn(2300, NoteTrackIndex.OPEN.value),
                ],
                [
                    NoteEvent(
                        0,
                        Note.G,
                        duration=100,
                        star_power_data=NoteEvent.StarPowerData(0, True),
                    ),
                    NoteEvent(
                        2000,
                        Note.R,
                        duration=50,
                        star_power_data=NoteEvent.StarPowerData(1, False),
                    ),
                    NoteEvent(
                        2075,
                        Note.YB,
                        star_power_data=NoteEvent.StarPowerData(1, True),
                    ),
                    NoteEvent(2100, Note.O, is_forced=True),
                    NoteEvent(2200, Note.B, is_tap=True),
                    NoteEvent(2300, Note.OPEN),
                ],
                [StarPowerEvent(0, 100), StarPowerEvent(2000, 80)],
                id="everything_together",
            ),
        ],
    )
    def test_parse_note_events_from_iterable(
        self, invalid_chart_line, lines, want_note_events, want_star_power_events
    ):
        lines_iterator_getter = lambda: iter(lines)
        instrument_track = InstrumentTrack(
            pytest.default_instrument, pytest.default_difficulty, lines_iterator_getter
        )
        assert instrument_track.instrument == pytest.default_instrument
        assert instrument_track.difficulty == pytest.default_difficulty
        assert instrument_track.note_events == want_note_events
        assert instrument_track.star_power_events == want_star_power_events

    @pytest.mark.parametrize(
        "note_events,star_power_events,want_note_events",
        [
            pytest.param(
                [
                    NoteEvent(0, Note.G, duration=100),
                    NoteEvent(2000, Note.R, duration=50),
                    NoteEvent(2075, Note.YB),
                ],
                [
                    StarPowerEvent(0, 100),
                    StarPowerEvent(2000, 80),
                ],
                [
                    NoteEvent(
                        0,
                        Note.G,
                        duration=100,
                        star_power_data=NoteEvent.StarPowerData(0, True),
                    ),
                    NoteEvent(
                        2000,
                        Note.R,
                        duration=50,
                        star_power_data=NoteEvent.StarPowerData(1, False),
                    ),
                    NoteEvent(
                        2075,
                        Note.YB,
                        star_power_data=NoteEvent.StarPowerData(1, True),
                    ),
                ],
                id="basic",
            ),
        ],
    )
    def test_populate_star_power_data(
        self, bare_instrument_track, note_events, star_power_events, want_note_events
    ):
        bare_instrument_track.note_events = note_events
        bare_instrument_track.star_power_events = star_power_events
        bare_instrument_track._populate_star_power_data()
        assert bare_instrument_track.note_events == want_note_events


class TestNoteEvent(object):
    def test_init(self, note_event_with_all_optionals_set):
        assert note_event_with_all_optionals_set.note == pytest.default_note
        assert note_event_with_all_optionals_set.duration == pytest.default_duration
        assert note_event_with_all_optionals_set.is_forced is True
        assert note_event_with_all_optionals_set.is_tap is True

    def test_validate_duration(self):
        NoteEvent._validate_duration(0, Note.G)
        NoteEvent._validate_duration([100, None, None, None, None], Note.G)
        with pytest.raises(TypeError):
            NoteEvent._validate_duration((100, None, None, None, None), Note.G)

    def test_validate_int_duration_negative(self):
        with pytest.raises(ValueError):
            NoteEvent._validate_int_duration(-1)

    @pytest.mark.parametrize(
        "duration, note",
        [
            pytest.param(
                [None, None, None, None], pytest.default_note, id="incorrect_length_list"
            ),
            pytest.param([100, 100, None, None, None], Note.G, id="mismatched_set_lanes"),
        ],
    )
    def test_validate_list_duration_raises_ValueError(self, duration, note):
        with pytest.raises(ValueError):
            NoteEvent._validate_list_duration(duration, note)

    @pytest.mark.parametrize(
        "duration, want",
        [
            pytest.param([None, None, None, None, None], 0, id="all_none"),
            pytest.param([100, None, None, 100, None], 100, id="all_the_same"),
            pytest.param(100, 100, id="int_pass_through"),
            pytest.param(
                [100, 0, None, None, None], [100, 0, None, None, None], id="list_pass_through"
            ),
        ],
    )
    def test_refine_duration(self, duration, want):
        assert NoteEvent._refine_duration(duration) == want


class TestStarPowerEvent(object):
    def test_init(self, star_power_event):
        assert star_power_event.duration == pytest.default_duration

    def test_from_chart_line(self, generate_valid_star_power_line):
        line = generate_valid_star_power_line()
        event = StarPowerEvent.from_chart_line(line)
        assert event.tick == pytest.default_tick
        assert event.duration == pytest.default_duration

    def test_from_chart_line_no_match(self, generate_valid_note_line):
        line = generate_valid_note_line()
        with pytest.raises(RegexFatalNotMatchError):
            _ = StarPowerEvent.from_chart_line(line)
