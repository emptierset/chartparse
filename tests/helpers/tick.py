import chartparse.tick
from chartparse.tick import NoteDuration, Ticks
from tests.helpers import defaults


def calculate_ticks_between_notes_with_defaults(
    note_duration: NoteDuration,
    *,
    resolution: Ticks = defaults.resolution,
) -> Ticks:
    return chartparse.tick.calculate_ticks_between_notes(resolution, note_duration)
