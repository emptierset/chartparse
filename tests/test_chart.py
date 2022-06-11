import datetime
import pathlib
import pytest

from chartparse.chart import Chart
from chartparse.enums import Difficulty, Instrument, Note
from chartparse.event import NoteEvent


_directory_of_this_file = pathlib.Path(__file__).parent.resolve()
_chart_directory_filepath = _directory_of_this_file / "data"
_valid_chart_filepath = _chart_directory_filepath / "test.chart"
_missing_metadata_chart_filepath = _chart_directory_filepath / "missing_metadata.chart"
_missing_resolution_chart_filepath = _chart_directory_filepath / "missing_resolution.chart"
_missing_sync_track_chart_filepath = _chart_directory_filepath / "missing_sync_track.chart"


class TestChartInit(object):
    def test_init(self):
        with open(_valid_chart_filepath, "r", encoding="utf-8-sig") as f:
            c = Chart(f)

        assert c.metadata is not None

        def validate_timestamps(got_events, want_timestamps):
            assert len(got_events) == len(want_timestamps)
            for got_event, want_timestamp in zip(got_events, want_timestamps):
                assert got_event.timestamp == want_timestamp

        validate_timestamps(
            c.global_events_track.events,
            [
                datetime.timedelta(seconds=4, microseconds=102564),
                datetime.timedelta(seconds=5, microseconds=102564),
                datetime.timedelta(seconds=6, microseconds=102564),
                datetime.timedelta(seconds=6, microseconds=302564),
                datetime.timedelta(seconds=10, microseconds=102564),
                datetime.timedelta(seconds=10, microseconds=342564),
            ],
        )

        validate_timestamps(
            c.sync_track.time_signature_events,
            [datetime.timedelta(0), datetime.timedelta(seconds=6, microseconds=102564)],
        )
        validate_timestamps(
            c.sync_track.bpm_events,
            [
                datetime.timedelta(0),
                datetime.timedelta(seconds=4, microseconds=102564),
                datetime.timedelta(seconds=6, microseconds=102564),
                datetime.timedelta(seconds=10, microseconds=102564),
            ],
        )

        instrument_track = c.instrument_tracks[Instrument.GUITAR][Difficulty.EXPERT]
        validate_timestamps(
            instrument_track.note_events,
            [
                datetime.timedelta(seconds=4, microseconds=102564),
                datetime.timedelta(seconds=4, microseconds=227564),
                datetime.timedelta(seconds=4, microseconds=602564),
                datetime.timedelta(seconds=5, microseconds=102564),
                datetime.timedelta(seconds=5, microseconds=602564),
                datetime.timedelta(seconds=5, microseconds=852564),
                datetime.timedelta(seconds=6, microseconds=102564),
                datetime.timedelta(seconds=6, microseconds=269231),
                datetime.timedelta(seconds=6, microseconds=769231),
                datetime.timedelta(seconds=11, microseconds=302564),
            ],
        )
        validate_timestamps(
            instrument_track.star_power_events,
            [
                datetime.timedelta(seconds=5, microseconds=102564),
                datetime.timedelta(seconds=6, microseconds=102564),
            ],
        )

    @pytest.mark.parametrize(
        "path",
        [
            pytest.param(_missing_metadata_chart_filepath, id="missing_metadata"),
            pytest.param(_missing_resolution_chart_filepath, id="missing_resolution"),
            pytest.param(_missing_sync_track_chart_filepath, id="missing_sync_track"),
        ],
    )
    def test_invalid_chart(self, path):
        with open(path, "r", encoding="utf-8-sig") as f, pytest.raises(ValueError):
            _ = Chart(f)


class TestSecondsFromTicksAtBPM(object):
    @pytest.mark.parametrize(
        "ticks,bpm,resolution,want",
        [
            pytest.param(100, 60, 100, 1),
            pytest.param(100, 120, 100, 0.5),
            pytest.param(200, 120, 100, 1),
            pytest.param(400, 200, 100, 1.2),
        ],
    )
    def test_basic(self, basic_chart, ticks, bpm, resolution, want):
        basic_chart.metadata.resolution = resolution
        assert basic_chart._seconds_from_ticks_at_bpm(ticks, bpm) == want

    @pytest.mark.parametrize(
        "ticks,bpm,resolution",
        [
            pytest.param(100, -1, 192, id="negative_bpm"),
            pytest.param(100, 0, 192, id="zero_bpm"),
        ],
    )
    def test_error(self, basic_chart, ticks, bpm, resolution):
        with pytest.raises(ValueError):
            _ = basic_chart._seconds_from_ticks_at_bpm(ticks, bpm)


