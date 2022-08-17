import pytest
import re
import unittest.mock

import chartparse.tick
from chartparse.exceptions import RegexNotMatchError
from chartparse.instrument import (
    InstrumentTrack,
    StarPowerEvent,
    NoteEvent,
    StarPowerData,
    HOPOState,
    SpecialEvent,
    Note,
    NoteTrackIndex,
)
from chartparse.tick import NoteDuration

from tests.helpers.lines import generate_note as generate_note_line
from tests.helpers.lines import generate_star_power as generate_star_power_line
from tests.helpers.constructors import StarPowerEventWithDefaults


class TestInstrumentTrack(object):
    class TestInit(object):
        def test_basic(self, mocker, basic_instrument_track):
            mock_populate_star_power_data = mocker.patch.object(
                InstrumentTrack, "_populate_star_power_data"
            )
            _ = InstrumentTrack(
                pytest.default_instrument,
                pytest.default_difficulty,
                pytest.default_note_event_list,
                pytest.default_star_power_event_list,
            )
            assert basic_instrument_track.instrument == pytest.default_instrument
            assert basic_instrument_track.difficulty == pytest.default_difficulty
            assert basic_instrument_track.note_events == pytest.default_note_event_list
            assert basic_instrument_track.star_power_events == pytest.default_star_power_event_list
            assert basic_instrument_track.section_name == pytest.default_section_name
            mock_populate_star_power_data.assert_called_once()

    class TestFromChartLines(object):
        def test_basic(self, mocker, minimal_string_iterator_getter, minimal_timestamp_getter):
            mock_parse_note_events = mocker.patch.object(
                InstrumentTrack,
                "_parse_note_events_from_chart_lines",
                return_value=pytest.default_note_event_list,
            )
            mock_parse_events = mocker.patch(
                "chartparse.track.parse_events_from_chart_lines",
                return_value=pytest.default_star_power_event_list,
            )
            mock_init = mocker.spy(InstrumentTrack, "__init__")
            _ = InstrumentTrack.from_chart_lines(
                pytest.default_instrument,
                pytest.default_difficulty,
                minimal_string_iterator_getter,
                minimal_timestamp_getter,
                pytest.default_resolution,
            )
            mock_parse_note_events.assert_called_once_with(
                minimal_string_iterator_getter(),
                minimal_timestamp_getter,
                pytest.default_resolution,
            )
            mock_parse_events.assert_called_once_with(
                pytest.default_resolution,
                minimal_string_iterator_getter(),
                StarPowerEvent.from_chart_line,
                minimal_timestamp_getter,
            )
            mock_init.assert_called_once_with(
                unittest.mock.ANY,
                pytest.default_instrument,
                pytest.default_difficulty,
                pytest.default_note_event_list,
                pytest.default_star_power_event_list,
            )

        @pytest.mark.parametrize(
            "lines, want_note_events, want_star_power_events",
            [
                pytest.param([pytest.invalid_chart_line], [], [], id="skip_invalid_line"),
                pytest.param(
                    [generate_note_line(0, NoteTrackIndex.OPEN.value)],
                    # TODO: Create helper NoteEventWithDefaults.
                    [NoteEvent(0, pytest.default_timestamp, Note.OPEN)],
                    [],
                    id="open_note",
                ),
                pytest.param(
                    [generate_note_line(0, NoteTrackIndex.G.value)],
                    [NoteEvent(0, pytest.default_timestamp, Note.G)],
                    [],
                    id="green_note",
                ),
                pytest.param(
                    [generate_note_line(0, NoteTrackIndex.R.value)],
                    [NoteEvent(0, pytest.default_timestamp, Note.R)],
                    [],
                    id="red_note",
                ),
                pytest.param(
                    [generate_note_line(0, NoteTrackIndex.Y.value)],
                    [NoteEvent(0, pytest.default_timestamp, Note.Y)],
                    [],
                    id="yellow_note",
                ),
                pytest.param(
                    [generate_note_line(0, NoteTrackIndex.B.value)],
                    [NoteEvent(0, pytest.default_timestamp, Note.B)],
                    [],
                    id="blue_note",
                ),
                pytest.param(
                    [generate_note_line(0, NoteTrackIndex.O.value)],
                    [NoteEvent(0, pytest.default_timestamp, Note.O)],
                    [],
                    id="orange_note",
                ),
                pytest.param(
                    [
                        generate_note_line(0, NoteTrackIndex.G.value),
                        generate_note_line(0, NoteTrackIndex.TAP.value),
                    ],
                    [NoteEvent(0, pytest.default_timestamp, Note.G, is_tap=True)],
                    [],
                    id="tap_green_note",
                ),
                pytest.param(
                    [
                        generate_note_line(0, NoteTrackIndex.G.value),
                        generate_note_line(0, NoteTrackIndex.FORCED.value),
                    ],
                    [NoteEvent(0, pytest.default_timestamp, Note.G, is_forced=True)],
                    [],
                    id="forced_green_note",
                ),
                pytest.param(
                    [
                        generate_note_line(0, NoteTrackIndex.G.value, sustain=100),
                    ],
                    [NoteEvent(0, pytest.default_timestamp, Note.G, sustain=100)],
                    [],
                    id="green_with_sustain",
                ),
                pytest.param(
                    [
                        generate_note_line(0, NoteTrackIndex.G.value),
                        generate_note_line(0, NoteTrackIndex.R.value),
                    ],
                    [NoteEvent(0, pytest.default_timestamp, Note.GR)],
                    [],
                    id="chord",
                ),
                pytest.param(
                    [
                        generate_note_line(0, NoteTrackIndex.G.value, sustain=100),
                        generate_note_line(0, NoteTrackIndex.R.value),
                    ],
                    [
                        NoteEvent(
                            0,
                            pytest.default_timestamp,
                            Note.GR,
                            sustain=[100, 0, None, None, None],
                        )
                    ],
                    [],
                    id="nonuniform_sustains",
                ),
                pytest.param(
                    [generate_star_power_line(0, 100)],
                    [],
                    [StarPowerEventWithDefaults(tick=0, sustain=100)],
                    id="single_star_power_phrase",
                ),
                pytest.param(
                    [
                        generate_note_line(0, NoteTrackIndex.G.value, sustain=100),
                        generate_star_power_line(0, 100),
                        generate_note_line(2000, NoteTrackIndex.R.value, sustain=50),
                        generate_note_line(2075, NoteTrackIndex.Y.value),
                        generate_note_line(2075, NoteTrackIndex.B.value),
                        generate_star_power_line(2000, 80),
                        generate_note_line(2100, NoteTrackIndex.O.value),
                        generate_note_line(2100, NoteTrackIndex.FORCED.value),
                        generate_note_line(2200, NoteTrackIndex.B.value),
                        generate_note_line(2200, NoteTrackIndex.TAP.value),
                        generate_note_line(2300, NoteTrackIndex.OPEN.value),
                    ],
                    [
                        NoteEvent(
                            0,
                            pytest.default_timestamp,
                            Note.G,
                            sustain=100,
                            star_power_data=StarPowerData(0, True),
                        ),
                        NoteEvent(
                            2000,
                            pytest.default_timestamp,
                            Note.R,
                            sustain=50,
                            star_power_data=StarPowerData(1, False),
                        ),
                        NoteEvent(
                            2075,
                            pytest.default_timestamp,
                            Note.YB,
                            star_power_data=StarPowerData(1, True),
                        ),
                        NoteEvent(2100, pytest.default_timestamp, Note.O, is_forced=True),
                        NoteEvent(2200, pytest.default_timestamp, Note.B, is_tap=True),
                        NoteEvent(2300, pytest.default_timestamp, Note.OPEN),
                    ],
                    [
                        StarPowerEventWithDefaults(tick=0, sustain=100),
                        StarPowerEventWithDefaults(tick=2000, sustain=80),
                    ],
                    id="everything_together",
                ),
            ],
        )
        def test_integration(self, mocker, lines, want_note_events, want_star_power_events):
            timestamp_getter_mock = mocker.Mock(return_value=(pytest.default_timestamp, 0))

            lines_iterator_getter = lambda: iter(lines)
            instrument_track = InstrumentTrack.from_chart_lines(
                pytest.default_instrument,
                pytest.default_difficulty,
                lines_iterator_getter,
                timestamp_getter_mock,
                pytest.default_resolution,
            )
            assert instrument_track.instrument == pytest.default_instrument
            assert instrument_track.difficulty == pytest.default_difficulty
            assert instrument_track.note_events == want_note_events
            assert instrument_track.star_power_events == want_star_power_events

    class TestPopulateStarPowerData(object):
        @pytest.mark.parametrize(
            "note_events,star_power_events,want",
            [
                pytest.param(
                    [
                        NoteEvent(0, pytest.default_timestamp, Note.G, sustain=100),
                        NoteEvent(2000, pytest.default_timestamp, Note.R, sustain=50),
                        NoteEvent(2075, pytest.default_timestamp, Note.YB),
                    ],
                    [
                        StarPowerEventWithDefaults(tick=0, sustain=100),
                        StarPowerEventWithDefaults(tick=2000, sustain=80),
                    ],
                    [
                        NoteEvent(
                            0,
                            pytest.default_timestamp,
                            Note.G,
                            sustain=100,
                            star_power_data=StarPowerData(0, True),
                        ),
                        NoteEvent(
                            2000,
                            pytest.default_timestamp,
                            Note.R,
                            sustain=50,
                            star_power_data=StarPowerData(1, False),
                        ),
                        NoteEvent(
                            2075,
                            pytest.default_timestamp,
                            Note.YB,
                            star_power_data=StarPowerData(1, True),
                        ),
                    ],
                    id="basic",
                ),
            ],
        )
        def test_basic(self, bare_instrument_track, note_events, star_power_events, want):
            bare_instrument_track.note_events = note_events
            bare_instrument_track.star_power_events = star_power_events
            bare_instrument_track._populate_star_power_data()
            got = bare_instrument_track.note_events
            assert got == want


