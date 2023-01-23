from __future__ import annotations

import datetime
import pathlib
import pytest
import unittest.mock

from chartparse.chart import Chart
from chartparse.exceptions import RegexNotMatchError
from chartparse.globalevents import GlobalEventsTrack
from chartparse.instrument import InstrumentTrack, Difficulty, Instrument, Note
from chartparse.metadata import Metadata
from chartparse.sync import SyncTrack

from tests.helpers import defaults
from tests.helpers import unsafe
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
            mocker,
            default_metadata,
            default_global_events_track,
            default_sync_track,
            default_instrument_track,
            default_instrument_tracks,
        ):
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
        def test(self, mocker, default_chart):
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
            mocker,
            default_chart,
            default_metadata,
            default_global_events_track,
            default_sync_track,
            default_instrument_track,
            invalid_chart_line,
        ):
            mocker.patch.object(
                Chart,
                "_find_sections",
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
            # _find_sections, InstrumentTrack.from_chart_lines will be called more than once if the
            # filtering logic does not work.
            instrument_track_from_chart_lines_mock.assert_called_once_with(
                Instrument.GUITAR,
                Difficulty.EXPERT,
                [invalid_chart_line],
                default_sync_track,
            )

        @pytest.mark.parametrize(
            "path",
            [
                pytest.param(
                    _missing_metadata_chart_filepath,
                    id="missing_metadata",
                ),
                pytest.param(
                    _missing_sync_track_chart_filepath,
                    id="missing_sync_track",
                ),
                pytest.param(
                    _missing_global_events_track_chart_filepath,
                    id="missing_global_events_track",
                ),
            ],
        )
        def test_invalid_chart(self, path):
            with open(path, "r", encoding="utf-8-sig") as f, pytest.raises(ValueError):
                _ = Chart.from_file(f)

        def test_unhandled_section(self, caplog):
            with open(_unhandled_section_chart_filepath, "r", encoding="utf-8-sig") as f:
                _ = Chart.from_file(f)
            logchecker = LogChecker(caplog)
            logchecker.assert_contains_string_in_one_line(
                Chart._unhandled_section_log_msg_tmpl.format("Foo")
            )

    class TestFindSections(object):
        def test(self):
            # TODO: Reconstruct file contents from want_lines rather than having an actual file.
            with open(_valid_chart_filepath, "r", encoding="utf-8-sig") as f:
                lines = f.read().splitlines()

            sections = Chart._find_sections(lines)

            def validate_lines(section_name, want_lines):
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

        @pytest.mark.parametrize(
            "lines",
            [
                pytest.param(
                    ["Song]", "{", '  Name = "Song Name"', "}"],
                    id="malformed_missing_open_bracket",
                ),
                pytest.param(
                    ["[Song", "{", '  Name = "Song Name"', "}"],
                    id="malformed_missing_close_bracket",
                ),
                pytest.param(
                    [
                        "[Song]",
                        "{",
                        '  Name = "Song Name"',
                        "}",
                        "[ExpertSingle",
                    ],
                    id="malformed_noninitial_section",
                ),
            ],
        )
        def test_raises(self, lines):
            with pytest.raises(RegexNotMatchError):
                _ = Chart._find_sections(lines)

    class TestSecondsFromTicksAtBPM(object):
        def test(self, mocker, minimal_chart):
            mock = mocker.patch("chartparse.tick.seconds_from_ticks_at_bpm")
            _ = minimal_chart._seconds_from_ticks_at_bpm(defaults.tick, defaults.bpm)
            mock.assert_called_once_with(defaults.tick, defaults.bpm, defaults.resolution)

    class TestNotesPerSecond(object):
        @pytest.mark.parametrize(
            "interval_start_time,interval_end_time,want",
            [
                pytest.param(
                    datetime.timedelta(seconds=1),
                    datetime.timedelta(seconds=3),
                    3 / 2,
                    id="boundaries_included",
                ),
                pytest.param(
                    datetime.timedelta(seconds=2),
                    datetime.timedelta(seconds=3),
                    2,
                    id="filtered_too_early_note",
                ),
                pytest.param(
                    datetime.timedelta(seconds=1),
                    datetime.timedelta(seconds=2),
                    2,
                    id="filtered_too_late_note",
                ),
                pytest.param(
                    datetime.timedelta(seconds=0),
                    datetime.timedelta(seconds=4),
                    3 / 4,
                    id="wider_interval_than_notes",
                ),
            ],
        )
        def test_from_note_events(self, bare_chart, interval_start_time, interval_end_time, want):
            note_event1 = NoteEventWithDefaults(
                timestamp=datetime.timedelta(seconds=1),
                note=Note.GRY,
            )
            note_event2 = NoteEventWithDefaults(
                timestamp=datetime.timedelta(seconds=2),
                note=Note.RYB,
            )
            note_event3 = NoteEventWithDefaults(
                timestamp=datetime.timedelta(seconds=3),
                note=Note.YBO,
            )
            test_notes_per_second_note_events = [note_event1, note_event2, note_event3]
            got = bare_chart._notes_per_second(
                test_notes_per_second_note_events, interval_start_time, interval_end_time
            )
            assert got == want

        @pytest.mark.parametrize(
            "start_tick,end_tick,want_interval_start_time,want_interval_end_time",
            [
                pytest.param(
                    None,
                    2,
                    datetime.timedelta(0),
                    datetime.timedelta(seconds=2),
                    id="all_start_args_none",
                ),
                pytest.param(
                    1,
                    None,
                    datetime.timedelta(seconds=1),
                    datetime.timedelta(seconds=1000),
                    id="last_none",
                ),
                pytest.param(
                    1,
                    2,
                    datetime.timedelta(seconds=1),
                    datetime.timedelta(seconds=2),
                    id="no_none",
                ),
            ],
        )
        def test_with_ticks(
            self,
            mocker,
            minimal_chart,
            start_tick,
            end_tick,
            want_interval_start_time,
            want_interval_end_time,
        ):
            unsafe.setattr(
                minimal_chart[defaults.instrument][defaults.difficulty],
                "note_events",
                defaults.note_events,
            )

            mocker.patch.object(
                InstrumentTrack,
                "last_note_end_timestamp",
                new_callable=mocker.PropertyMock,
                return_value=want_interval_end_time,
            )

            # NOTE: This _should_ be mocked as such, but because sync_track is a frozen dataclass,
            # it cannot be mocked conventionally.
            # mocker.patch.object(
            #    minimal_chart.sync_track,
            #    "timestamp_at_tick",
            #    side_effect=lambda tick, _resolution: (datetime.timedelta(seconds=tick),),
            # )
            unsafe.setattr(
                minimal_chart.sync_track,
                "timestamp_at_tick",
                lambda tick, _resolution: (datetime.timedelta(seconds=tick),),
            )
            spy = mocker.spy(minimal_chart, "_notes_per_second")
            _ = minimal_chart.notes_per_second(
                defaults.instrument,
                defaults.difficulty,
                start_tick=start_tick,
                end_tick=end_tick,
            )
            spy.assert_called_once_with(
                defaults.note_events, want_interval_start_time, want_interval_end_time
            )

            # NOTE: Manually reset timestamp_at_tick from mocked version.
            unsafe.delattr(
                minimal_chart.sync_track,
                "timestamp_at_tick",
            )

        @pytest.mark.parametrize(
            "start_time,end_time,want_interval_start_time,want_interval_end_time",
            [
                pytest.param(
                    datetime.timedelta(seconds=1),
                    None,
                    datetime.timedelta(seconds=1),
                    datetime.timedelta(seconds=1000),
                    id="last_none",
                ),
                pytest.param(
                    datetime.timedelta(seconds=1),
                    datetime.timedelta(seconds=2),
                    datetime.timedelta(seconds=1),
                    datetime.timedelta(seconds=2),
                    id="no_none",
                ),
            ],
        )
        def test_with_time(
            self,
            mocker,
            minimal_chart,
            start_time,
            end_time,
            want_interval_start_time,
            want_interval_end_time,
        ):
            unsafe.setattr(
                minimal_chart[defaults.instrument][defaults.difficulty],
                "note_events",
                defaults.note_events,
            )

            mocker.patch.object(
                InstrumentTrack,
                "last_note_end_timestamp",
                new_callable=mocker.PropertyMock,
                return_value=want_interval_end_time,
            )

            spy = mocker.spy(minimal_chart, "_notes_per_second")
            _ = minimal_chart.notes_per_second(
                defaults.instrument,
                defaults.difficulty,
                start_time=start_time,
                end_time=end_time,
            )
            spy.assert_called_once_with(
                defaults.note_events, want_interval_start_time, want_interval_end_time
            )

        @pytest.mark.parametrize(
            "start_seconds,end_seconds,want_interval_start_time,want_interval_end_time",
            [
                pytest.param(
                    1,
                    None,
                    datetime.timedelta(seconds=1),
                    datetime.timedelta(seconds=1000),
                    id="last_none",
                ),
                pytest.param(
                    1,
                    2,
                    datetime.timedelta(seconds=1),
                    datetime.timedelta(seconds=2),
                    id="no_none",
                ),
            ],
        )
        def test_with_seconds(
            self,
            mocker,
            minimal_chart,
            start_seconds,
            end_seconds,
            want_interval_start_time,
            want_interval_end_time,
        ):
            unsafe.setattr(
                minimal_chart[defaults.instrument][defaults.difficulty],
                "note_events",
                defaults.note_events,
            )

            mocker.patch.object(
                InstrumentTrack,
                "last_note_end_timestamp",
                new_callable=mocker.PropertyMock,
                return_value=want_interval_end_time,
            )

            spy = mocker.spy(minimal_chart, "_notes_per_second")
            _ = minimal_chart.notes_per_second(
                defaults.instrument,
                defaults.difficulty,
                start_seconds=start_seconds,
                end_seconds=end_seconds,
            )
            spy.assert_called_once_with(
                defaults.note_events, want_interval_start_time, want_interval_end_time
            )

        @pytest.mark.parametrize(
            "start_time,start_tick,start_seconds",
            [
                pytest.param(
                    defaults.timestamp,
                    defaults.tick,
                    None,
                ),
                pytest.param(
                    defaults.timestamp,
                    None,
                    defaults.seconds,
                ),
                pytest.param(
                    None,
                    defaults.tick,
                    defaults.seconds,
                ),
                pytest.param(
                    defaults.timestamp,
                    defaults.tick,
                    defaults.seconds,
                ),
            ],
        )
        def test_too_many_start_args(self, bare_chart, start_time, start_tick, start_seconds):
            with pytest.raises(ValueError):
                _ = bare_chart.notes_per_second(
                    defaults.instrument,
                    defaults.difficulty,
                    start_time=start_time,
                    start_tick=start_tick,
                    start_seconds=start_seconds,
                )

        @pytest.mark.parametrize(
            "instrument,difficulty",
            [
                pytest.param(Instrument.BASS, Difficulty.EXPERT),
                pytest.param(Instrument.GUITAR, Difficulty.MEDIUM),
                pytest.param(Instrument.BASS, Difficulty.MEDIUM),
            ],
        )
        def test_missing_instrument_difficulty(self, default_chart, instrument, difficulty):
            with pytest.raises(ValueError):
                _ = default_chart.notes_per_second(
                    instrument,
                    difficulty,
                )

        def test_empty_note_events(self, bare_chart, minimal_instrument_tracks):
            bare_chart.instrument_tracks = minimal_instrument_tracks
            with pytest.raises(ValueError):
                _ = bare_chart.notes_per_second(
                    defaults.instrument,
                    defaults.difficulty,
                )

    class TestGetItem(object):
        def test(self, default_chart):
            got = default_chart[defaults.instrument][defaults.difficulty]
            want = default_chart.instrument_tracks[defaults.instrument][defaults.difficulty]
            assert got == want
