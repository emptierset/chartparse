import chartparse.tick
from chartparse.tick import NoteDuration, Ticks
from tests.helpers import defaults


def note_duration_to_ticks(
    note_duration: NoteDuration,
    *,
    resolution: Ticks = defaults.resolution,
) -> Ticks:
    return chartparse.tick.note_duration_to_ticks(resolution, note_duration)