class TestNoteEvent(object):
    class TestInit(object):
        def test_basic(self, mocker):
            mock_validate_sustain = mocker.patch.object(NoteEvent, "_validate_sustain")
            mock_refine_sustain = mocker.patch.object(
                NoteEvent, "_refine_sustain", return_value=pytest.default_sustain
            )
            got = NoteEvent(
                pytest.default_tick,
                pytest.default_timestamp,
                pytest.default_note,
                sustain=pytest.default_sustain,
                is_forced=True,
                is_tap=True,
            )
            mock_validate_sustain.assert_called_once_with(
                pytest.default_sustain, pytest.default_note
            )
            mock_refine_sustain.assert_called_once_with(pytest.default_sustain)
            assert got.note == pytest.default_note
            assert got.sustain == pytest.default_sustain
            assert got._is_forced is True
            assert got._is_tap is True

    class TestValidateSustain(object):
        def test_int(self, mocker):
            sustain = 0
            mock = mocker.patch.object(NoteEvent, "_validate_int_sustain")
            NoteEvent._validate_sustain(sustain, pytest.default_note)
            mock.assert_called_once_with(sustain)

        def test_list(self, mocker):
            sustain = [100, None, None, None, None]
            mock = mocker.patch.object(NoteEvent, "_validate_list_sustain")
            NoteEvent._validate_sustain(sustain, pytest.default_note)
            mock.assert_called_once_with(sustain, pytest.default_note)

        def test_unhandled_type(self, mocker):
            with pytest.raises(TypeError):
                NoteEvent._validate_sustain((100, None, None, None, None), pytest.default_note)

    class TestValidateIntSustain(object):
        def test_negative(self):
            with pytest.raises(ValueError):
                NoteEvent._validate_int_sustain(-1)

    class TestValidateListSustain(object):
        @pytest.mark.parametrize(
            "sustain, note",
            [
                pytest.param(
                    [None, None, None, None], pytest.default_note, id="incorrect_length_list"
                ),
                pytest.param([100, 100, None, None, None], Note.G, id="mismatched_set_lanes"),
            ],
        )
        def test_raises(self, sustain, note):
            with pytest.raises(ValueError):
                NoteEvent._validate_list_sustain(sustain, note)

    class TestRefineSustain(object):
        @pytest.mark.parametrize(
            "sustain, want",
            [
                pytest.param([None, None, None, None, None], 0, id="all_none"),
                pytest.param([0, 0, 0, 0, 0], 0, id="all_zero"),
                pytest.param([0, 0, None, None, None], 0, id="all_none_or_zero"),
                pytest.param([100, None, None, 100, None], 100, id="all_the_same"),
                pytest.param(100, 100, id="int_pass_through"),
                pytest.param(
                    [100, 0, None, None, None], [100, 0, None, None, None], id="list_pass_through"
                ),
            ],
        )
        def test_basic(self, sustain, want):
            assert NoteEvent._refine_sustain(sustain) == want

    class TestComputeHOPOState(object):
        @pytest.mark.parametrize(
            "current,previous,want",
            [
                pytest.param(
                    NoteEvent(0, pytest.default_timestamp, Note.G, is_tap=True, is_forced=True),
                    None,
                    HOPOState.TAP,
                    id="tap_notes_are_taps",
                ),
                pytest.param(
                    NoteEvent(0, pytest.default_timestamp, Note.G),
                    None,
                    HOPOState.STRUM,
                    id="first_note_is_strum",
                ),
                pytest.param(
                    NoteEvent(
                        chartparse.tick.calculate_ticks_between_notes(
                            pytest.default_resolution,
                            NoteDuration.SIXTEENTH,
                        ),
                        pytest.default_timestamp,
                        Note.R,
                    ),
                    NoteEvent(0, pytest.default_timestamp, Note.G),
                    HOPOState.HOPO,
                    id="16th_notes_are_hopos",
                ),
                pytest.param(
                    NoteEvent(
                        chartparse.tick.calculate_ticks_between_notes(
                            pytest.default_resolution,
                            NoteDuration.TWELFTH,
                        ),
                        pytest.default_timestamp,
                        Note.R,
                    ),
                    NoteEvent(0, pytest.default_timestamp, Note.G),
                    HOPOState.HOPO,
                    id="12th_notes_are_hopos",
                ),
                pytest.param(
                    NoteEvent(
                        chartparse.tick.calculate_ticks_between_notes(
                            pytest.default_resolution,
                            NoteDuration.EIGHTH,
                        ),
                        pytest.default_timestamp,
                        Note.R,
                    ),
                    NoteEvent(0, pytest.default_timestamp, Note.G),
                    HOPOState.STRUM,
                    id="8th_notes_are_strums",
                ),
                pytest.param(
                    NoteEvent(
                        chartparse.tick.calculate_ticks_between_notes(
                            pytest.default_resolution,
                            NoteDuration.SIXTEENTH,
                        ),
                        pytest.default_timestamp,
                        Note.G,
                    ),
                    NoteEvent(0, pytest.default_timestamp, Note.G),
                    HOPOState.STRUM,
                    id="consecutive_16th_notes_are_strums",
                ),
                pytest.param(
                    NoteEvent(
                        chartparse.tick.calculate_ticks_between_notes(
                            pytest.default_resolution,
                            NoteDuration.TWELFTH,
                        ),
                        pytest.default_timestamp,
                        Note.G,
                    ),
                    NoteEvent(0, pytest.default_timestamp, Note.G),
                    HOPOState.STRUM,
                    id="consecutive_12th_notes_are_strums",
                ),
                pytest.param(
                    NoteEvent(
                        chartparse.tick.calculate_ticks_between_notes(
                            pytest.default_resolution,
                            NoteDuration.EIGHTH,
                        ),
                        pytest.default_timestamp,
                        Note.G,
                    ),
                    NoteEvent(0, pytest.default_timestamp, Note.G),
                    HOPOState.STRUM,
                    id="consecutive_8th_notes_are_strums",
                ),
                pytest.param(
                    NoteEvent(
                        chartparse.tick.calculate_ticks_between_notes(
                            pytest.default_resolution,
                            NoteDuration.TWELFTH,
                        ),
                        pytest.default_timestamp,
                        Note.G,
                    ),
                    NoteEvent(0, pytest.default_timestamp, Note.RY),
                    HOPOState.HOPO,
                    id="pull_off_from_chord_is_hopo",
                ),
                pytest.param(
                    NoteEvent(
                        chartparse.tick.calculate_ticks_between_notes(
                            pytest.default_resolution,
                            NoteDuration.TWELFTH,
                        ),
                        pytest.default_timestamp,
                        Note.RY,
                    ),
                    NoteEvent(0, pytest.default_timestamp, Note.G),
                    HOPOState.STRUM,
                    id="hammer_on_to_chord_is_not_hopo",
                ),
                pytest.param(
                    NoteEvent(
                        chartparse.tick.calculate_ticks_between_notes(
                            pytest.default_resolution,
                            NoteDuration.TWELFTH,
                        ),
                        pytest.default_timestamp,
                        Note.OPEN,
                    ),
                    NoteEvent(0, pytest.default_timestamp, Note.G),
                    HOPOState.HOPO,
                    id="hammer_on_to_open_is_hopo",
                ),
                pytest.param(
                    NoteEvent(
                        chartparse.tick.calculate_ticks_between_notes(
                            pytest.default_resolution,
                            NoteDuration.TWELFTH,
                        ),
                        pytest.default_timestamp,
                        Note.G,
                    ),
                    NoteEvent(0, pytest.default_timestamp, Note.OPEN),
                    HOPOState.HOPO,
                    id="pull_off_to_open_is_hopo",
                ),
            ],
        )
        def test_basic(self, current, previous, want):
            state = NoteEvent._compute_hopo_state(pytest.default_resolution, current, previous)
            assert state == want

    class TestLongestSustain(object):
        @pytest.mark.parametrize(
            "sustain,want",
            [
                pytest.param(100, 100),
                pytest.param([50, 100, None, 200, None], 200),
            ],
        )
        def test_basic(self, bare_note_event, sustain, want):
            bare_note_event.sustain = sustain
            assert bare_note_event.longest_sustain == want

        def test_raises(self, bare_note_event):
            bare_note_event.sustain = [None, None, None, None, None]
            with pytest.raises(ValueError):
                _ = bare_note_event.longest_sustain