class TestNotesPerSecond(object):
    @pytest.mark.parametrize(
        "events,want",
        [
            pytest.param(
                [
                    NoteEvent(
                        pytest.default_tick,
                        pytest.default_note,
                        timestamp=datetime.timedelta(seconds=0),
                    ),
                    NoteEvent(
                        pytest.default_tick,
                        pytest.default_note,
                        timestamp=datetime.timedelta(seconds=1),
                    ),
                ],
                2,
            ),
            pytest.param(
                [
                    NoteEvent(
                        pytest.default_tick,
                        pytest.default_note,
                        timestamp=datetime.timedelta(seconds=15),
                    ),
                    NoteEvent(
                        pytest.default_tick,
                        pytest.default_note,
                        timestamp=datetime.timedelta(seconds=18.5),
                    ),
                    NoteEvent(
                        pytest.default_tick,
                        pytest.default_note,
                        timestamp=datetime.timedelta(seconds=20.5),
                    ),
                ],
                3 / 5.5,
            ),
        ],
    )
    def test_from_note_events(self, basic_chart, events, want):
        assert basic_chart._notes_per_second_from_note_events(events) == want

    note_event1 = NoteEvent(0, pytest.default_note, timestamp=datetime.timedelta(seconds=5))
    note_event2 = NoteEvent(1, pytest.default_note, timestamp=datetime.timedelta(seconds=15))
    note_event3 = NoteEvent(2, pytest.default_note, timestamp=datetime.timedelta(seconds=25))
    notes_per_second_note_events = [note_event1, note_event2, note_event3]

    @pytest.mark.parametrize(
        "start_tick,end_tick,want",
        [
            pytest.param(1, None, [note_event2, note_event3]),
            pytest.param(1, 2, [note_event2, note_event3]),
            pytest.param(0, 2, [note_event1, note_event2, note_event3]),
        ],
    )
    def test_with_ticks(self, mocker, basic_chart, start_tick, end_tick, want):
        basic_chart.instrument_tracks[pytest.default_instrument][
            pytest.default_difficulty
        ].note_events = self.notes_per_second_note_events
        spy = mocker.spy(basic_chart, "_notes_per_second_from_note_events")
        _ = basic_chart.notes_per_second(
            pytest.default_instrument,
            pytest.default_difficulty,
            start_tick=start_tick,
            end_tick=end_tick,
        )
        spy.assert_called_once_with(want)

    @pytest.mark.parametrize(
        "start_time,end_time,want",
        [
            pytest.param(datetime.timedelta(seconds=10), None, [note_event2, note_event3]),
            pytest.param(
                datetime.timedelta(seconds=10),
                datetime.timedelta(seconds=30),
                [note_event2, note_event3],
            ),
            pytest.param(
                datetime.timedelta(seconds=0),
                datetime.timedelta(seconds=30),
                [note_event1, note_event2, note_event3],
            ),
        ],
    )
    def test_with_time(self, mocker, basic_chart, start_time, end_time, want):
        basic_chart.instrument_tracks[pytest.default_instrument][
            pytest.default_difficulty
        ].note_events = self.notes_per_second_note_events
        spy = mocker.spy(basic_chart, "_notes_per_second_from_note_events")
        _ = basic_chart.notes_per_second(
            pytest.default_instrument,
            pytest.default_difficulty,
            start_time=start_time,
            end_time=end_time,
        )
        spy.assert_called_once_with(want)

    @pytest.mark.parametrize(
        "start_seconds,end_seconds,want",
        [
            pytest.param(10, None, [note_event2, note_event3]),
            pytest.param(10, 30, [note_event2, note_event3]),
            pytest.param(0, 30, [note_event1, note_event2, note_event3]),
        ],
    )
    def test_with_seconds(self, mocker, basic_chart, start_seconds, end_seconds, want):
        basic_chart.instrument_tracks[pytest.default_instrument][
            pytest.default_difficulty
        ].note_events = self.notes_per_second_note_events
        spy = mocker.spy(basic_chart, "_notes_per_second_from_note_events")
        _ = basic_chart.notes_per_second(
            pytest.default_instrument,
            pytest.default_difficulty,
            start_seconds=start_seconds,
            end_seconds=end_seconds,
        )
        spy.assert_called_once_with(want)

    @pytest.mark.parametrize(
        "start_seconds,end_seconds",
        [
            pytest.param(30, None),
            pytest.param(30, 40),
            pytest.param(20, 30),
        ],
    )
    def test_insufficient_number_of_note_events(self, basic_chart, start_seconds, end_seconds):
        basic_chart.instrument_tracks[pytest.default_instrument][
            pytest.default_difficulty
        ].note_events = self.notes_per_second_note_events
        with pytest.raises(ValueError):
            _ = basic_chart.notes_per_second(
                pytest.default_instrument,
                pytest.default_difficulty,
                start_seconds=start_seconds,
                end_seconds=end_seconds,
            )

    @pytest.mark.parametrize(
        "start_time,start_tick,start_seconds",
        [
            pytest.param(datetime.timedelta(0), 0, None),
            pytest.param(datetime.timedelta(0), None, 0),
            pytest.param(None, 0, 0),
            pytest.param(datetime.timedelta(0), 0, 0),
        ],
    )
    def test_too_many_start_args(self, basic_chart, start_time, start_tick, start_seconds):
        with pytest.raises(ValueError):
            _ = basic_chart.notes_per_second(
                pytest.default_instrument,
                pytest.default_difficulty,
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
    def test_missing_instrument_difficulty(self, basic_chart, instrument, difficulty):
        with pytest.raises(ValueError):
            _ = basic_chart.notes_per_second(
                instrument,
                difficulty,
                start_tick=0,
            )
