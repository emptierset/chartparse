import pytest

import chartparse.tick


def calculate_ticks_between_notes_with_defaults(
    note_duration,
    *,
    resolution=pytest.defaults.resolution,
):
    return chartparse.tick.calculate_ticks_between_notes(resolution, note_duration)
