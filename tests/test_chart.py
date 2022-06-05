import datetime
import pathlib
import pytest

from chartparse.chart import Chart
from chartparse.enums import Difficulty, Instrument


_directory_of_this_file = pathlib.Path(__file__).parent.resolve()
_chart_directory_filepath = _directory_of_this_file / "data"
_valid_chart_filepath = _chart_directory_filepath / "test.chart"
_missing_properties_chart_filepath = _chart_directory_filepath / "missing_properties.chart"
_missing_resolution_chart_filepath = _chart_directory_filepath / "missing_resolution.chart"
_missing_sync_track_chart_filepath = _chart_directory_filepath / "missing_sync_track.chart"


class TestChart(object):
    def test_init(self):
        with open(_valid_chart_filepath, "r", encoding="utf-8-sig") as f:
            c = Chart(f)

        assert c.properties is not None

        def validate_timestamps(got_events, want_timestamps):
            assert len(got_events) == len(want_timestamps)
            for got_event, want_timestamp in zip(got_events, want_timestamps):
                assert got_event.timestamp == want_timestamp

        validate_timestamps(
            c.events_track.events,
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

    @pytest.mark.parametrize("path", [
        pytest.param(_missing_properties_chart_filepath, id="missing_properties"),
        pytest.param(_missing_resolution_chart_filepath, id="missing_resolution"),
        pytest.param(_missing_sync_track_chart_filepath, id="missing_sync_track"),
    ])
    def test_init_invalid_chart(self, path):
        with open(path, "r", encoding="utf-8-sig") as f, pytest.raises(ValueError):
            _ = Chart(f)

    @pytest.mark.parametrize(
        "ticks,bpm,resolution,want",
        [
            pytest.param(100, 60, 100, 1),
            pytest.param(100, 120, 100, 0.5),
            pytest.param(200, 120, 100, 1),
            pytest.param(400, 200, 100, 1.2),
        ],
    )
    def test_seconds_from_ticks(self, basic_chart, ticks, bpm, resolution, want):
        basic_chart.properties.resolution = resolution
        assert basic_chart._seconds_from_ticks(ticks, bpm) == want

    @pytest.mark.parametrize(
        "ticks,bpm,resolution",
        [
            pytest.param(100, -1, 192, id="negative_bpm"),
            pytest.param(100, 0, 192, id="zero_bpm"),
        ],
    )
    def test_seconds_from_ticks_raises_ValueError(self, basic_chart, ticks, bpm, resolution):
        with pytest.raises(ValueError):
            _ = basic_chart._seconds_from_ticks(ticks, bpm)
