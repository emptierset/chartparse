"""For functionality relating to tick arithmetic.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import functools
import typing as typ
from enum import Enum

from chartparse.time import Seconds

Tick = typ.NewType("Tick", int)
"""A specific tick-moment in a chart."""


Ticks = typ.NewType("Ticks", int)
"""A duration measured in ticks."""


def add(a: Tick, b: Ticks) -> Tick:
    """Returns the tick value at ``a + b``.

    Args:
        a: A tick moment.
        b: A number of ticks.
    """
    return Tick(a + b)


def sum(a: Ticks, b: Ticks) -> Ticks:
    """Returns the number of ticks in ``a + b``.

    Args:
        a: A number of ticks.
        b: A number of ticks.
    """
    return Ticks(a + b)  # pragma: no cover


def difference(a: Ticks, b: Ticks) -> Ticks:
    """Returns the number of ticks in ``a - b``.

    Args:
        a: A number of ticks.
        b: A number of ticks.
    """
    return Ticks(a - b)  # pragma: no cover


def between(a: Tick, b: Tick) -> Ticks:
    """Returns the number of ticks in ``b - a``.

    Args:
        a: A tick moment.
        b: A tick moment.
    """
    # TODO: Should this be absolute value?
    return Ticks(b - a)


@typ.final
class NoteDuration(Enum):
    """The note durations supported by Moonscraper.

    The enum values are the number of that type of note in one
    :attr:`~chartparse.metadata.Metadata.resolution`\\'s worth of ticks.
    """

    @staticmethod
    def _int_if_possible(f: float) -> float | int:
        if (i := int(f)) == f:
            return i
        return f

    WHOLE = _int_if_possible(2 ** (-2))
    HALF = _int_if_possible(2 ** (-1))
    QUARTER = _int_if_possible(2**0)
    EIGHTH = _int_if_possible(2**1)
    SIXTEENTH = _int_if_possible(2**2)
    THIRTY_SECOND = _int_if_possible(2**3)
    SIXTY_FOURTH = _int_if_possible(2**4)
    HUNDRED_TWENTY_EIGHTH = _int_if_possible(2**5)
    TWO_HUNDRED_FIFTH_SIXTH = _int_if_possible(2**6)
    FIVE_HUNDRED_TWELFTH = _int_if_possible(2**7)

    THIRD = _int_if_possible(
        (HALF + QUARTER) / 2,
    )
    SIXTH = _int_if_possible(
        (QUARTER + EIGHTH) / 2,
    )
    TWELFTH = _int_if_possible(
        (EIGHTH + SIXTEENTH) / 2,
    )
    TWENTY_FOURTH = _int_if_possible(
        (SIXTEENTH + THIRTY_SECOND) / 2,
    )
    FOURTY_EIGHTH = _int_if_possible(
        (THIRTY_SECOND + SIXTY_FOURTH) / 2,
    )
    NINETY_SIXTH = _int_if_possible(
        (SIXTY_FOURTH + HUNDRED_TWENTY_EIGHTH) / 2,
    )
    HUNDRED_NINETY_SECOND = _int_if_possible(
        (HUNDRED_TWENTY_EIGHTH + TWO_HUNDRED_FIFTH_SIXTH) / 2,
    )
    THREE_HUNDRED_EIGHTY_FOURTH = _int_if_possible(
        (TWO_HUNDRED_FIFTH_SIXTH + FIVE_HUNDRED_TWELFTH) / 2
    )
    SEVEN_HUNDRED_SIXTY_EIGHTH = _int_if_possible(
        (FIVE_HUNDRED_TWELFTH + FIVE_HUNDRED_TWELFTH * 2) / 2
    )

    # Aliases

    HALF_TRIPLET = THIRD
    QUARTER_TRIPLET = SIXTH
    EIGHTH_TRIPLET = TWELFTH
    SIXTEENTH_TRIPLET = TWENTY_FOURTH
    THIRTY_SECOND_TRIPLET = FOURTY_EIGHTH
    SIXTY_FOURTH_TRIPLET = NINETY_SIXTH
    HUNDRED_TWENTY_EIGHTH_TRIPLET = HUNDRED_NINETY_SECOND
    TWO_HUNDRED_FIFTH_SIXTH_TRIPLET = THREE_HUNDRED_EIGHTY_FOURTH
    FIVE_HUNDRED_TWELFTH_TRIPLET = SEVEN_HUNDRED_SIXTY_EIGHTH


@functools.lru_cache
def note_duration_to_ticks(resolution: Ticks, note_duration: NoteDuration) -> Ticks:
    """Returns the number of ticks between two notes of a particular note value.

    I do not know whether Moonscraper rounds or truncates when ``resolution`` does not divide
    evenly. The vast majority of charts have a ``resolution`` of exactly ``192``, so this is mostly
    a nonissue, because ``192`` is divided evenly by every note value.

    Args:
        resolution: The number of ticks in a quarter note.
        note_duration: The note duration for which the tick interval should be computed.

    Returns: The number of ticks between two notes of a particular note value.

    """
    return Ticks(round(resolution / note_duration.value))


def seconds_from_ticks_at_bpm(ticks: Ticks, bpm: float, resolution: Ticks) -> Seconds:
    """Returns the number of seconds that elapse over some number of ticks at a particular tempo.

    Args:
        ticks: The number of ticks for which the duration should be calculated.
        bpm: The tempo.
        resolution: The number of ticks in a quarter note.

    Returns: The number of seconds that elapse over ``ticks`` ticks at tempo ``bpm`` and resolution
    ``resolution``.
    """
    if ticks < 0:
        raise ValueError(f"ticks {ticks} must be non-negative")
    if bpm <= 0:
        raise ValueError(f"bpm {bpm} must be positive")
    if resolution <= 0:
        raise ValueError(f"resolution {resolution} must be positive")
    ticks_per_minute = bpm * resolution
    ticks_per_second = ticks_per_minute / 60
    seconds_per_tick = 1 / ticks_per_second
    return Seconds(ticks * seconds_per_tick)
