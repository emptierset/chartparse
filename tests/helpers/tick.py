import chartparse.tick

from tests.helpers import defaults


def calculate_ticks_between_notes_with_defaults(
    note_duration,
    *,
    resolution=defaults.resolution,
):
    return chartparse.tick.calculate_ticks_between_notes(resolution, note_duration)
