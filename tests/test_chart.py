from __future__ import annotations

import pathlib
import typing as typ
import unittest.mock
from collections.abc import Sequence
from datetime import timedelta

import pytest

from chartparse.chart import Chart, InstrumentTrackMap
from chartparse.exceptions import RegexNotMatchError
from chartparse.globalevents import GlobalEventsTrack
from chartparse.instrument import Difficulty, Instrument, InstrumentTrack, Note
from chartparse.metadata import Metadata
from chartparse.sync import SyncTrack
from chartparse.tick import Tick
from chartparse.time import Timestamp
from tests.helpers import defaults, testcase, unsafe
from tests.helpers.instrument import NoteEventWithDefaults
from tests.helpers.log import LogChecker

_directory_of_this_file = pathlib.Path(__file__).parent.resolve()
_chart_directory_filepath = _directory_of_this_file / "data"
_valid_chart_filepath = _chart_directory_filepath / "test.chart"
_missing_metadata_chart_filepath = _chart_directory_filepath / "missing_metadata.chart"
_missing_sync_track_chart_filepath = _chart_directory_filepath / "missing_sync_track.chart"
_missing_global_events_track_chart_filepath = (
    _chart_directory_filepath / "missing_global_events_track.chart"
)
_unhandled_section_chart_filepath = _chart_directory_filepath / "unhandled_section.chart"


