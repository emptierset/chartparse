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
