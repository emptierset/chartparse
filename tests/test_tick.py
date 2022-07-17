import pytest

import chartparse.tick

from chartparse.tick import NoteDuration


class TestCalculateTicksBetweenNotes(object):
    @pytest.mark.parametrize(
        "resolution,note_duration,want",
        [
            pytest.param(100, NoteDuration.QUARTER, 100),
            pytest.param(192, NoteDuration.QUARTER, 192),
            pytest.param(192, NoteDuration.EIGHTH, 96),
            pytest.param(192, NoteDuration.EIGHTH_TRIPLET, 64),
            pytest.param(192, NoteDuration.SIXTEENTH_TRIPLET, 32),
        ],
    )
    def test_basic(self, resolution, note_duration, want):
        assert chartparse.tick.calculate_ticks_between_notes(resolution, note_duration) == want


# TODO: Add "id" (and pytest.param where still missing) everywhere.
# TODO: Refactor all asserts to assign to a local variable `got` first. It makes output prettier.
# TODO: Refactor tests that do not need class enclosures to not use classes. Particularly, this is
# the classes that just contain a single test_basic and possibly a test_error.
class TestSecondsFromTicksAtBPM(object):
    @pytest.mark.parametrize(
        "ticks,bpm,resolution,want",
        [
            pytest.param(100, 60, 100, 1),
            pytest.param(100, 120, 100, 0.5),
            pytest.param(200, 120, 100, 1),
            pytest.param(400, 200, 100, 1.2),
            pytest.param(100, 60, 200, 0.5),
        ],
    )
    def test_basic(self, ticks, bpm, resolution, want):
        got = chartparse.tick.seconds_from_ticks_at_bpm(ticks, bpm, resolution)
        assert got == want

    @pytest.mark.parametrize(
        "ticks,bpm,resolution",
        [
            pytest.param(pytest.default_tick, -1, 192, id="negative_bpm"),
            pytest.param(pytest.default_tick, 0, 192, id="zero_bpm"),
            pytest.param(pytest.default_tick, 120.000, -1, id="negative_resolution"),
            pytest.param(pytest.default_tick, 120.000, 0, id="zero_resolution"),
        ],
    )
    def test_error(self, ticks, bpm, resolution):
        with pytest.raises(ValueError):
            _ = chartparse.tick.seconds_from_ticks_at_bpm(ticks, bpm, resolution)
