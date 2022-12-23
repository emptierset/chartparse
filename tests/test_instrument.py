from __future__ import annotations

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
from tests.helpers.instrument import (
    InstrumentTrackWithDefaults,
    StarPowerEventWithDefaults,
    NoteEventWithDefaults,
    NoteEventParsedDataWithDefaults,
    SpecialEventWithDefaults,
    SpecialEventParsedDataWithDefaults,
)
from tests.helpers.lines import generate_note as generate_note_line
from tests.helpers.lines import generate_star_power as generate_star_power_line


class TestInstrumentTrack(object):
    class TestInit(object):
        def test(self, mocker, default_instrument_track):
            _ = InstrumentTrackWithDefaults()
            assert default_instrument_track.instrument == pytest.defaults.instrument
            assert default_instrument_track.difficulty == pytest.defaults.difficulty
            assert default_instrument_track.note_events == pytest.defaults.note_events
            assert default_instrument_track.star_power_events == pytest.defaults.star_power_events
            assert default_instrument_track.section_name == pytest.defaults.section_name

        @pytest.mark.parametrize("resolution", [0, -1])
        def test_non_positive_resolution(self, resolution):
            with pytest.raises(ValueError):
                _ = InstrumentTrackWithDefaults(resolution=0)

    class TestFromChartLines(object):
        def test(self, mocker, default_tatter):
            mock_parse_data = mocker.patch.object(
                InstrumentTrack,
                "_parse_data_from_chart_lines",
                return_value=(
                    pytest.defaults.note_event_parsed_datas,
                    pytest.defaults.star_power_event_parsed_datas,
                ),
            )
            mock_build_note_events = mocker.patch.object(
                InstrumentTrack,
                "_build_note_events_from_data",
                return_value=pytest.defaults.note_events,
            )
            mock_build_events = mocker.patch(
                "chartparse.track.build_events_from_data",
                return_value=pytest.defaults.star_power_events,
            )
            spy_init = mocker.spy(InstrumentTrack, "__init__")
            _ = InstrumentTrack.from_chart_lines(
                pytest.defaults.instrument,
                pytest.defaults.difficulty,
                pytest.invalid_chart_lines,
                default_tatter,
            )
            mock_parse_data.assert_called_once_with(pytest.invalid_chart_lines)
            mock_build_note_events.assert_called_once_with(
                pytest.defaults.note_event_parsed_datas,
                pytest.defaults.star_power_events,
                default_tatter,
            )
            mock_build_events.assert_called_once_with(
                pytest.defaults.star_power_event_parsed_datas,
                StarPowerEvent.from_parsed_data,
                default_tatter,
            )
            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                pytest.defaults.resolution,
                pytest.defaults.instrument,
                pytest.defaults.difficulty,
                pytest.defaults.note_events,
                pytest.defaults.star_power_events,
            )

        def NoteEventWithDefaultsPlus(**kwargs):
            return NoteEventWithDefaults(
                proximal_bpm_event_index=pytest.defaults.default_tatter_index,
                timestamp=pytest.defaults.default_tatter_timestamp,
                end_timestamp=pytest.defaults.default_tatter_timestamp,
                **kwargs,
            )

        def StarPowerEventWithDefaultsPlus(**kwargs):
            return StarPowerEventWithDefaults(
                proximal_bpm_event_index=pytest.defaults.default_tatter_index,
                timestamp=pytest.defaults.default_tatter_timestamp,
                **kwargs,
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
                    [NoteEventWithDefaultsPlus(tick=0, note=Note.OPEN)],
                    [],
                    id="open_note",
                ),
                pytest.param(
                    [generate_note_line(0, NoteTrackIndex.G.value)],
                    [NoteEventWithDefaultsPlus(tick=0, note=Note.G)],
                    [],
                    id="green_note",
                ),
                pytest.param(
                    [generate_note_line(0, NoteTrackIndex.R.value)],
                    [NoteEventWithDefaultsPlus(tick=0, note=Note.R)],
                    [],
                    id="red_note",
                ),
                pytest.param(
                    [generate_note_line(0, NoteTrackIndex.Y.value)],
                    [NoteEventWithDefaultsPlus(tick=0, note=Note.Y)],
                    [],
                    id="yellow_note",
                ),
                pytest.param(
                    [generate_note_line(0, NoteTrackIndex.B.value)],
                    [NoteEventWithDefaultsPlus(tick=0, note=Note.B)],
                    [],
                    id="blue_note",
                ),
                pytest.param(
                    [generate_note_line(0, NoteTrackIndex.O.value)],
                    [NoteEventWithDefaultsPlus(tick=0, note=Note.O)],
                    [],
                    id="orange_note",
                ),
                pytest.param(
                    [
                        generate_note_line(0, NoteTrackIndex.G.value),
                        generate_note_line(0, NoteTrackIndex.TAP.value),
                    ],
                    [
                        NoteEventWithDefaultsPlus(
                            tick=0,
                            note=Note.G,
                            hopo_state=HOPOState.TAP,
                        )
                    ],
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
                        NoteEventWithDefaultsPlus(
                            tick=0,
                            note=Note.G,
                        ),
                        NoteEventWithDefaultsPlus(
                            tick=1,
                            note=Note.R,
                            hopo_state=HOPOState.STRUM,
                        ),
                    ],
                    [],
                    id="forced_red_note",
                ),
                pytest.param(
                    [
                        generate_note_line(0, NoteTrackIndex.G.value, sustain=100),
                    ],
                    [NoteEventWithDefaultsPlus(tick=0, note=Note.G, sustain=100)],
                    [],
                    id="green_with_sustain",
                ),
                pytest.param(
                    [
                        generate_note_line(0, NoteTrackIndex.G.value),
                        generate_note_line(0, NoteTrackIndex.R.value),
                    ],
                    [NoteEventWithDefaultsPlus(tick=0, note=Note.GR)],
                    [],
                    id="chord",
                ),
                pytest.param(
                    [
                        generate_note_line(0, NoteTrackIndex.G.value, sustain=100),
                        generate_note_line(0, NoteTrackIndex.R.value),
                    ],
                    [
                        NoteEventWithDefaultsPlus(
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
                    [StarPowerEventWithDefaultsPlus(tick=0, sustain=100)],
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
                        NoteEventWithDefaultsPlus(
                            tick=0,
                            note=Note.G,
                            sustain=100,
                            star_power_data=StarPowerData(0),
                        ),
                        NoteEventWithDefaultsPlus(
                            tick=2000,
                            note=Note.R,
                            sustain=50,
                            star_power_data=StarPowerData(1),
                        ),
                        NoteEventWithDefaultsPlus(
                            tick=2075,
                            note=Note.YB,
                            star_power_data=StarPowerData(1),
                        ),
                        NoteEventWithDefaultsPlus(
                            tick=2100,
                            note=Note.O,
                            hopo_state=HOPOState.STRUM,
                        ),
                        NoteEventWithDefaultsPlus(
                            tick=2200,
                            note=Note.B,
                            hopo_state=HOPOState.TAP,
                        ),
                        NoteEventWithDefaultsPlus(
                            tick=2300,
                            note=Note.OPEN,
                        ),
                    ],
                    [
                        StarPowerEventWithDefaultsPlus(
                            tick=0,
                            sustain=100,
                            init_end_tick=True,
                        ),
                        StarPowerEventWithDefaultsPlus(
                            tick=2000,
                            sustain=80,
                            init_end_tick=True,
                        ),
                    ],
                    id="everything_together",
                ),
            ],
        )
        def test_integration(
            self, mocker, lines, want_note_events, want_star_power_events, default_tatter
        ):
            got = InstrumentTrack.from_chart_lines(
                pytest.defaults.instrument,
                pytest.defaults.difficulty,
                lines,
                default_tatter,
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

    class TestFromParsedData(object):
        def test(self, mocker, default_tatter):
            want_hopo_state = HOPOState.STRUM
            mock_compute_hopo_state = mocker.patch.object(
                NoteEvent, "_compute_hopo_state", return_value=want_hopo_state
            )

            want_star_power_data = StarPowerData(5)
            want_star_power_event_index = 11
            mock_compute_star_power_data = mocker.patch.object(
                NoteEvent,
                "_compute_star_power_data",
                return_value=(want_star_power_data, want_star_power_event_index),
            )

            want_proximal_bpm_event_index = 22
            unrefined_sustain = [100, None, None, None, None]
            data = NoteEventParsedDataWithDefaults(sustain=unrefined_sustain)

            spy_init = mocker.spy(NoteEvent, "__init__")

            _event, _bpm_event_index, _star_power_event_index = NoteEvent.from_parsed_data(
                data,
                None,
                pytest.defaults.star_power_events,
                default_tatter,
                proximal_bpm_event_index=want_proximal_bpm_event_index,
                star_power_event_index=want_star_power_event_index,
            )

            default_tatter.spy.assert_has_calls(
                [
                    unittest.mock.call(
                        pytest.defaults.tick,
                        proximal_bpm_event_index=want_proximal_bpm_event_index,
                    ),
                    unittest.mock.call(
                        pytest.defaults.tick + 100,
                        proximal_bpm_event_index=pytest.defaults.default_tatter_index,
                    ),
                ],
            )

            mock_compute_hopo_state.assert_called_once_with(
                default_tatter.resolution, data.tick, pytest.defaults.note, False, False, None
            )

            mock_compute_star_power_data.assert_called_once_with(
                pytest.defaults.tick,
                pytest.defaults.star_power_events,
                proximal_star_power_event_index=want_star_power_event_index,
            )

            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                pytest.defaults.tick,
                pytest.defaults.default_tatter_timestamp,
                pytest.defaults.default_tatter_timestamp,
                pytest.defaults.note,
                want_hopo_state,
                sustain=data.immutable_sustain,
                proximal_bpm_event_index=pytest.defaults.default_tatter_index,
                star_power_data=want_star_power_data,
            )

        def test_sustain_none(
            self,
            mocker,
            default_tatter,
            minimal_compute_hopo_state_mock,
            minimal_compute_star_power_data_mock,
        ):
            with pytest.raises(ValueError):
                _ = NoteEvent.from_parsed_data(
                    NoteEventParsedDataWithDefaults(sustain=None),
                    None,
                    pytest.defaults.star_power_events,
                    default_tatter,
                )

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

    class TestParsedData(object):
        class TestFromChartLine(object):
            test_regex = r"^T (\d+?) I (\d+?) S (\d+?)$"

            tick = 4
            sustain_ticks = 3

            @pytest.mark.parametrize(
                (
                    "note_track_index,"
                    "sustain_ticks,"
                    "want_note_array,"
                    "want_sustain,"
                    "want_is_forced,"
                    "want_is_tap"
                ),
                [
                    pytest.param(
                        NoteTrackIndex.YELLOW,
                        sustain_ticks,
                        bytearray((0, 0, 1, 0, 0)),
                        [None, None, sustain_ticks, None, None],
                        False,
                        False,
                        id="normal_note",
                    ),
                    pytest.param(
                        NoteTrackIndex.OPEN,
                        sustain_ticks,
                        bytearray((0, 0, 0, 0, 0)),
                        sustain_ticks,
                        False,
                        False,
                        id="open_note",
                    ),
                    pytest.param(
                        NoteTrackIndex.FORCED,
                        0,
                        bytearray((0, 0, 0, 0, 0)),
                        None,
                        True,
                        False,
                        id="forced_note",
                    ),
                    pytest.param(
                        NoteTrackIndex.TAP,
                        0,
                        bytearray((0, 0, 0, 0, 0)),
                        None,
                        False,
                        True,
                        id="tap_note",
                    ),
                ],
            )
            def test(
                self,
                note_track_index,
                sustain_ticks,
                want_note_array,
                want_sustain,
                want_is_forced,
                want_is_tap,
            ):
                got = NoteEvent.ParsedData.from_chart_line(
                    f"T {self.tick} I {note_track_index.value} S {sustain_ticks}"
                )
                want = NoteEvent.ParsedData(
                    tick=self.tick,
                    note_array=want_note_array,
                    sustain=want_sustain,
                    is_forced=want_is_forced,
                    is_tap=want_is_tap,
                )
                assert got.tick == want.tick
                assert got.note_array == want.note_array
                assert got.sustain == want.sustain
                assert got.is_forced == want.is_forced
                assert got.is_tap == want.is_tap

            def test_no_match(self, invalid_chart_line, default_tatter):
                with pytest.raises(RegexNotMatchError):
                    _ = NoteEvent.ParsedData.from_chart_line(invalid_chart_line)

            def test_unhandled_note_track_index(self, mocker, caplog):
                invalid_instrument_note_track_index = 8
                with pytest.raises(ValueError):
                    _ = NoteEvent.ParsedData.from_chart_line(
                        f"T {pytest.defaults.tick} "
                        f"I {invalid_instrument_note_track_index} "
                        f"S {pytest.defaults.sustain}"
                    )

            def setup_method(self):
                NoteEvent.ParsedData._regex = self.test_regex
                NoteEvent.ParsedData._regex_prog = re.compile(NoteEvent.ParsedData._regex)

            def teardown_method(self):
                del NoteEvent.ParsedData._regex
                del NoteEvent.ParsedData._regex_prog

        class TestComplexSustain(object):
            @pytest.mark.parametrize(
                "sustain,want",
                [
                    pytest.param(None, None, id="None"),
                    pytest.param(1, 1, id="int"),
                    pytest.param(
                        [None, 1, None, None, None], (None, 1, None, None, None), id="list"
                    ),
                ],
            )
            def test(self, bare_note_event_parsed_data, sustain, want):
                bare_note_event_parsed_data.sustain = sustain
                got = bare_note_event_parsed_data.immutable_sustain
                assert got == want

        class TestCoalesced(object):
            @pytest.mark.parametrize(
                "sustain_dest,sustain_src,want",
                [
                    pytest.param(100, None, 100, id="other_None"),
                    pytest.param(None, 100, 100, id="self_None"),
                    pytest.param(
                        [100, None, None, None, None],
                        [None, 100, None, None, None],
                        [100, 100, None, None, None],
                        id="both_list",
                    ),
                ],
            )
            def test_sustain(self, sustain_dest, sustain_src, want):
                dest = NoteEventParsedDataWithDefaults(sustain=sustain_dest)
                src = NoteEventParsedDataWithDefaults(sustain=sustain_src)
                got = NoteEvent.ParsedData.coalesced(dest, src).sustain
                assert got == want

            @pytest.mark.parametrize(
                "sustain_dest,sustain_src",
                [
                    pytest.param(100, [100, None, None, None, None], id="self_open"),
                    pytest.param([100, None, None, None, None], 100, id="other_open"),
                ],
            )
            def test_sustain_merge_open_raises(self, sustain_dest, sustain_src):
                with pytest.raises(ValueError):
                    dest = NoteEventParsedDataWithDefaults(sustain=sustain_dest)
                    src = NoteEventParsedDataWithDefaults(sustain=sustain_src)
                    _ = NoteEvent.ParsedData.coalesced(dest, src)

            def test_note_array(self):
                dest = NoteEventParsedDataWithDefaults(note_array=bytearray((1, 0, 0, 0, 0)))
                src = NoteEventParsedDataWithDefaults(note_array=bytearray((0, 1, 0, 0, 0)))
                got = NoteEvent.ParsedData.coalesced(dest, src).note_array
                want = bytearray((1, 1, 0, 0, 0))
                assert got == want

            @pytest.mark.parametrize(
                "is_forced_dest,is_forced_src,want",
                [
                    pytest.param(True, False, True, id="self_forced"),
                    pytest.param(False, True, True, id="self_forced"),
                    pytest.param(False, False, False, id="neither_forced"),
                    pytest.param(True, True, True, id="both_forced"),
                ],
            )
            def test_is_forced(self, is_forced_dest, is_forced_src, want):
                dest = NoteEventParsedDataWithDefaults(is_forced=is_forced_dest)
                src = NoteEventParsedDataWithDefaults(is_forced=is_forced_src)
                got = NoteEvent.ParsedData.coalesced(dest, src).is_forced
                assert got == want

            @pytest.mark.parametrize(
                "is_tap_dest,is_tap_src,want",
                [
                    pytest.param(True, False, True, id="self_tap"),
                    pytest.param(False, True, True, id="self_tap"),
                    pytest.param(False, False, False, id="neither_tap"),
                    pytest.param(True, True, True, id="both_tap"),
                ],
            )
            def test_is_tap(self, is_tap_dest, is_tap_src, want):
                dest = NoteEventParsedDataWithDefaults(is_tap=is_tap_dest)
                src = NoteEventParsedDataWithDefaults(is_tap=is_tap_src)
                got = NoteEvent.ParsedData.coalesced(dest, src).is_tap
                assert got == want

    class TestComputeStarPowerData(object):
        @pytest.mark.parametrize(
            "tick,star_power_events,want_data,want_proximal_star_power_event_index",
            [
                pytest.param(
                    pytest.defaults.tick,
                    [],
                    None,
                    0,
                    id="empty_star_power_events",
                ),
                pytest.param(
                    0,
                    [StarPowerEventWithDefaults(tick=100, sustain=10)],
                    None,
                    0,
                    id="tick_not_in_event",
                ),
                pytest.param(
                    10,
                    [
                        StarPowerEventWithDefaults(tick=0, sustain=10),
                        StarPowerEventWithDefaults(tick=100, sustain=10),
                    ],
                    None,
                    1,
                    id="tick_not_in_event_with_noninitial_candidate_index",
                ),
                pytest.param(
                    0,
                    [StarPowerEventWithDefaults(tick=0, sustain=10)],
                    StarPowerData(
                        star_power_event_index=pytest.defaults.proximal_star_power_event_index
                    ),
                    0,
                    id="tick_in_event",
                ),
                pytest.param(
                    100,
                    [
                        StarPowerEventWithDefaults(tick=0, sustain=10),
                        StarPowerEventWithDefaults(tick=100, sustain=10),
                    ],
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
        def test(self, mocker, bare_note_event, sustain, want):
            bare_note_event.sustain = 100
            spy = mocker.spy(NoteEvent, "_longest_sustain")
            bare_note_event.longest_sustain
            spy.assert_called_once_with(100)

        @pytest.mark.parametrize(
            "sustain,want",
            [
                pytest.param(100, 100),
                pytest.param((50, 100, None, 200, None), 200),
            ],
        )
        def test_impl(self, sustain, want):
            got = NoteEvent._longest_sustain(sustain)
            assert got == want

        def test_impl_all_none(self):
            with pytest.raises(ValueError):
                _ = NoteEvent._longest_sustain((None, None, None, None, None))

    class TestEndTick(object):
        def test_wrapper(self, mocker, bare_note_event):
            bare_note_event.tick = 100
            bare_note_event.sustain = 10
            spy = mocker.spy(NoteEvent, "_end_tick")
            bare_note_event.end_tick
            assert spy.called_once_with(100, 10)

        def test_impl(self):
            got = NoteEvent._end_tick(100, 10)
            want = 110
            assert got == want


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

    class TestFromParsedData(object):
        @pytest.mark.parametrize(
            "prev_event",
            [
                pytest.param(None, id="prev_event_none"),
                pytest.param(
                    SpecialEventWithDefaults(proximal_bpm_event_index=1), id="prev_event_present"
                ),
            ],
        )
        def test(self, mocker, default_tatter, prev_event):
            spy_init = mocker.spy(SpecialEvent, "__init__")

            _ = SpecialEvent.from_parsed_data(
                SpecialEventParsedDataWithDefaults(), prev_event, default_tatter
            )

            default_tatter.spy.assert_called_once_with(
                pytest.defaults.tick,
                proximal_bpm_event_index=prev_event._proximal_bpm_event_index if prev_event else 0,
            )
            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                pytest.defaults.tick,
                pytest.defaults.default_tatter_timestamp,
                pytest.defaults.sustain,
                proximal_bpm_event_index=pytest.defaults.default_tatter_index,
            )

    class TestParsedData(object):
        class TestFromChartLine(object):
            test_regex = r"^T (\d+?) V (.*?)$"

            def test(self, mocker):
                got = SpecialEvent.ParsedData.from_chart_line(
                    f"T {pytest.defaults.tick} V {pytest.defaults.sustain}"
                )
                assert got.tick == pytest.defaults.tick
                assert got.sustain == pytest.defaults.sustain

            def test_no_match(self, invalid_chart_line, default_tatter):
                with pytest.raises(RegexNotMatchError):
                    _ = SpecialEvent.ParsedData.from_chart_line(invalid_chart_line)

            def setup_method(self):
                SpecialEvent.ParsedData._regex = self.test_regex
                SpecialEvent.ParsedData._regex_prog = re.compile(SpecialEvent.ParsedData._regex)

            def teardown_method(self):
                del SpecialEvent.ParsedData._regex
                del SpecialEvent.ParsedData._regex_prog

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
