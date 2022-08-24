import datetime
import pathlib
import pytest

from chartparse.chart import Chart, _max_timedelta
from chartparse.exceptions import RegexNotMatchError
from chartparse.globalevents import GlobalEventsTrack
from chartparse.instrument import InstrumentTrack, Difficulty, Instrument, Note
from chartparse.metadata import Metadata
from chartparse.sync import SyncTrack

from tests.helpers.constructors import NoteEventWithDefaults
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
            mock_populate_event_hopo_states = mocker.patch.object(
                Chart, "_populate_note_event_hopo_states"
            )
            mock_populate_last_note_timestamp = mocker.patch.object(
                Chart, "_populate_last_note_timestamp"
            )
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

            mock_populate_event_hopo_states.assert_called_once_with(
                default_instrument_track.note_events
            )
            mock_populate_last_note_timestamp.assert_called_once_with(default_instrument_track)

    class TestFromFileAndFilepath(object):
        def test(
            self,
            mocker,
            minimal_string_iterator_getter,
            default_chart,
            default_metadata,
            default_global_events_track,
            default_sync_track,
            default_instrument_track,
        ):
            mocker.patch.object(
                Chart,
                "_find_sections",
                return_value={
                    "Song": minimal_string_iterator_getter,
                    "Events": minimal_string_iterator_getter,
                    "SyncTrack": minimal_string_iterator_getter,
                    "ExpertSingle": minimal_string_iterator_getter,
                },
            )
            mocker.patch.object(Metadata, "from_chart_lines", return_value=default_metadata)
            mocker.patch.object(
                GlobalEventsTrack, "from_chart_lines", return_value=default_global_events_track
            )
            mocker.patch.object(SyncTrack, "from_chart_lines", return_value=default_sync_track)
            mocker.patch.object(
                InstrumentTrack, "from_chart_lines", return_value=default_instrument_track
            )
            with open(_valid_chart_filepath, "r", encoding="utf-8-sig") as f:
                got_from_file = Chart.from_file(f)
            got_from_filepath = Chart.from_filepath(_valid_chart_filepath)

            assert got_from_file == default_chart
            assert got_from_filepath == default_chart

        @pytest.mark.parametrize(
            "path",
            [
                pytest.param(_missing_metadata_chart_filepath, id="missing_metadata"),
                pytest.param(_missing_sync_track_chart_filepath, id="missing_sync_track"),
                pytest.param(
                    _missing_global_events_track_chart_filepath, id="missing_global_events_track"
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
                lines_getter = sections[section_name]
                assert list(lines_getter()) == want_lines

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
                ["Song]", "{", '  Name = "Song Name"', "}"],
                ["[Song]", "{", '  Name = "Song Name"', "}", "[ExpertSingle"],
            ],
        )
        def test_raises(self, lines):
            with pytest.raises(RegexNotMatchError):
                _ = Chart._find_sections(lines)

    class TestPopulateNoteEventHOPOStates(object):
        def test(self, mocker, minimal_chart):
            note_event1 = NoteEventWithDefaults(tick=0, note=Note.G)
            note_event2 = NoteEventWithDefaults(tick=pytest.defaults.resolution, note=Note.R)
            note_event3 = NoteEventWithDefaults(
                tick=pytest.defaults.resolution + pytest.defaults.resolution * 2,
                note=Note.Y,
            )
            note_events = [note_event1, note_event2, note_event3]

            mock_populate_hopo_state1 = mocker.patch.object(note_event1, "_populate_hopo_state")
            mock_populate_hopo_state2 = mocker.patch.object(note_event2, "_populate_hopo_state")
            mock_populate_hopo_state3 = mocker.patch.object(note_event3, "_populate_hopo_state")

            minimal_chart._populate_note_event_hopo_states(note_events)

            mock_populate_hopo_state1.assert_called_once_with(pytest.defaults.resolution, None)
            mock_populate_hopo_state2.assert_called_once_with(
                pytest.defaults.resolution, note_event1
            )
            mock_populate_hopo_state3.assert_called_once_with(
                pytest.defaults.resolution, note_event2
            )

        def test_empty(self, minimal_chart):
            note_events = []
            minimal_chart._populate_note_event_hopo_states(note_events)
            assert len(note_events) == 0

    class TestPopulateLastNoteTimestamp(object):
        @pytest.mark.parametrize(
            "note_events,want_tick",
            [
                pytest.param(
                    [NoteEventWithDefaults(tick=1)],
                    1,
                    id="one_event",
                ),
                pytest.param(
                    [
                        NoteEventWithDefaults(
                            tick=1,
                        ),
                        NoteEventWithDefaults(tick=2),
                    ],
                    2,
                    id="two_events",
                ),
                pytest.param(
                    [NoteEventWithDefaults(tick=1, sustain=2)],
                    3,
                    id="event_with_sustain",
                ),
                pytest.param(
                    [
                        NoteEventWithDefaults(
                            tick=1,
                            note=Note.G,
                            sustain=3,
                        ),
                        NoteEventWithDefaults(
                            tick=2,
                            note=Note.R,
                        ),
                    ],
                    4,
                    id="event_with_sustain_through_note",
                ),
            ],
        )
        def test(self, mocker, minimal_chart, note_events, want_tick):
            mock_timestamp_at_tick = mocker.patch.object(
                minimal_chart.sync_track,
                "timestamp_at_tick",
                return_value=(pytest.defaults.timestamp, None),
            )
            # TODO: Make it simpler to fetch the only instrument track when there is only one.
            track = minimal_chart[pytest.defaults.instrument][pytest.defaults.difficulty]
            track.note_events = note_events
            minimal_chart._populate_last_note_timestamp(track)
            mock_timestamp_at_tick.assert_called_once_with(want_tick, start_bpm_event_index=0)
            assert track._last_note_timestamp == pytest.defaults.timestamp

        def test_empty(self, mocker, minimal_chart):
            mock = mocker.patch.object(
                minimal_chart.sync_track, "timestamp_at_tick", return_value=(None, None)
            )
            track = minimal_chart[pytest.defaults.instrument][pytest.defaults.difficulty]
            minimal_chart._populate_last_note_timestamp(track)
            mock.assert_not_called()

    class TestSecondsFromTicksAtBPM(object):
        def test(self, mocker, minimal_chart):
            mock = mocker.patch("chartparse.tick.seconds_from_ticks_at_bpm")
            _ = minimal_chart._seconds_from_ticks_at_bpm(pytest.defaults.tick, pytest.defaults.bpm)
            mock.assert_called_once_with(
                pytest.defaults.tick, pytest.defaults.bpm, pytest.defaults.resolution
            )

    class TestNotesPerSecond(object):
        note_event1 = NoteEventWithDefaults(
            tick=pytest.defaults.resolution,
            timestamp=datetime.timedelta(seconds=1),
            note=Note.GRY,
        )
        note_event2 = NoteEventWithDefaults(
            tick=pytest.defaults.resolution * 2,
            timestamp=datetime.timedelta(seconds=2),
            note=Note.RYB,
        )
        note_event3 = NoteEventWithDefaults(
            tick=pytest.defaults.resolution * 3,
            timestamp=datetime.timedelta(seconds=3),
            note=Note.YBO,
        )
        test_notes_per_second_note_events = [note_event1, note_event2, note_event3]

        @pytest.mark.parametrize(
            "lower_bound,upper_bound,want",
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
        def test_from_note_events(self, bare_chart, lower_bound, upper_bound, want):
            got = bare_chart._notes_per_second(
                self.test_notes_per_second_note_events, lower_bound, upper_bound
            )
            assert got == want

        @pytest.mark.parametrize(
            "start_tick,end_tick,want_lower_bound,want_upper_bound",
            [
                pytest.param(
                    None,
                    2,
                    datetime.timedelta(0),
                    datetime.timedelta(seconds=2),
                    id="all_start_args_none",
                ),
                pytest.param(
                    1, None, datetime.timedelta(seconds=1), _max_timedelta, id="last_none"
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
            self, mocker, minimal_chart, start_tick, end_tick, want_lower_bound, want_upper_bound
        ):
            track = minimal_chart[pytest.defaults.instrument][pytest.defaults.difficulty]
            track._last_note_timestamp = _max_timedelta
            minimal_chart.instrument_tracks = {
                pytest.defaults.instrument: {
                    pytest.defaults.difficulty: track,
                }
            }

            def tick_to_bound(tick):
                return datetime.timedelta(seconds=tick)

            def timestamp_at_tick_side_effect(tick, _resolution):
                return (tick_to_bound(tick),)

            mocker.patch.object(
                minimal_chart.sync_track,
                "timestamp_at_tick",
                side_effect=timestamp_at_tick_side_effect,
            )
            spy = mocker.spy(minimal_chart, "_notes_per_second")
            _ = minimal_chart.notes_per_second(
                pytest.defaults.instrument,
                pytest.defaults.difficulty,
                start_tick=start_tick,
                end_tick=end_tick,
            )
            spy.assert_called_once_with([], want_lower_bound, want_upper_bound)

        @pytest.mark.parametrize(
            "start_time,end_time,want_lower_bound,want_upper_bound",
            [
                pytest.param(
                    datetime.timedelta(seconds=1),
                    None,
                    datetime.timedelta(seconds=1),
                    _max_timedelta,
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
            self, mocker, minimal_chart, start_time, end_time, want_lower_bound, want_upper_bound
        ):
            track = minimal_chart[pytest.defaults.instrument][pytest.defaults.difficulty]
            track._last_note_timestamp = _max_timedelta
            spy = mocker.spy(minimal_chart, "_notes_per_second")
            _ = minimal_chart.notes_per_second(
                pytest.defaults.instrument,
                pytest.defaults.difficulty,
                start_time=start_time,
                end_time=end_time,
            )
            spy.assert_called_once_with([], want_lower_bound, want_upper_bound)

        @pytest.mark.parametrize(
            "start_seconds,end_seconds,want_lower_bound,want_upper_bound",
            [
                pytest.param(
                    1,
                    None,
                    datetime.timedelta(seconds=1),
                    _max_timedelta,
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
            want_lower_bound,
            want_upper_bound,
        ):
            track = minimal_chart[pytest.defaults.instrument][pytest.defaults.difficulty]
            track._last_note_timestamp = _max_timedelta
            spy = mocker.spy(minimal_chart, "_notes_per_second")
            _ = minimal_chart.notes_per_second(
                pytest.defaults.instrument,
                pytest.defaults.difficulty,
                start_seconds=start_seconds,
                end_seconds=end_seconds,
            )
            spy.assert_called_once_with([], want_lower_bound, want_upper_bound)

        @pytest.mark.parametrize(
            "start_time,start_tick,start_seconds",
            [
                pytest.param(datetime.timedelta(0), 0, None),
                pytest.param(datetime.timedelta(0), None, 0),
                pytest.param(None, 0, 0),
                pytest.param(datetime.timedelta(0), 0, 0),
            ],
        )
        def test_too_many_start_args(self, bare_chart, start_time, start_tick, start_seconds):
            with pytest.raises(ValueError):
                _ = bare_chart.notes_per_second(
                    pytest.defaults.instrument,
                    pytest.defaults.difficulty,
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
                    start_tick=0,
                )

    class TestGetItem(object):
        def test(self, default_chart):
            got = default_chart[pytest.defaults.instrument][pytest.defaults.difficulty]
            want = default_chart.instrument_tracks[pytest.defaults.instrument][
                pytest.defaults.difficulty
            ]
            assert got == want
