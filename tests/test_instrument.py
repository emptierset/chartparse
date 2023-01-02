from __future__ import annotations

import datetime
import pytest
import re
import unittest.mock

import chartparse.instrument
from chartparse.exceptions import RegexNotMatchError
from chartparse.instrument import (
    InstrumentTrack,
    StarPowerEvent,
    NoteEvent,
    TrackEvent,
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
    TrackEventWithDefaults,
    TrackEventParsedDataWithDefaults,
)
from tests.helpers.lines import generate_note as generate_note_line
from tests.helpers.lines import generate_star_power as generate_star_power_line
from tests.helpers.lines import generate_track as generate_track_line


class TestNote(object):
    class TestFromParsedData(object):
        @pytest.mark.parametrize(
            "data,want",
            [
                pytest.param(
                    NoteEventParsedDataWithDefaults(note_track_index=NoteTrackIndex.G),
                    Note.G,
                    id="single_data",
                ),
                pytest.param(
                    [
                        NoteEventParsedDataWithDefaults(note_track_index=NoteTrackIndex.G),
                        NoteEventParsedDataWithDefaults(note_track_index=NoteTrackIndex.R),
                    ],
                    Note.GR,
                    id="multiple_data",
                ),
            ],
        )
        def test(self, data, want):
            got = Note.from_parsed_data(data)
            assert got == want


class TestNoteTrackIndex(object):
    class TestTotalOrdering(object):
        assert NoteTrackIndex.G < NoteTrackIndex.R
        assert NoteTrackIndex.G <= NoteTrackIndex.R
        assert NoteTrackIndex.R >= NoteTrackIndex.G
        assert NoteTrackIndex.R > NoteTrackIndex.G
        assert NoteTrackIndex.G == NoteTrackIndex.G
        assert NoteTrackIndex.G != NoteTrackIndex.R


class TestComplexSustainFromParsedDatas(object):
    @pytest.mark.parametrize(
        "datas, want",
        [
            pytest.param(
                [
                    NoteEventParsedDataWithDefaults(
                        note_track_index=NoteTrackIndex.OPEN, sustain=100
                    )
                ],
                100,
                id="open",
            ),
            pytest.param(
                [NoteEventParsedDataWithDefaults(note_track_index=NoteTrackIndex.TAP)],
                0,
                id="no_note_data",
            ),
            pytest.param(
                [
                    NoteEventParsedDataWithDefaults(
                        note_track_index=NoteTrackIndex.G, sustain=100
                    ),
                    NoteEventParsedDataWithDefaults(
                        note_track_index=NoteTrackIndex.R, sustain=100
                    ),
                ],
                100,
                id="same_length_notes_return_int_sustain",
            ),
            pytest.param(
                [
                    NoteEventParsedDataWithDefaults(
                        note_track_index=NoteTrackIndex.G, sustain=100
                    ),
                    NoteEventParsedDataWithDefaults(note_track_index=NoteTrackIndex.R, sustain=50),
                ],
                (100, 50, None, None, None),
                id="variable_length_notes_return_tuple_sustain",
            ),
        ],
    )
    def test(self, datas, want):
        got = chartparse.instrument.complex_sustain_from_parsed_datas(datas)
        assert got == want


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
                    pytest.defaults.track_event_parsed_datas,
                ),
            )
            mock_build_note_events = mocker.patch.object(
                InstrumentTrack,
                "_build_note_events_from_data",
                return_value=pytest.defaults.note_events,
            )
            mock_build_events = mocker.patch(
                "chartparse.track.build_events_from_data",
                side_effect=[
                    pytest.defaults.star_power_events,
                    pytest.defaults.track_events,
                ],
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
            mock_build_events.assert_has_calls(
                [
                    unittest.mock.call(
                        pytest.defaults.star_power_event_parsed_datas,
                        StarPowerEvent.from_parsed_data,
                        default_tatter,
                    ),
                    unittest.mock.call(
                        pytest.defaults.track_event_parsed_datas,
                        TrackEvent.from_parsed_data,
                        default_tatter,
                    ),
                ],
            )
            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                pytest.defaults.resolution,
                pytest.defaults.instrument,
                pytest.defaults.difficulty,
                pytest.defaults.note_events,
                pytest.defaults.star_power_events,
                pytest.defaults.track_events,
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
                            star_power_data=StarPowerData(star_power_event_index=0),
                        ),
                        NoteEventWithDefaultsPlus(
                            tick=2000,
                            note=Note.R,
                            sustain=50,
                            star_power_data=StarPowerData(star_power_event_index=1),
                        ),
                        NoteEventWithDefaultsPlus(
                            tick=2075,
                            note=Note.YB,
                            star_power_data=StarPowerData(star_power_event_index=1),
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
    class TestFromParsedData(object):
        @pytest.mark.parametrize(
            (
                "data,"
                "want_tick,"
                "want_sustain,"
                "want_note,"
                "want_hopo_state,"
                "want_star_power_data,"
                "want_star_power_event_index,"
                "want_proximal_bpm_event_index"
            ),
            [
                pytest.param(
                    NoteEventParsedDataWithDefaults(
                        tick=1, note_track_index=NoteTrackIndex.G, sustain=100
                    ),
                    1,
                    100,
                    Note.G,
                    HOPOState.STRUM,
                    StarPowerData(star_power_event_index=5),
                    11,
                    22,
                    id="single_data",
                ),
                pytest.param(
                    [
                        NoteEventParsedDataWithDefaults(
                            tick=1, note_track_index=NoteTrackIndex.G, sustain=100
                        ),
                        NoteEventParsedDataWithDefaults(
                            tick=1, note_track_index=NoteTrackIndex.R, sustain=50
                        ),
                    ],
                    1,
                    (100, 50, None, None, None),
                    Note.GR,
                    HOPOState.STRUM,
                    StarPowerData(star_power_event_index=5),
                    11,
                    22,
                    id="multiple_data",
                ),
            ],
        )
        def test(
            self,
            mocker,
            default_tatter,
            data,
            want_tick,
            want_sustain,
            want_note,
            want_hopo_state,
            want_star_power_data,
            want_star_power_event_index,
            want_proximal_bpm_event_index,
        ):
            mock_compute_hopo_state = mocker.patch.object(
                NoteEvent, "_compute_hopo_state", return_value=want_hopo_state
            )

            mock_compute_star_power_data = mocker.patch.object(
                NoteEvent,
                "_compute_star_power_data",
                return_value=(want_star_power_data, want_star_power_event_index),
            )

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
                        want_tick,
                        proximal_bpm_event_index=want_proximal_bpm_event_index,
                    ),
                    unittest.mock.call(
                        # technically tick+sustain, but annoying because it requires mocking or
                        # calling _end_tick.
                        unittest.mock.ANY,
                        proximal_bpm_event_index=pytest.defaults.default_tatter_index,
                    ),
                ],
            )

            mock_compute_hopo_state.assert_called_once_with(
                default_tatter.resolution,
                want_tick,
                want_note,
                False,
                False,
                None,
            )

            mock_compute_star_power_data.assert_called_once_with(
                want_tick,
                pytest.defaults.star_power_events,
                proximal_star_power_event_index=want_star_power_event_index,
            )

            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                tick=want_tick,
                timestamp=pytest.defaults.default_tatter_timestamp,
                end_timestamp=pytest.defaults.default_tatter_timestamp,
                note=want_note,
                hopo_state=want_hopo_state,
                sustain=want_sustain,
                _proximal_bpm_event_index=pytest.defaults.default_tatter_index,
                star_power_data=want_star_power_data,
            )

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
                ("want_note_track_index," "want_sustain,"),
                [
                    pytest.param(
                        NoteTrackIndex.YELLOW,
                        sustain_ticks,
                        id="normal_note",
                    ),
                    pytest.param(
                        NoteTrackIndex.OPEN,
                        sustain_ticks,
                        id="open_note",
                    ),
                    pytest.param(
                        NoteTrackIndex.FORCED,
                        0,
                        id="forced_note",
                    ),
                    pytest.param(
                        NoteTrackIndex.TAP,
                        0,
                        id="tap_note",
                    ),
                ],
            )
            def test(
                self,
                want_note_track_index,
                want_sustain,
            ):
                got = NoteEvent.ParsedData.from_chart_line(
                    f"T {self.tick} I {want_note_track_index.value} S {want_sustain}"
                )
                want = NoteEvent.ParsedData(
                    tick=self.tick,
                    note_track_index=want_note_track_index,
                    sustain=want_sustain,
                )
                assert got == want

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
                        (None, 1, None, None, None), (None, 1, None, None, None), id="list"
                    ),
                ],
            )
            def test(self, bare_note_event_parsed_data, sustain, want):
                bare_note_event_parsed_data.__dict__["sustain"] = sustain
                got = bare_note_event_parsed_data.sustain
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
            object.__setattr__(bare_note_event, "sustain", 100)
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
            object.__setattr__(bare_note_event, "tick", 100)
            object.__setattr__(bare_note_event, "sustain", 10)
            spy = mocker.spy(NoteEvent, "_end_tick")
            bare_note_event.end_tick
            assert spy.called_once_with(100, 10)

        def test_impl(self):
            got = NoteEvent._end_tick(100, 10)
            want = 110
            assert got == want