class TestChart(object):
    class TestInit(object):
        def test(
            self,
            mocker: typ.Any,
            default_metadata: Metadata,
            default_global_events_track: GlobalEventsTrack,
            default_sync_track: SyncTrack,
            default_instrument_track: InstrumentTrack,
            default_instrument_tracks: InstrumentTrackMap,
        ) -> None:
            got = Chart(
                default_metadata,
                default_global_events_track,
                default_sync_track,
                default_instrument_tracks,
            )

            assert got.metadata == default_metadata
            assert got.global_events_track == default_global_events_track
            assert got.sync_track == default_sync_track
            assert got.instrument_tracks == default_instrument_tracks

    class TestFromFilepath(object):
        def test(self, mocker: typ.Any, default_chart: Chart) -> None:
            spy = mocker.spy(Chart, "from_file")
            _ = Chart.from_filepath(_valid_chart_filepath, want_tracks=[])
            spy.assert_called_once_with(
                # I don't care to mock the stdlib's `open` return value.
                unittest.mock.ANY,
                want_tracks=[],
            )

    class TestFromFile(object):
        def test(
            self,
            mocker: typ.Any,
            default_chart: Chart,
            default_metadata: Metadata,
            default_global_events_track: GlobalEventsTrack,
            default_sync_track: SyncTrack,
            default_instrument_track: InstrumentTrack,
            invalid_chart_line: str,
        ) -> None:
            mocker.patch.object(
                Chart,
                "_parse_section_dict",
                return_value={
                    "Song": [invalid_chart_line],
                    "Events": [invalid_chart_line],
                    "SyncTrack": [invalid_chart_line],
                    "ExpertSingle": [invalid_chart_line],
                    # EasySingle is ignored in this test case via want_tracks.
                    "EasySingle": [invalid_chart_line],
                },
            )
            mocker.patch.object(
                Metadata,
                "from_chart_lines",
                return_value=default_metadata,
            )
            mocker.patch.object(
                GlobalEventsTrack,
                "from_chart_lines",
                return_value=default_global_events_track,
            )
            mocker.patch.object(
                SyncTrack,
                "from_chart_lines",
                return_value=default_sync_track,
            )
            instrument_track_from_chart_lines_mock = mocker.patch.object(
                InstrumentTrack,
                "from_chart_lines",
                return_value=default_instrument_track,
            )

            want_tracks = [(Instrument.GUITAR, Difficulty.EXPERT)]

            with open(_valid_chart_filepath, "r", encoding="utf-8-sig") as f:
                got = Chart.from_file(f, want_tracks=want_tracks)

            assert got == default_chart

            # This assert tests the want_tracks filtering logic; because EasySingle is returned by
            # _parse_section_dict, InstrumentTrack.from_chart_lines will be called more than once
            # if the filtering logic does not work.
            instrument_track_from_chart_lines_mock.assert_called_once_with(
                Instrument.GUITAR,
                Difficulty.EXPERT,
                [invalid_chart_line],
                default_sync_track.bpm_events,
            )

        @testcase.parametrize(
            ["path"],
            [
                testcase.new(
                    "missing_metadata",
                    path=_missing_metadata_chart_filepath,
                ),
                testcase.new(
                    "missing_sync_track",
                    path=_missing_sync_track_chart_filepath,
                ),
                testcase.new(
                    "missing_global_events_track",
                    path=_missing_global_events_track_chart_filepath,
                ),
            ],
        )
        def test_invalid_chart(self, path: str) -> None:
            with open(path, "r", encoding="utf-8-sig") as f, pytest.raises(ValueError):
                _ = Chart.from_file(f)

        def test_unhandled_section(self, caplog: pytest.LogCaptureFixture) -> None:
            with open(_unhandled_section_chart_filepath, "r", encoding="utf-8-sig") as f:
                _ = Chart.from_file(f)
            logchecker = LogChecker(caplog)
            logchecker.assert_contains_string_in_one_line(
                Chart._unhandled_section_log_msg_tmpl.format("Foo")
            )

    class TestFindSections(object):
        def test(self) -> None:
            with open(_valid_chart_filepath, "r", encoding="utf-8-sig") as f:
                lines = f.read().splitlines()

            sections = Chart._parse_section_dict(lines)

            def validate_lines(section_name: str, want_lines: Sequence[str]) -> None:
                assert section_name in sections
                lines = sections[section_name]
                assert list(lines) == want_lines

            validate_lines(
                "Events",
                [
                    '  800 = E "section Section 1"',
                    '  1000 = E "phrase_start"',
                    '  1200 = E "lyric Lo-"',
                    '  1230 = E "lyric rem"',
                    '  1800 = E "lyric ip-"',
                    '  1840 = E "lyric sum"',
                ],
            )

            validate_lines(
                "Song",
                [
                    '  Name = "Song Name"',
                    '  Artist = "Artist Name"',
                    '  Charter = "Charter Name"',
                    '  Album = "Album Name"',
                    '  Year = "1999"',
                    "  Offset = 0",
                    "  Resolution = 100",
                    "  Player2 = bass",
                    "  Difficulty = 6",
                    "  PreviewStart = 0",
                    "  PreviewEnd = 0",
                    '  Genre = "rock"',
                    '  MediaType = "cd"',
                    '  MusicStream = "song.ogg"',
                ],
            )

            validate_lines(
                "SyncTrack",
                [
                    "  0 = TS 4",
                    "  0 = B 117000",
                    "  800 = B 120000",
                    "  1200 = B 90000",
                    "  1200 = TS 6 3",
                    "  1800 = B 100000",
                ],
            )

            validate_lines(
                "ExpertSingle",
                [
                    "  800 = N 0 0",
                    "  800 = N 2 0",
                    "  825 = N 0 0",
                    "  825 = N 5 0 ",
                    "  900 = N 0 0",
                    "  1000 = N 0 0",
                    "  1000 = N 2 0",
                    "  1000 = S 2 100",
                    "  1100 = N 0 0",
                    "  1100 = N 5 0 ",
                    "  1150 = N 0 0",
                    "  1200 = N 0 0",
                    "  1200 = S 2 200",
                    "  1225 = N 0 0",
                    "  1300 = N 0 0",
                    "  1300 = N 3 0",
                    "  2000 = N 0 0",
                ],
            )

        @testcase.parametrize(
            ["lines"],
            [
                testcase.new(
                    "malformed_missing_open_bracket",
                    lines=["Song]", "{", '  Name = "Song Name"', "}"],
                ),
                testcase.new(
                    "malformed_missing_close_bracket",
                    lines=["[Song", "{", '  Name = "Song Name"', "}"],
                ),
                testcase.new(
                    "malformed_noninitial_section",
                    lines=[
                        "[Song]",
                        "{",
                        '  Name = "Song Name"',
                        "}",
                        "[ExpertSingle",
                    ],
                ),
            ],
        )
        def test_raises(self, lines: Sequence[str]) -> None:
            with pytest.raises(RegexNotMatchError):
                _ = Chart._parse_section_dict(lines)

    class TestNotesPerSecond(object):
        @testcase.parametrize(
            ["start_time", "end_time", "want"],
            [
                testcase.new(
                    "boundaries_included",
                    start_time=timedelta(seconds=1),
                    end_time=timedelta(seconds=3),
                    want=3 / 2,
                ),
                testcase.new(
                    "filtered_too_early_note",
                    start_time=timedelta(seconds=2),
                    end_time=timedelta(seconds=3),
                    want=2,
                ),
                testcase.new(
                    "filtered_too_late_note",
                    start_time=timedelta(seconds=1),
                    end_time=timedelta(seconds=2),
                    want=2,
                ),
                testcase.new(
                    "wider_interval_than_notes",
                    start_time=timedelta(seconds=0),
                    end_time=timedelta(seconds=4),
                    want=3 / 4,
                ),
            ],
        )
        def test_impl(
            self, bare_chart: Chart, start_time: Timestamp, end_time: Timestamp, want: float
        ) -> None:
            note_event1 = NoteEventWithDefaults(
                timestamp=Timestamp(timedelta(seconds=1)),
                note=Note.GRY,
            )
            note_event2 = NoteEventWithDefaults(
                timestamp=Timestamp(timedelta(seconds=2)),
                note=Note.RYB,
            )
            note_event3 = NoteEventWithDefaults(
                timestamp=Timestamp(timedelta(seconds=3)),
                note=Note.YBO,
            )
            test_notes_per_second_note_events = [note_event1, note_event2, note_event3]
            got = bare_chart._notes_per_second(
                test_notes_per_second_note_events, start_time, end_time
            )
            assert got == want

        @testcase.parametrize(
            ["start_time", "end_time"],
            [
                testcase.new(
                    "zero",
                    start_time=timedelta(seconds=1),
                    end_time=timedelta(seconds=1),
                ),
                testcase.new(
                    "negative",
                    start_time=timedelta(seconds=2),
                    end_time=timedelta(seconds=1),
                ),
            ],
        )
        def test_impl_error(
            self, bare_chart: Chart, start_time: Timestamp, end_time: Timestamp
        ) -> None:
            with pytest.raises(ValueError):
                _ = bare_chart._notes_per_second([], start_time, end_time)

        @testcase.parametrize(
            ["start_tick", "end_tick", "want_start_time", "want_end_time"],
            [
                testcase.new(
                    "both_none",
                    start_tick=None,
                    end_tick=None,
                    want_start_time=timedelta(0),
                    want_end_time=timedelta(seconds=2),
                ),
                testcase.new(
                    "end_none",
                    start_tick=1,
                    end_tick=None,
                    want_start_time=timedelta(seconds=1),
                    want_end_time=timedelta(seconds=1000),
                ),
                testcase.new(
                    "no_none",
                    start_tick=1,
                    end_tick=2,
                    want_start_time=timedelta(seconds=1),
                    want_end_time=timedelta(seconds=2),
                ),
            ],
        )
        def test_with_ticks(
            self,
            mocker: typ.Any,
            minimal_chart: Chart,
            start_tick: Tick,
            end_tick: Tick,
            want_start_time: Timestamp,
            want_end_time: Timestamp,
        ) -> None:
            unsafe.setattr(
                minimal_chart[defaults.instrument][defaults.difficulty],
                "note_events",
                [defaults.note_event],
            )

            mocker.patch.object(
                InstrumentTrack,
                "last_note_end_timestamp",
                new_callable=mocker.PropertyMock,
                return_value=want_end_time,
            )

            # NOTE: This _should_ be mocked with patch, but because bpm_events is a frozen
            # dataclass, it cannot be mocked conventionally (mocking tries to edit fields that are
            # protected by frozenness).
            unsafe.setattr(
                minimal_chart.sync_track.bpm_events,
                "timestamp_at_tick_no_optimize_return",
                lambda tick, *, _start_iteration_index=0: timedelta(seconds=tick),
            )
            mock = mocker.patch.object(minimal_chart, "_notes_per_second")
            _ = minimal_chart.notes_per_second(
                defaults.instrument,
                defaults.difficulty,
                start=start_tick,
                end=end_tick,
            )
            mock.assert_called_once_with([defaults.note_event], want_start_time, want_end_time)

            # NOTE: Manually reset timestamp_at_tick_no_optimize_return from mocked version.
            unsafe.delattr(
                minimal_chart.sync_track.bpm_events,
                "timestamp_at_tick_no_optimize_return",
            )

        @testcase.parametrize(
            ["start_time", "end_time", "want_start_time", "want_end_time"],
            [
                testcase.new(
                    "end_none",
                    start_time=timedelta(seconds=1),
                    end_time=None,
                    want_start_time=timedelta(seconds=1),
                    want_end_time=timedelta(seconds=1000),
                ),
                testcase.new(
                    "no_none",
                    start_time=timedelta(seconds=1),
                    end_time=timedelta(seconds=2),
                    want_start_time=timedelta(seconds=1),
                    want_end_time=timedelta(seconds=2),
                ),
            ],
        )
        def test_with_time(
            self,
            mocker: typ.Any,
            minimal_chart: Chart,
            start_time: Timestamp,
            end_time: Timestamp,
            want_start_time: Timestamp,
            want_end_time: Timestamp,
        ) -> None:
            unsafe.setattr(
                minimal_chart[defaults.instrument][defaults.difficulty],
                "note_events",
                [defaults.note_event],
            )

            mocker.patch.object(
                InstrumentTrack,
                "last_note_end_timestamp",
                new_callable=mocker.PropertyMock,
                return_value=want_end_time,
            )

            mock = mocker.patch.object(minimal_chart, "_notes_per_second")
            _ = minimal_chart.notes_per_second(
                defaults.instrument,
                defaults.difficulty,
                start=start_time,
                end=end_time,
            )
            mock.assert_called_once_with([defaults.note_event], want_start_time, want_end_time)

        @testcase.parametrize(
            ["instrument", "difficulty"],
            [
                testcase.new_anonymous(
                    instrument=Instrument.BASS,
                    difficulty=Difficulty.EXPERT,
                ),
                testcase.new_anonymous(
                    instrument=Instrument.GUITAR,
                    difficulty=Difficulty.MEDIUM,
                ),
                testcase.new_anonymous(
                    instrument=Instrument.BASS,
                    difficulty=Difficulty.MEDIUM,
                ),
            ],
        )
        def test_missing_instrument_difficulty(
            self, default_chart: Chart, instrument: Instrument, difficulty: Difficulty
        ) -> None:
            with pytest.raises(ValueError):
                _ = default_chart.notes_per_second(
                    instrument,
                    difficulty,
                )

        def test_empty_note_events(
            self,
            bare_chart: Chart,
            minimal_instrument_tracks: InstrumentTrackMap,
        ) -> None:
            unsafe.setattr(bare_chart, "instrument_tracks", minimal_instrument_tracks)
            with pytest.raises(ValueError):
                _ = bare_chart.notes_per_second(
                    defaults.instrument,
                    defaults.difficulty,
                )

    class TestGetItem(object):
        def test(self, default_chart: Chart) -> None:
            got = default_chart[defaults.instrument][defaults.difficulty]
            want = default_chart.instrument_tracks[defaults.instrument][defaults.difficulty]
            assert got == want

    class TestStr(object):
        # This just exercises the path; asserting the output is irksome and unnecessary.
        def test(self, default_chart: Chart) -> None:
            str(default_chart)
