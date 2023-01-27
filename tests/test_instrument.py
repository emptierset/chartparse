from __future__ import annotations

import re
import unittest.mock
from datetime import timedelta

import pytest

import chartparse.instrument
import tests.helpers.tick
from chartparse.exceptions import RegexNotMatchError
from chartparse.instrument import (
    Difficulty,
    HOPOState,
    Instrument,
    InstrumentTrack,
    Note,
    NoteEvent,
    NoteTrackIndex,
    SpecialEvent,
    StarPowerData,
    StarPowerEvent,
    TrackEvent,
)
from chartparse.tick import NoteDuration
from tests.helpers import defaults, testcase, unsafe
from tests.helpers.instrument import (
    InstrumentTrackWithDefaults,
    NoteEventParsedDataWithDefaults,
    NoteEventWithDefaults,
    SpecialEventParsedDataWithDefaults,
    SpecialEventWithDefaults,
    StarPowerEventWithDefaults,
    TrackEventParsedDataWithDefaults,
    TrackEventWithDefaults,
)
from tests.helpers.lines import generate_note as generate_note_line
from tests.helpers.lines import generate_star_power as generate_star_power_line
from tests.helpers.lines import generate_track as generate_track_line


class TestNote(object):
    class TestFromParsedData(object):
        @testcase.parametrize(
            ["data", "want"],
            [
                testcase.new(
                    "single_data",
                    data=NoteEventParsedDataWithDefaults(note_track_index=NoteTrackIndex.G),
                    want=Note.G,
                ),
                testcase.new(
                    "multiple_data",
                    data=[
                        NoteEventParsedDataWithDefaults(note_track_index=NoteTrackIndex.G),
                        NoteEventParsedDataWithDefaults(note_track_index=NoteTrackIndex.R),
                    ],
                    want=Note.GR,
                ),
            ],
        )
        def test(self, data, want):
            got = Note.from_parsed_data(data)
            assert got == want


class TestNoteTrackIndex(object):
    class TestOrderability(object):
        def test(self):
            assert NoteTrackIndex.G < NoteTrackIndex.R
            assert NoteTrackIndex.G <= NoteTrackIndex.R
            assert NoteTrackIndex.R >= NoteTrackIndex.G
            assert NoteTrackIndex.R > NoteTrackIndex.G


class TestComplexSustainFromParsedDatas(object):
    @testcase.parametrize(
        ["datas", "want"],
        [
            testcase.new(
                "open",
                datas=[
                    NoteEventParsedDataWithDefaults(
                        note_track_index=NoteTrackIndex.OPEN, sustain=100
                    )
                ],
                want=100,
            ),
            testcase.new(
                "no_note_data",
                datas=[NoteEventParsedDataWithDefaults(note_track_index=NoteTrackIndex.TAP)],
                want=0,
            ),
            testcase.new(
                "same_length_notes_return_int_sustain",
                datas=[
                    NoteEventParsedDataWithDefaults(
                        note_track_index=NoteTrackIndex.G, sustain=100
                    ),
                    NoteEventParsedDataWithDefaults(
                        note_track_index=NoteTrackIndex.R, sustain=100
                    ),
                ],
                want=100,
            ),
            testcase.new(
                "variable_length_notes_return_tuple_sustain",
                datas=[
                    NoteEventParsedDataWithDefaults(
                        note_track_index=NoteTrackIndex.G, sustain=100
                    ),
                    NoteEventParsedDataWithDefaults(note_track_index=NoteTrackIndex.R, sustain=50),
                ],
                want=(100, 50, None, None, None),
            ),
        ],
    )
    def test(self, datas, want):
        got = chartparse.instrument.complex_sustain_from_parsed_datas(datas)
        assert got == want