class TestSpecialEvent(object):
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
                tick=pytest.defaults.tick,
                timestamp=pytest.defaults.default_tatter_timestamp,
                sustain=pytest.defaults.sustain,
                _proximal_bpm_event_index=pytest.defaults.default_tatter_index,
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

    class TestTickIsDuringEvent(object):
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
            got = event.tick_is_during_event(tick)
            assert got == want


# TODO: Test regex?
class TestStarPowerEvent(object):
    pass


class TestTrackEvent(object):
    class TestFromParsedData(object):
        @pytest.mark.parametrize(
            "prev_event",
            [
                pytest.param(
                    None,
                    id="prev_event_none",
                ),
                pytest.param(
                    TrackEventWithDefaults(proximal_bpm_event_index=1),
                    id="prev_event_present",
                ),
            ],
        )
        def test(self, mocker, default_tatter, prev_event):
            spy_init = mocker.spy(TrackEvent, "__init__")

            _ = TrackEvent.from_parsed_data(
                TrackEventParsedDataWithDefaults(),
                prev_event,
                default_tatter,
            )

            default_tatter.spy.assert_called_once_with(
                pytest.defaults.tick,
                proximal_bpm_event_index=prev_event._proximal_bpm_event_index if prev_event else 0,
            )

            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                tick=pytest.defaults.tick,
                timestamp=pytest.defaults.default_tatter_timestamp,
                value=pytest.defaults.track_event_value,
                _proximal_bpm_event_index=pytest.defaults.default_tatter_index,
            )

    class TestParsedData(object):
        class TestFromChartLine(object):
            def test(self, mocker):
                line = generate_track_line(pytest.defaults.tick, pytest.defaults.track_event_value)
                got = TrackEvent.ParsedData.from_chart_line(line)
                assert got.tick == pytest.defaults.tick
                assert got.value == pytest.defaults.track_event_value

            def test_no_match(self, invalid_chart_line):
                with pytest.raises(RegexNotMatchError):
                    _ = TrackEvent.ParsedData.from_chart_line(invalid_chart_line)
