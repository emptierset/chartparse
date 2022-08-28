import datetime
import pytest
import re
import unittest.mock

from chartparse.event import Event
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

import tests.helpers.tick
from tests.helpers.datastructures import AlreadySortedImmutableSortedList
from tests.helpers.instrument import (
    StarPowerEventWithDefaults,
    NoteEventWithDefaults,
    SpecialEventWithDefaults,
)
from tests.helpers.lines import generate_note as generate_note_line
from tests.helpers.lines import generate_star_power as generate_star_power_line


class TestInstrumentTrack(object):
    class TestInit(object):
        def test(self, mocker, default_instrument_track):
            _ = InstrumentTrack(
                pytest.defaults.resolution,
                pytest.defaults.instrument,
                pytest.defaults.difficulty,
                pytest.defaults.note_events,
                pytest.defaults.star_power_events,
            )
            assert default_instrument_track.instrument == pytest.defaults.instrument
            assert default_instrument_track.difficulty == pytest.defaults.difficulty
            assert default_instrument_track.note_events == pytest.defaults.note_events
            assert default_instrument_track.star_power_events == pytest.defaults.star_power_events
            assert default_instrument_track.section_name == pytest.defaults.section_name

        def test_non_positive_resolution(self):
            with pytest.raises(ValueError):
                # TODO: Add InstrumentTrackWithDefaults (and other tracks)
                _ = InstrumentTrack(
                    0,
                    pytest.defaults.instrument,
                    pytest.defaults.difficulty,
                    pytest.defaults.note_events,
                    pytest.defaults.star_power_events,
                )
            with pytest.raises(ValueError):
                _ = InstrumentTrack(
                    -1,
                    pytest.defaults.instrument,
                    pytest.defaults.difficulty,
                    pytest.defaults.note_events,
                    pytest.defaults.star_power_events,
                )

    class TestFromChartLines(object):
        def test(self, mocker, minimal_string_iterator_getter, minimal_tatter):
            mock_parse_note_events = mocker.patch.object(
                InstrumentTrack,
                "_parse_note_events_from_chart_lines",
                return_value=pytest.defaults.note_events,
            )
            mock_parse_events = mocker.patch(
                "chartparse.track.parse_events_from_chart_lines",
                return_value=pytest.defaults.star_power_events,
            )
            spy_init = mocker.spy(InstrumentTrack, "__init__")
            _ = InstrumentTrack.from_chart_lines(
                pytest.defaults.instrument,
                pytest.defaults.difficulty,
                minimal_string_iterator_getter,
                minimal_tatter,
            )
            mock_parse_note_events.assert_called_once_with(
                minimal_string_iterator_getter(), pytest.defaults.star_power_events, minimal_tatter
            )
            mock_parse_events.assert_called_once_with(
                minimal_string_iterator_getter(), StarPowerEvent.from_chart_line, minimal_tatter
            )
            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                pytest.defaults.resolution,
                pytest.defaults.instrument,
                pytest.defaults.difficulty,
                pytest.defaults.note_events,
                pytest.defaults.star_power_events,
            )

        @pytest.mark.parametrize(
            "lines, want_note_events, want_star_power_events",
            [
                pytest.param(
                    [pytest.invalid_chart_line],
                    [],
                    [],
                    id="skip_invalid_line",
                ),
                pytest.param(
                    [generate_note_line(0, NoteTrackIndex.OPEN.value)],
                    [NoteEventWithDefaults(tick=0, note=Note.OPEN)],
                    [],
                    id="open_note",
                ),
                pytest.param(
                    [generate_note_line(0, NoteTrackIndex.G.value)],
                    [NoteEventWithDefaults(tick=0, note=Note.G)],
                    [],
                    id="green_note",
                ),
                pytest.param(
                    [generate_note_line(0, NoteTrackIndex.R.value)],
                    [NoteEventWithDefaults(tick=0, note=Note.R)],
                    [],
                    id="red_note",
                ),
                pytest.param(
                    [generate_note_line(0, NoteTrackIndex.Y.value)],
                    [NoteEventWithDefaults(tick=0, note=Note.Y)],
                    [],
                    id="yellow_note",
                ),
                pytest.param(
                    [generate_note_line(0, NoteTrackIndex.B.value)],
                    [NoteEventWithDefaults(tick=0, note=Note.B)],
                    [],
                    id="blue_note",
                ),
                pytest.param(
                    [generate_note_line(0, NoteTrackIndex.O.value)],
                    [NoteEventWithDefaults(tick=0, note=Note.O)],
                    [],
                    id="orange_note",
                ),
                pytest.param(
                    [
                        generate_note_line(0, NoteTrackIndex.G.value),
                        generate_note_line(0, NoteTrackIndex.TAP.value),
                    ],
                    [NoteEventWithDefaults(tick=0, note=Note.G, hopo_state=HOPOState.TAP)],
                    [],
                    id="tap_green_note",
                ),
                pytest.param(
                    [
                        generate_note_line(0, NoteTrackIndex.G.value),
                        generate_note_line(1, NoteTrackIndex.R.value),
                        generate_note_line(1, NoteTrackIndex.FORCED.value),
                    ],
                    [
                        NoteEventWithDefaults(tick=0, note=Note.G),
                        NoteEventWithDefaults(tick=1, note=Note.R, hopo_state=HOPOState.STRUM),
                    ],
                    [],
                    id="forced_red_note",
                ),
                pytest.param(
                    [
                        generate_note_line(0, NoteTrackIndex.G.value, sustain=100),
                    ],
                    [NoteEventWithDefaults(tick=0, note=Note.G, sustain=100)],
                    [],
                    id="green_with_sustain",
                ),
                pytest.param(
                    [
                        generate_note_line(0, NoteTrackIndex.G.value),
                        generate_note_line(0, NoteTrackIndex.R.value),
                    ],
                    [NoteEventWithDefaults(tick=0, note=Note.GR)],
                    [],
                    id="chord",
                ),
                pytest.param(
                    [
                        generate_note_line(0, NoteTrackIndex.G.value, sustain=100),
                        generate_note_line(0, NoteTrackIndex.R.value),
                    ],
                    [
                        NoteEventWithDefaults(
                            tick=0,
                            note=Note.GR,
                            sustain=(100, 0, None, None, None),
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
                        NoteEventWithDefaults(
                            tick=0,
                            note=Note.G,
                            sustain=100,
                            star_power_data=StarPowerData(0),
                        ),
                        NoteEventWithDefaults(
                            tick=2000,
                            note=Note.R,
                            sustain=50,
                            star_power_data=StarPowerData(1),
                        ),
                        NoteEventWithDefaults(
                            tick=2075,
                            note=Note.YB,
                            star_power_data=StarPowerData(1),
                        ),
                        NoteEventWithDefaults(tick=2100, note=Note.O, hopo_state=HOPOState.STRUM),
                        NoteEventWithDefaults(tick=2200, note=Note.B, hopo_state=HOPOState.TAP),
                        NoteEventWithDefaults(tick=2300, note=Note.OPEN),
                    ],
                    [
                        StarPowerEventWithDefaults(tick=0, sustain=100, init_end_tick=True),
                        StarPowerEventWithDefaults(tick=2000, sustain=80, init_end_tick=True),
                    ],
                    id="everything_together",
                ),
            ],
        )
        # TODO: This test currently tests parse_note_events_from_chart_lines by
        # proxy. Make its own tests instead.
        def test_integration(
            self, mocker, lines, want_note_events, want_star_power_events, minimal_tatter
        ):
            got = InstrumentTrack.from_chart_lines(
                pytest.defaults.instrument,
                pytest.defaults.difficulty,
                lambda: iter(lines),
                minimal_tatter,
            )
            assert got.instrument == pytest.defaults.instrument
            assert got.difficulty == pytest.defaults.difficulty
            assert got.star_power_events == want_star_power_events
            assert got.note_events == want_note_events

    class TestLastNoteEndTimestamp(object):
        @pytest.mark.parametrize(
            "note_events,want",
            [
                pytest.param(
                    [
                        NoteEventWithDefaults(end_timestamp=datetime.timedelta(seconds=0)),
                        NoteEventWithDefaults(end_timestamp=datetime.timedelta(seconds=1)),
                        NoteEventWithDefaults(end_timestamp=datetime.timedelta(seconds=0.5)),
                    ],
                    datetime.timedelta(seconds=1),
                ),
            ],
        )
        def test(self, bare_instrument_track, note_events, want):
            bare_instrument_track.note_events = note_events
            got = bare_instrument_track.last_note_end_timestamp
            assert got == want

        def test_empty(self, minimal_instrument_track):
            got = minimal_instrument_track.last_note_end_timestamp
            assert got is None


class TestNoteEvent(object):
    class TestInit(object):
        def test(self, mocker):
            want_end_timestamp = datetime.timedelta(1)
            want_star_power_data = StarPowerData(2)
            want_sustain = 3
            input_sustain = 4
            want_proximal_bpm_event_index = 5
            want_note = Note.ORANGE
            want_hopo_state = HOPOState.TAP

            spy_init = mocker.spy(Event, "__init__")

            mock_refine_sustain = mocker.patch.object(
                NoteEvent, "_refine_sustain", return_value=want_sustain
            )

            got = NoteEventWithDefaults(
                end_timestamp=want_end_timestamp,
                note=want_note,
                hopo_state=want_hopo_state,
                sustain=input_sustain,
                star_power_data=want_star_power_data,
                proximal_bpm_event_index=want_proximal_bpm_event_index,
            )

            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                pytest.defaults.tick,
                pytest.defaults.timestamp,
                want_proximal_bpm_event_index,
            )

            mock_refine_sustain.assert_called_once_with(input_sustain)

            assert got.end_timestamp == want_end_timestamp
            assert got.note == want_note
            assert got.sustain == want_sustain
            assert got.hopo_state == want_hopo_state
            assert got.star_power_data == want_star_power_data

    class TestRefineSustain(object):
        @pytest.mark.parametrize(
            "sustain, want",
            [
                pytest.param(
                    (None, None, None, None, None),
                    0,
                    id="all_none",
                ),
                pytest.param(
                    (0, 0, 0, 0, 0),
                    0,
                    id="all_zero",
                ),
                pytest.param(
                    (0, 0, None, None, None),
                    0,
                    id="all_none_or_zero",
                ),
                pytest.param(
                    (100, None, None, 100, None),
                    100,
                    id="all_the_same",
                ),
                pytest.param(
                    100,
                    100,
                    id="int_pass_through",
                ),
                pytest.param(
                    (100, 0, None, None, None),
                    (100, 0, None, None, None),
                    id="list_pass_through",
                ),
            ],
        )
        def test(self, sustain, want):
            got = NoteEvent._refine_sustain(sustain)
            assert got == want

    class TestComputeHOPOState(object):
        @pytest.mark.parametrize(
            "tick,note,is_tap,is_forced,previous,want",
            [
                pytest.param(
                    tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.SIXTEENTH,
                    ),
                    Note.R,
                    True,
                    True,
                    NoteEventWithDefaults(
                        tick=0,
                        note=Note.G,
                    ),
                    HOPOState.TAP,
                    id="forced_tap_note_is_a_tap",
                    # TODO: I don't actually know if this test case is accurate. Needs verifying.
                ),
                pytest.param(
                    0,
                    Note.G,
                    False,
                    False,
                    None,
                    HOPOState.STRUM,
                    id="first_note_is_strum",
                ),
                pytest.param(
                    tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.SIXTEENTH,
                    ),
                    Note.R,
                    False,
                    False,
                    NoteEventWithDefaults(
                        tick=0,
                        note=Note.G,
                    ),
                    HOPOState.HOPO,
                    id="16th_notes_are_hopos",
                ),
                pytest.param(
                    tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.TWELFTH,
                    ),
                    Note.R,
                    False,
                    False,
                    NoteEventWithDefaults(
                        tick=0,
                        note=Note.G,
                    ),
                    HOPOState.HOPO,
                    id="12th_notes_are_hopos",
                ),
                pytest.param(
                    tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.EIGHTH,
                    ),
                    Note.R,
                    False,
                    False,
                    NoteEventWithDefaults(
                        tick=0,
                        note=Note.G,
                    ),
                    HOPOState.STRUM,
                    id="8th_notes_are_strums",
                ),
                pytest.param(
                    tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.SIXTEENTH,
                    ),
                    Note.G,
                    False,
                    False,
                    NoteEventWithDefaults(
                        tick=0,
                        note=Note.G,
                    ),
                    HOPOState.STRUM,
                    id="consecutive_16th_notes_are_strums",
                ),
                pytest.param(
                    tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.TWELFTH,
                    ),
                    Note.G,
                    False,
                    False,
                    NoteEventWithDefaults(
                        tick=0,
                        note=Note.G,
                    ),
                    HOPOState.STRUM,
                    id="consecutive_12th_notes_are_strums",
                ),
                pytest.param(
                    tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.EIGHTH,
                    ),
                    Note.G,
                    False,
                    False,
                    NoteEventWithDefaults(
                        tick=0,
                        note=Note.G,
                    ),
                    HOPOState.STRUM,
                    id="consecutive_8th_notes_are_strums",
                ),
                pytest.param(
                    tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.TWELFTH,
                    ),
                    Note.G,
                    False,
                    False,
                    NoteEventWithDefaults(
                        tick=0,
                        note=Note.RY,
                    ),
                    HOPOState.HOPO,
                    id="pull_off_from_chord_is_hopo",
                ),
                pytest.param(
                    tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.TWELFTH,
                    ),
                    Note.RY,
                    False,
                    False,
                    NoteEventWithDefaults(
                        tick=0,
                        note=Note.G,
                    ),
                    HOPOState.STRUM,
                    id="hammer_on_to_chord_is_not_hopo",
                ),
                pytest.param(
                    tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.TWELFTH,
                    ),
                    Note.OPEN,
                    False,
                    False,
                    NoteEventWithDefaults(
                        tick=0,
                        note=Note.G,
                    ),
                    HOPOState.HOPO,
                    id="hammer_on_to_open_is_hopo",
                ),
                pytest.param(
                    tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.TWELFTH,
                    ),
                    Note.G,
                    False,
                    False,
                    NoteEventWithDefaults(
                        tick=0,
                        note=Note.OPEN,
                    ),
                    HOPOState.HOPO,
                    id="pull_off_to_open_is_hopo",
                ),
            ],
        )
        def test(self, tick, note, is_tap, is_forced, previous, want):
            got = NoteEvent._compute_hopo_state(
                pytest.defaults.resolution,
                tick,
                note,
                is_tap,
                is_forced,
                previous,
            )
            assert got == want

        def test_forced_first_note_raises(self):
            with pytest.raises(ValueError):
                _ = NoteEvent._compute_hopo_state(
                    pytest.defaults.resolution,
                    pytest.defaults.tick,
                    pytest.defaults.note,
                    False,
                    True,
                    None,
                )

    class TestComputeStarPowerData(object):
        @pytest.mark.parametrize(
            "tick,star_power_events,want_data,want_proximal_star_power_event_index",
            [
                pytest.param(
                    pytest.defaults.tick,
                    AlreadySortedImmutableSortedList([]),
                    None,
                    0,
                    id="empty_star_power_events",
                ),
                pytest.param(
                    0,
                    AlreadySortedImmutableSortedList(
                        [StarPowerEventWithDefaults(tick=100, sustain=10)]
                    ),
                    None,
                    0,
                    id="tick_not_in_event",
                ),
                pytest.param(
                    10,
                    AlreadySortedImmutableSortedList(
                        [
                            StarPowerEventWithDefaults(tick=0, sustain=10),
                            StarPowerEventWithDefaults(tick=100, sustain=10),
                        ]
                    ),
                    None,
                    1,
                    id="tick_not_in_event_with_noninitial_candidate_index",
                ),
                pytest.param(
                    0,
                    AlreadySortedImmutableSortedList(
                        [StarPowerEventWithDefaults(tick=0, sustain=10)]
                    ),
                    StarPowerData(
                        star_power_event_index=pytest.defaults.proximal_star_power_event_index
                    ),
                    0,
                    id="tick_in_event",
                ),
                pytest.param(
                    100,
                    AlreadySortedImmutableSortedList(
                        [
                            StarPowerEventWithDefaults(tick=0, sustain=10),
                            StarPowerEventWithDefaults(tick=100, sustain=10),
                        ]
                    ),
                    StarPowerData(star_power_event_index=1),
                    1,
                    id="tick_in_event_with_noninitial_candidate_index",
                ),
            ],
        )
        def test(
            self,
            tick,
            star_power_events,
            want_data,
            want_proximal_star_power_event_index,
        ):
            got_data, got_proximal_star_power_event_index = NoteEvent._compute_star_power_data(
                tick,
                star_power_events,
                proximal_star_power_event_index=pytest.defaults.proximal_star_power_event_index,
            )
            assert got_data == want_data
            assert got_proximal_star_power_event_index == want_proximal_star_power_event_index

        def test_proximal_star_power_event_index_after_last_event(self):
            with pytest.raises(ValueError):
                _, _ = NoteEvent._compute_star_power_data(
                    pytest.defaults.tick,
                    pytest.defaults.star_power_events,
                    proximal_star_power_event_index=len(pytest.defaults.star_power_events),
                )

    class TestLongestSustain(object):
        @pytest.mark.parametrize(
            "sustain,want",
            [
                pytest.param(100, 100),
                pytest.param((50, 100, None, 200, None), 200),
            ],
        )
        def test(self, bare_note_event, sustain, want):
            bare_note_event.sustain = sustain
            got = bare_note_event.longest_sustain
            assert got == want

        def test_raises(self, bare_note_event):
            bare_note_event.sustain = (None, None, None, None, None)
            with pytest.raises(ValueError):
                _ = bare_note_event.longest_sustain

    class TestEndTick(object):
        def test(self, mocker, bare_note_event):
            bare_note_event.tick = 100
            bare_note_event.sustain = 10
            got = bare_note_event.end_tick
            assert got == 110