class TestSpecialEvent(object):
    class TestInit(object):
        def test_basic(self, default_star_power_event):
            assert default_star_power_event.sustain == pytest.default_sustain

    class TestFromChartLine(object):
        test_regex = r"^T (\d+?) V (.*?)$"

        def setup_method(self):
            SpecialEvent._regex = self.test_regex
            SpecialEvent._regex_prog = re.compile(SpecialEvent._regex)

        def teardown_method(self):
            del SpecialEvent._regex
            del SpecialEvent._regex_prog

        def test_basic(self, mocker, minimal_timestamp_getter):
            line = f"T {pytest.default_tick} V {pytest.default_sustain}"
            spy_calculate_timestamp = mocker.spy(SpecialEvent, "calculate_timestamp")
            got = SpecialEvent.from_chart_line(
                line, None, minimal_timestamp_getter, pytest.default_resolution
            )
            spy_calculate_timestamp.assert_called_once_with(
                pytest.default_tick, None, minimal_timestamp_getter, pytest.default_resolution
            )
            assert got.sustain == pytest.default_sustain

        def test_no_match(self, invalid_chart_line, minimal_timestamp_getter):
            with pytest.raises(RegexNotMatchError):
                _ = SpecialEvent.from_chart_line(
                    invalid_chart_line,
                    None,
                    minimal_timestamp_getter,
                    pytest.default_resolution,
                )


# TODO: Test regex?
class TestStarPowerEvent(object):
    pass