class TestInstrumentTrack(object):
    class TestSectionName(object):
        @testcase.parametrize(
            ["instrument", "difficulty", "want"],
            [
                testcase.new_anonymous(
                    instrument=Instrument.GUITAR,
                    difficulty=Difficulty.EXPERT,
                    want="ExpertSingle",
                ),
                testcase.new_anonymous(
                    instrument=Instrument.BASS,
                    difficulty=Difficulty.EASY,
                    want="EasyDoubleBass",
                ),
            ],
        )
        def test(self, instrument, difficulty, want):
            track = InstrumentTrackWithDefaults(instrument=instrument, difficulty=difficulty)
            got = track.section_name
            assert got == want

    class TestFromChartLines(object):
        def test(self, mocker, minimal_bpm_events):
            mock_parse_data = mocker.patch.object(
                InstrumentTrack,
                "_parse_data_from_chart_lines",
                return_value=(
                    [defaults.note_event_parsed_data],
                    [defaults.star_power_event],
                    [defaults.track_event_parsed_data],
                ),
            )
            mock_build_note_events = mocker.patch.object(
                InstrumentTrack,
                "_build_note_events_from_data",
                return_value=[defaults.note_event],
            )
            mock_build_events = mocker.patch(
                "chartparse.track.build_events_from_data",
                side_effect=[
                    [defaults.star_power_event],
                    [defaults.track_event],
                ],
            )
            spy_init = mocker.spy(InstrumentTrack, "__init__")
            _ = InstrumentTrack.from_chart_lines(
                defaults.instrument,
                defaults.difficulty,
                defaults.invalid_chart_lines,
                minimal_bpm_events,
            )
            mock_parse_data.assert_called_once_with(defaults.invalid_chart_lines)
            mock_build_note_events.assert_called_once_with(
                [defaults.note_event_parsed_data],
                [defaults.star_power_event],
                minimal_bpm_events,
            )
            mock_build_events.assert_has_calls(
                [
                    unittest.mock.call(
                        [defaults.star_power_event],
                        StarPowerEvent.from_parsed_data,
                        minimal_bpm_events,
                    ),
                    unittest.mock.call(
                        [defaults.track_event_parsed_data],
                        TrackEvent.from_parsed_data,
                        minimal_bpm_events,
                    ),
                ],
            )
            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                instrument=defaults.instrument,
                difficulty=defaults.difficulty,
                note_events=[defaults.note_event],
                star_power_events=[defaults.star_power_event],
                track_events=[defaults.track_event],
            )

        @staticmethod
        def NoteEventWithDefaultsPlus(**kwargs):
            return NoteEventWithDefaults(
                _proximal_bpm_event_index=defaults.timestamp_at_tick_proximal_bpm_event_index,
                timestamp=defaults.timestamp_at_tick_timestamp,
                end_timestamp=defaults.timestamp_at_tick_timestamp,
                **kwargs,
            )

        @staticmethod
        def StarPowerEventWithDefaultsPlus(**kwargs):
            return StarPowerEventWithDefaults(
                _proximal_bpm_event_index=defaults.timestamp_at_tick_proximal_bpm_event_index,
                timestamp=defaults.timestamp_at_tick_timestamp,
                **kwargs,
            )

        # TODO: This doesn't actually test timestamp generation.
        @testcase.parametrize(
            ["lines", "want_note_events", "want_star_power_events"],
            [
                testcase.new(
                    "skip_invalid_line",
                    lines=[defaults.invalid_chart_line],
                    want_note_events=[],
                ),
                testcase.new(
                    "open_note",
                    lines=[generate_note_line(0, NoteTrackIndex.OPEN.value)],
                    want_note_events=[NoteEventWithDefaultsPlus(tick=0, note=Note.OPEN)],
                ),
                testcase.new(
                    "green_note",
                    lines=[generate_note_line(0, NoteTrackIndex.G.value)],
                    want_note_events=[NoteEventWithDefaultsPlus(tick=0, note=Note.G)],
                ),
                testcase.new(
                    "red_note",
                    lines=[generate_note_line(0, NoteTrackIndex.R.value)],
                    want_note_events=[NoteEventWithDefaultsPlus(tick=0, note=Note.R)],
                ),
                testcase.new(
                    "yellow_note",
                    lines=[generate_note_line(0, NoteTrackIndex.Y.value)],
                    want_note_events=[NoteEventWithDefaultsPlus(tick=0, note=Note.Y)],
                ),
                testcase.new(
                    "blue_note",
                    lines=[generate_note_line(0, NoteTrackIndex.B.value)],
                    want_note_events=[NoteEventWithDefaultsPlus(tick=0, note=Note.B)],
                ),
                testcase.new(
                    "orange_note",
                    lines=[generate_note_line(0, NoteTrackIndex.O.value)],
                    want_note_events=[NoteEventWithDefaultsPlus(tick=0, note=Note.O)],
                ),
                testcase.new(
                    "tap_green_note",
                    lines=[
                        generate_note_line(0, NoteTrackIndex.G.value),
                        generate_note_line(0, NoteTrackIndex.TAP.value),
                    ],
                    want_note_events=[
                        NoteEventWithDefaultsPlus(
                            tick=0,
                            note=Note.G,
                            hopo_state=HOPOState.TAP,
                        )
                    ],
                ),
                testcase.new(
                    "forced_red_note",
                    lines=[
                        generate_note_line(0, NoteTrackIndex.G.value),
                        generate_note_line(1, NoteTrackIndex.R.value),
                        generate_note_line(1, NoteTrackIndex.FORCED.value),
                    ],
                    want_note_events=[
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
                ),
                testcase.new(
                    "green_with_sustain",
                    lines=[
                        generate_note_line(0, NoteTrackIndex.G.value, sustain=100),
                    ],
                    want_note_events=[NoteEventWithDefaultsPlus(tick=0, note=Note.G, sustain=100)],
                ),
                testcase.new(
                    "chord",
                    lines=[
                        generate_note_line(0, NoteTrackIndex.G.value),
                        generate_note_line(0, NoteTrackIndex.R.value),
                    ],
                    want_note_events=[NoteEventWithDefaultsPlus(tick=0, note=Note.GR)],
                ),
                testcase.new(
                    "nonuniform_sustains",
                    lines=[
                        generate_note_line(0, NoteTrackIndex.G.value, sustain=100),
                        generate_note_line(0, NoteTrackIndex.R.value),
                    ],
                    want_note_events=[
                        NoteEventWithDefaultsPlus(
                            tick=0,
                            note=Note.GR,
                            sustain=(100, 0, None, None, None),
                        )
                    ],
                ),
                testcase.new(
                    "single_star_power_phrase",
                    lines=[generate_star_power_line(0, 100)],
                    want_star_power_events=[StarPowerEventWithDefaultsPlus(tick=0, sustain=100)],
                ),
                testcase.new(
                    "everything_together",
                    lines=[
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
                    want_note_events=[
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
                    want_star_power_events=[
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
                ),
            ],
            default_values={"want_note_events": [], "want_star_power_events": []},
        )
        def test_integration(
            self,
            mocker,
            lines,
            want_note_events,
            want_star_power_events,
            minimal_bpm_events_with_mock,
        ):
            got = InstrumentTrack.from_chart_lines(
                defaults.instrument,
                defaults.difficulty,
                lines,
                minimal_bpm_events_with_mock,
            )
            assert got.instrument == defaults.instrument
            assert got.difficulty == defaults.difficulty
            assert got.star_power_events == want_star_power_events
            assert got.note_events == want_note_events

    class TestLastNoteEndTimestamp(object):
        @testcase.parametrize(
            ["note_events", "want"],
            [
                testcase.new(
                    "in_the_middle",
                    note_events=[
                        NoteEventWithDefaults(end_timestamp=timedelta(seconds=0)),
                        NoteEventWithDefaults(end_timestamp=timedelta(seconds=1)),
                        NoteEventWithDefaults(end_timestamp=timedelta(seconds=0.5)),
                    ],
                    want=timedelta(seconds=1),
                ),
            ],
        )
        def test(self, bare_instrument_track, note_events, want):
            unsafe.setattr(bare_instrument_track, "note_events", note_events)
            got = bare_instrument_track.last_note_end_timestamp
            assert got == want

        def test_empty(self, minimal_instrument_track):
            got = minimal_instrument_track.last_note_end_timestamp
            assert got is None

    class TestStr(object):
        # This just exercises the path; asserting the output is irksome and unnecessary.
        def test(self, default_instrument_track):
            str(default_instrument_track)


class TestNoteEvent(object):
    class TestFromParsedData(object):
        @testcase.parametrize(
            [
                "data",
                "want_tick",
                "want_sustain",
                "want_note",
                "want_hopo_state",
                "want_star_power_data",
                "want_star_power_event_index",
                "want_proximal_bpm_event_index",
            ],
            [
                testcase.new(
                    "single_data",
                    data=NoteEventParsedDataWithDefaults(
                        tick=1, note_track_index=NoteTrackIndex.G, sustain=100
                    ),
                    want_tick=1,
                    want_sustain=100,
                    want_note=Note.G,
                    want_hopo_state=HOPOState.STRUM,
                    want_star_power_data=StarPowerData(star_power_event_index=5),
                    want_star_power_event_index=11,
                    want_proximal_bpm_event_index=22,
                ),
                testcase.new(
                    "multiple_data",
                    data=[
                        NoteEventParsedDataWithDefaults(
                            tick=1, note_track_index=NoteTrackIndex.G, sustain=100
                        ),
                        NoteEventParsedDataWithDefaults(
                            tick=1, note_track_index=NoteTrackIndex.R, sustain=50
                        ),
                    ],
                    want_tick=1,
                    want_sustain=(100, 50, None, None, None),
                    want_note=Note.GR,
                    want_hopo_state=HOPOState.STRUM,
                    want_star_power_data=StarPowerData(star_power_event_index=5),
                    want_star_power_event_index=11,
                    want_proximal_bpm_event_index=22,
                ),
            ],
        )
        def test(
            self,
            mocker,
            minimal_bpm_events_with_mock,
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
                [defaults.star_power_event],
                minimal_bpm_events_with_mock,
                proximal_bpm_event_index=want_proximal_bpm_event_index,
                star_power_event_index=want_star_power_event_index,
            )

            minimal_bpm_events_with_mock.timestamp_at_tick_mock.assert_has_calls(
                [
                    unittest.mock.call(
                        want_tick,
                        start_iteration_index=want_proximal_bpm_event_index,
                    ),
                    unittest.mock.call(
                        # technically tick+sustain, but annoying because it requires mocking or
                        # calling _end_tick.
                        unittest.mock.ANY,
                        start_iteration_index=minimal_bpm_events_with_mock.proximal_bpm_event_index,  # noqa: E501
                    ),
                ],
            )

            mock_compute_hopo_state.assert_called_once_with(
                minimal_bpm_events_with_mock.resolution,
                want_tick,
                want_note,
                False,
                False,
                None,
            )

            mock_compute_star_power_data.assert_called_once_with(
                want_tick,
                [defaults.star_power_event],
                proximal_star_power_event_index=want_star_power_event_index,
            )

            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                tick=want_tick,
                timestamp=minimal_bpm_events_with_mock.timestamp,
                end_timestamp=minimal_bpm_events_with_mock.timestamp,
                note=want_note,
                hopo_state=want_hopo_state,
                sustain=want_sustain,
                _proximal_bpm_event_index=minimal_bpm_events_with_mock.proximal_bpm_event_index,
                star_power_data=want_star_power_data,
            )

    class TestStr(object):
        # This just exercises the path; asserting the output is irksome and unnecessary.
        @testcase.parametrize(
            ["event"],
            [
                testcase.new(
                    "with_star_power",
                    event=NoteEventWithDefaults(
                        star_power_data=StarPowerData(star_power_event_index=0)
                    ),
                ),
                testcase.new(
                    "without_star_power",
                    event=NoteEventWithDefaults(),
                ),
            ],
        )
        def test(self, event):
            str(event)

    class TestComputeHOPOState(object):
        @testcase.parametrize(
            ["tick", "note", "is_tap", "is_forced", "previous", "want"],
            [
                testcase.new(
                    "forced_tap_note_is_a_tap",
                    # TODO: I don't actually know if this test case is accurate. Needs verifying.
                    tick=tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.SIXTEENTH,
                    ),
                    note=Note.R,
                    is_tap=True,
                    is_forced=True,
                    previous=NoteEventWithDefaults(
                        tick=0,
                        note=Note.G,
                    ),
                    want=HOPOState.TAP,
                ),
                testcase.new(
                    "first_note_is_strum",
                    tick=0,
                    note=Note.G,
                    is_tap=False,
                    is_forced=False,
                    previous=None,
                    want=HOPOState.STRUM,
                ),
                testcase.new(
                    "16th_notes_are_hopos",
                    tick=tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.SIXTEENTH,
                    ),
                    note=Note.R,
                    is_tap=False,
                    is_forced=False,
                    previous=NoteEventWithDefaults(
                        tick=0,
                        note=Note.G,
                    ),
                    want=HOPOState.HOPO,
                ),
                testcase.new(
                    "12th_notes_are_hopos",
                    tick=tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.TWELFTH,
                    ),
                    note=Note.R,
                    is_tap=False,
                    is_forced=False,
                    previous=NoteEventWithDefaults(
                        tick=0,
                        note=Note.G,
                    ),
                    want=HOPOState.HOPO,
                ),
                testcase.new(
                    "8th_notes_are_strums",
                    tick=tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.EIGHTH,
                    ),
                    note=Note.R,
                    is_tap=False,
                    is_forced=False,
                    previous=NoteEventWithDefaults(
                        tick=0,
                        note=Note.G,
                    ),
                    want=HOPOState.STRUM,
                ),
                testcase.new(
                    "consecutive_16th_notes_are_strums",
                    tick=tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.SIXTEENTH,
                    ),
                    note=Note.G,
                    is_tap=False,
                    is_forced=False,
                    previous=NoteEventWithDefaults(
                        tick=0,
                        note=Note.G,
                    ),
                    want=HOPOState.STRUM,
                ),
                testcase.new(
                    "consecutive_12th_notes_are_strums",
                    tick=tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.TWELFTH,
                    ),
                    note=Note.G,
                    is_tap=False,
                    is_forced=False,
                    previous=NoteEventWithDefaults(
                        tick=0,
                        note=Note.G,
                    ),
                    want=HOPOState.STRUM,
                ),
                testcase.new(
                    "consecutive_8th_notes_are_strums",
                    tick=tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.EIGHTH,
                    ),
                    note=Note.G,
                    is_tap=False,
                    is_forced=False,
                    previous=NoteEventWithDefaults(
                        tick=0,
                        note=Note.G,
                    ),
                    want=HOPOState.STRUM,
                ),
                testcase.new(
                    "pull_off_from_chord_is_hopo",
                    tick=tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.TWELFTH,
                    ),
                    note=Note.G,
                    is_tap=False,
                    is_forced=False,
                    previous=NoteEventWithDefaults(
                        tick=0,
                        note=Note.RY,
                    ),
                    want=HOPOState.HOPO,
                ),
                testcase.new(
                    "hammer_on_to_chord_is_not_hopo",
                    tick=tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.TWELFTH,
                    ),
                    note=Note.RY,
                    is_tap=False,
                    is_forced=False,
                    previous=NoteEventWithDefaults(
                        tick=0,
                        note=Note.G,
                    ),
                    want=HOPOState.STRUM,
                ),
                testcase.new(
                    "hammer_on_to_open_is_hopo",
                    tick=tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.TWELFTH,
                    ),
                    note=Note.OPEN,
                    is_tap=False,
                    is_forced=False,
                    previous=NoteEventWithDefaults(
                        tick=0,
                        note=Note.G,
                    ),
                    want=HOPOState.HOPO,
                ),
                testcase.new(
                    "pull_off_to_open_is_hopo",
                    tick=tests.helpers.tick.calculate_ticks_between_notes_with_defaults(
                        NoteDuration.TWELFTH,
                    ),
                    note=Note.G,
                    is_tap=False,
                    is_forced=False,
                    previous=NoteEventWithDefaults(
                        tick=0,
                        note=Note.OPEN,
                    ),
                    want=HOPOState.HOPO,
                ),
            ],
        )
        def test(self, tick, note, is_tap, is_forced, previous, want):
            got = NoteEvent._compute_hopo_state(
                defaults.resolution,
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
                    defaults.resolution,
                    defaults.tick,
                    defaults.note,
                    False,
                    True,
                    None,
                )

    class TestParsedData(object):
        class TestFromChartLine(object):
            test_regex = r"^T (\d+?) I (\d+?) S (\d+?)$"

            tick = 4

            @testcase.parametrize(
                ["want_note_track_index", "want_sustain"],
                [
                    testcase.new(
                        "normal_note",
                        want_note_track_index=NoteTrackIndex.YELLOW,
                        want_sustain=3,
                    ),
                    testcase.new(
                        "open_note",
                        want_note_track_index=NoteTrackIndex.OPEN,
                        want_sustain=3,
                    ),
                    testcase.new(
                        "forced_note",
                        want_note_track_index=NoteTrackIndex.FORCED,
                        want_sustain=0,
                    ),
                    testcase.new(
                        "tap_note",
                        want_note_track_index=NoteTrackIndex.TAP,
                        want_sustain=0,
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

            def test_no_match(self, invalid_chart_line):
                with pytest.raises(RegexNotMatchError):
                    _ = NoteEvent.ParsedData.from_chart_line(invalid_chart_line)

            def test_unhandled_note_track_index(self, mocker, caplog):
                invalid_instrument_note_track_index = 8
                with pytest.raises(ValueError):
                    _ = NoteEvent.ParsedData.from_chart_line(
                        f"T {defaults.tick} "
                        f"I {invalid_instrument_note_track_index} "
                        f"S {defaults.sustain}"
                    )

            def setup_method(self):
                NoteEvent.ParsedData._regex = self.test_regex
                NoteEvent.ParsedData._regex_prog = re.compile(NoteEvent.ParsedData._regex)

            def teardown_method(self):
                del NoteEvent.ParsedData._regex
                del NoteEvent.ParsedData._regex_prog

        class TestComplexSustain(object):
            @testcase.parametrize(
                ["sustain", "want"],
                [
                    testcase.new(
                        "None",
                        sustain=None,
                        want=None,
                    ),
                    testcase.new(
                        "int",
                        sustain=1,
                        want=1,
                    ),
                    testcase.new(
                        "list",
                        sustain=(None, 1, None, None, None),
                        want=(None, 1, None, None, None),
                    ),
                ],
            )
            def test(self, bare_note_event_parsed_data, sustain, want):
                bare_note_event_parsed_data.__dict__["sustain"] = sustain
                got = bare_note_event_parsed_data.sustain
                assert got == want

    class TestComputeStarPowerData(object):
        @testcase.parametrize(
            ["tick", "star_power_events", "want_data", "want_proximal_star_power_event_index"],
            [
                testcase.new(
                    "empty_star_power_events",
                    tick=defaults.tick,
                    star_power_events=[],
                    want_data=None,
                    want_proximal_star_power_event_index=0,
                ),
                testcase.new(
                    "tick_not_in_event",
                    tick=0,
                    star_power_events=[StarPowerEventWithDefaults(tick=100, sustain=10)],
                    want_data=None,
                    want_proximal_star_power_event_index=0,
                ),
                testcase.new(
                    "tick_not_in_event_with_noninitial_candidate_index",
                    tick=10,
                    star_power_events=[
                        StarPowerEventWithDefaults(tick=0, sustain=10),
                        StarPowerEventWithDefaults(tick=100, sustain=10),
                    ],
                    want_data=None,
                    want_proximal_star_power_event_index=1,
                ),
                testcase.new(
                    "tick_in_event",
                    tick=0,
                    star_power_events=[StarPowerEventWithDefaults(tick=0, sustain=10)],
                    want_data=StarPowerData(
                        star_power_event_index=defaults.proximal_star_power_event_index
                    ),
                    want_proximal_star_power_event_index=0,
                ),
                testcase.new(
                    "tick_in_event_with_noninitial_candidate_index",
                    tick=100,
                    star_power_events=[
                        StarPowerEventWithDefaults(tick=0, sustain=10),
                        StarPowerEventWithDefaults(tick=100, sustain=10),
                    ],
                    want_data=StarPowerData(star_power_event_index=1),
                    want_proximal_star_power_event_index=1,
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
                proximal_star_power_event_index=defaults.proximal_star_power_event_index,
            )
            assert got_data == want_data
            assert got_proximal_star_power_event_index == want_proximal_star_power_event_index

        def test_proximal_star_power_event_index_after_last_event(self):
            with pytest.raises(ValueError):
                _, _ = NoteEvent._compute_star_power_data(
                    defaults.tick,
                    [defaults.star_power_event],
                    proximal_star_power_event_index=len([defaults.star_power_event]),
                )

    class TestLongestSustain(object):
        @testcase.parametrize(
            ["sustain", "want"],
            [
                testcase.new(
                    "simple_sustain",
                    sustain=100,
                    want=100,
                ),
                testcase.new(
                    "tuple_sustain",
                    sustain=(50, 100, None, 200, None),
                    want=200,
                ),
            ],
        )
        def test(self, mocker, bare_note_event, sustain, want):
            # Test wrapper
            unsafe.setattr(bare_note_event, "sustain", 100)
            spy = mocker.spy(NoteEvent, "_longest_sustain")
            bare_note_event.longest_sustain
            spy.assert_called_once_with(100)

            # Test impl
            got = NoteEvent._longest_sustain(sustain)
            assert got == want

        def test_impl_all_none(self):
            with pytest.raises(ValueError):
                _ = NoteEvent._longest_sustain((None, None, None, None, None))

    class TestEndTick(object):
        def test_wrapper(self, mocker, bare_note_event):
            unsafe.setattr(bare_note_event, "tick", 100)
            unsafe.setattr(bare_note_event, "sustain", 10)
            spy = mocker.spy(NoteEvent, "_end_tick")
            bare_note_event.end_tick
            assert spy.called_once_with(100, 10)

        def test_impl(self):
            got = NoteEvent._end_tick(100, 10)
            want = 110
            assert got == want


class TestSpecialEvent(object):
    class TestFromParsedData(object):
        @testcase.parametrize(
            ["prev_event"],
            [
                testcase.new(
                    "prev_event_none",
                    prev_event=None,
                ),
                testcase.new(
                    "prev_event_present",
                    prev_event=SpecialEventWithDefaults(_proximal_bpm_event_index=1),
                ),
            ],
        )
        def test(self, mocker, minimal_bpm_events_with_mock, prev_event):
            spy_init = mocker.spy(SpecialEvent, "__init__")

            _ = SpecialEvent.from_parsed_data(
                SpecialEventParsedDataWithDefaults(), prev_event, minimal_bpm_events_with_mock
            )

            minimal_bpm_events_with_mock.timestamp_at_tick_mock.assert_called_once_with(
                defaults.tick,
                start_iteration_index=prev_event._proximal_bpm_event_index if prev_event else 0,
            )
            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                tick=defaults.tick,
                timestamp=minimal_bpm_events_with_mock.timestamp,
                sustain=defaults.sustain,
                _proximal_bpm_event_index=minimal_bpm_events_with_mock.proximal_bpm_event_index,
            )

    class TestStr(object):
        # This just exercises the path; asserting the output is irksome and unnecessary.
        def test(self):
            e = SpecialEventWithDefaults()
            str(e)

    class TestParsedData(object):
        class TestFromChartLine(object):
            test_regex = r"^T (\d+?) V (.*?)$"

            def test(self, mocker):
                got = SpecialEvent.ParsedData.from_chart_line(
                    f"T {defaults.tick} V {defaults.sustain}"
                )
                assert got.tick == defaults.tick
                assert got.sustain == defaults.sustain

            def test_no_match(self, invalid_chart_line):
                with pytest.raises(RegexNotMatchError):
                    _ = SpecialEvent.ParsedData.from_chart_line(invalid_chart_line)

            def setup_method(self):
                SpecialEvent.ParsedData._regex = self.test_regex
                SpecialEvent.ParsedData._regex_prog = re.compile(SpecialEvent.ParsedData._regex)

            def teardown_method(self):
                del SpecialEvent.ParsedData._regex
                del SpecialEvent.ParsedData._regex_prog

    class TestTickIsAfterEvent(object):
        @testcase.parametrize(
            ["tick", "want"],
            [
                testcase.new(
                    "before",
                    tick=0,
                    want=False,
                ),
                testcase.new(
                    "coincide_with_start",
                    tick=100,
                    want=False,
                ),
                testcase.new(
                    "coincide_with_end",
                    tick=110,
                    want=True,
                ),
                testcase.new(
                    "after",
                    tick=111,
                    want=True,
                ),
            ],
        )
        def test(self, tick, want):
            event = SpecialEventWithDefaults(tick=100, sustain=10)
            got = event.tick_is_after_event(tick)
            assert got == want

    class TestTickIsDuringEvent(object):
        @testcase.parametrize(
            ["tick", "want"],
            [
                testcase.new(
                    "before",
                    tick=0,
                    want=False,
                ),
                testcase.new(
                    "coincide_with_start",
                    tick=100,
                    want=True,
                ),
                testcase.new(
                    "coincide_with_end",
                    tick=110,
                    want=False,
                ),
                testcase.new(
                    "after",
                    tick=111,
                    want=False,
                ),
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
        @testcase.parametrize(
            ["prev_event"],
            [
                testcase.new(
                    "prev_event_none",
                    prev_event=None,
                ),
                testcase.new(
                    "prev_event_present",
                    prev_event=TrackEventWithDefaults(_proximal_bpm_event_index=1),
                ),
            ],
        )
        def test(self, mocker, minimal_bpm_events_with_mock, prev_event):
            spy_init = mocker.spy(TrackEvent, "__init__")

            _ = TrackEvent.from_parsed_data(
                TrackEventParsedDataWithDefaults(),
                prev_event,
                minimal_bpm_events_with_mock,
            )

            minimal_bpm_events_with_mock.timestamp_at_tick_mock.assert_called_once_with(
                defaults.tick,
                start_iteration_index=prev_event._proximal_bpm_event_index if prev_event else 0,
            )

            spy_init.assert_called_once_with(
                unittest.mock.ANY,  # ignore self
                tick=defaults.tick,
                timestamp=minimal_bpm_events_with_mock.timestamp,
                value=defaults.track_event_value,
                _proximal_bpm_event_index=minimal_bpm_events_with_mock.proximal_bpm_event_index,
            )

    class TestStr(object):
        # This just exercises the path; asserting the output is irksome and unnecessary.
        def test(self):
            e = TrackEventWithDefaults()
            str(e)

    class TestParsedData(object):
        class TestFromChartLine(object):
            def test(self, mocker):
                line = generate_track_line(defaults.tick, defaults.track_event_value)
                got = TrackEvent.ParsedData.from_chart_line(line)
                assert got.tick == defaults.tick
                assert got.value == defaults.track_event_value

            def test_no_match(self, invalid_chart_line):
                with pytest.raises(RegexNotMatchError):
                    _ = TrackEvent.ParsedData.from_chart_line(invalid_chart_line)