class TestSpecialEvent(object):
    class TestInit(object):
        def test(self, mocker):
            want_proximal_bpm_event_index = 1
            want_sustain = 2
            spy_init = mocker.spy(Event, "__init__")

            got = SpecialEventWithDefaults(
                sustain=want_sustain, proximal_bpm_event_index=want_proximal_bpm_event_index
            )

            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                pytest.defaults.tick,
                pytest.defaults.timestamp,
                proximal_bpm_event_index=want_proximal_bpm_event_index,
            )
            assert got.sustain == want_sustain

    class TestFromChartLine(object):
        test_regex = r"^T (\d+?) V (.*?)$"

        def test(self, mocker, minimal_tatter):
            spy_init = mocker.spy(SpecialEvent, "__init__")

            line = f"T {pytest.defaults.tick} V {pytest.defaults.sustain}"
            _ = SpecialEvent.from_chart_line(line, None, minimal_tatter)

            minimal_tatter.spy.assert_called_once_with(
                pytest.defaults.tick, proximal_bpm_event_index=0
            )
            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                pytest.defaults.tick,
                pytest.defaults.timestamp,
                pytest.defaults.sustain,
                proximal_bpm_event_index=pytest.defaults.proximal_bpm_event_index,
            )

        def test_no_match(self, invalid_chart_line, minimal_tatter):
            with pytest.raises(RegexNotMatchError):
                _ = SpecialEvent.from_chart_line(invalid_chart_line, None, minimal_tatter)

        def setup_method(self):
            SpecialEvent._regex = self.test_regex
            SpecialEvent._regex_prog = re.compile(SpecialEvent._regex)

        def teardown_method(self):
            del SpecialEvent._regex
            del SpecialEvent._regex_prog

    class TestTickIsAfterEvent(object):
        @pytest.mark.parametrize(
            "tick,want",
            [
                pytest.param(0, False, id="before"),
                pytest.param(
                    100,
                    False,
                    id="coincide_with_start",
                ),
                pytest.param(110, True, id="coincide_with_end"),
                pytest.param(111, True, id="after"),
            ],
        )
        def test(self, tick, want):
            event = SpecialEventWithDefaults(tick=100, sustain=10)
            got = event.tick_is_after_event(tick)
            assert got == want

    class TestTickIsInEvent(object):
        @pytest.mark.parametrize(
            "tick,want",
            [
                pytest.param(0, False, id="before"),
                pytest.param(
                    100,
                    True,
                    id="coincide_with_start",
                ),
                pytest.param(110, False, id="coincide_with_end"),
                pytest.param(111, False, id="after"),
            ],
        )
        def test(self, tick, want):
            event = SpecialEventWithDefaults(tick=100, sustain=10)
            got = event.tick_is_in_event(tick)
            assert got == want


# TODO: Test regex?
class TestStarPowerEvent(object):
    pass
