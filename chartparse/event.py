# TODO: Rename to `events.py`

import re

from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.util import DictPropertiesEqMixin


class Event(object):
    def __init__(self, tick, timestamp=None):
        self.tick = tick
        self.timestamp = timestamp

    def __str__(self):  # pragma: no cover
        to_join = [f"{type(self).__name__: >18}(t@{self.tick:07}"]
        if self.timestamp is not None:
            as_str = (
                str(self.timestamp)
                if self.timestamp.total_seconds() > 0
                else f"{self.timestamp}.000000"
            )
            to_join.append(f" {as_str}")
        to_join.append(")")
        return "".join(to_join)

    def __repr__(self):  # pragma: no cover
        return str(self.__dict__)


class TimeSignatureEvent(Event, DictPropertiesEqMixin):
    # Match 1: Tick
    # Match 2: Upper numeral
    # Match 3: Lower numeral (optional; assumed to be 4 if absent)
    _regex = r"^\s\s(\d+?)\s=\sTS\s(\d+?)(?:\s(\d+?))?$"
    _regex_prog = re.compile(_regex)

    def __init__(self, tick, upper_numeral, lower_numeral, timestamp=None):
        super().__init__(tick, timestamp=timestamp)
        self.upper_numeral = upper_numeral
        self.lower_numeral = lower_numeral

    @classmethod
    def from_chart_line(cls, line):
        m = cls._regex_prog.match(line)
        if not m:
            raise RegexFatalNotMatchError(cls._regex, line)
        tick, upper_numeral = int(m.group(1)), int(m.group(2))
        # For some reason, the lower number is written by Moonscraper as the
        # exponent of whatever power of 2 it is.
        lower_numeral = 2 ** int(m.group(3)) if m.group(3) else 4
        return cls(tick, upper_numeral, lower_numeral)

    def __str__(self):  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": {self.upper_numeral}/{self.lower_numeral}")
        return "".join(to_join)


class BPMEvent(Event):
    # Match 1: Tick
    # Match 2: BPM (the last 3 digits are the decimal places)
    _regex = r"^\s*?(\d+?)\s=\sB\s(\d+?)\s*?$"
    _regex_prog = re.compile(_regex)

    def __init__(self, tick, bpm, timestamp=None):
        super().__init__(tick, timestamp=timestamp)
        self.bpm = bpm

    @classmethod
    def from_chart_line(cls, line):
        m = cls._regex_prog.match(line)
        if not m:
            raise RegexFatalNotMatchError(cls._regex, line)
        tick, raw_bpm = int(m.group(1)), m.group(2)
        bpm_whole_part_str, bpm_decimal_part_str = raw_bpm[:-3], raw_bpm[-3:]
        bpm_whole_part = int(bpm_whole_part_str) if bpm_whole_part_str != "" else 0
        bpm_decimal_part = int(bpm_decimal_part_str) / 1000
        bpm = bpm_whole_part + bpm_decimal_part
        return cls(tick, bpm)

    def __str__(self):  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": {self.bpm} BPM")
        return "".join(to_join)


class StarPowerEvent(Event, DictPropertiesEqMixin):
    # Match 1: Tick
    # Match 2: Note index (Might be always 2? Not sure what this is, to be honest.)
    # Match 3: Duration (ticks)
    _regex = r"^\s*?(\d+?)\s=\sS\s(\d+?)\s(\d+?)\s*?$"
    _regex_prog = re.compile(_regex)

    def __init__(self, tick, duration, timestamp=None):
        super().__init__(tick, timestamp=timestamp)
        self.duration = duration

    @classmethod
    def from_chart_line(cls, line):
        m = cls._regex_prog.match(line)
        if not m:
            raise RegexFatalNotMatchError(cls._regex, line)
        tick, duration = int(m.group(1)), int(m.group(3))
        return cls(tick, duration)

    def __str__(self):  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": duration={self.duration}")
        return "".join(to_join)

    def __repr__(self):  # pragma: no cover
        return str(self.__dict__)


class NoteEvent(Event, DictPropertiesEqMixin):
    # This regex matches a single "N" line within a instrument track section,
    # but this class should be used to represent all of the notes at a
    # particular tick. This means that you might need to consolidate multiple
    # "N" lines into a single NoteEvent, e.g. for chords.
    # Match 1: Tick
    # Match 2: Note index
    # Match 3: Duration (ticks)
    _regex = r"^\s*?(\d+?)\s=\sN\s([0-7])\s(\d+?)\s*?$"
    _regex_prog = re.compile(_regex)

    def __init__(self, tick, note, timestamp=None, duration=0, is_forced=False, is_tap=False):
        self._validate_duration(duration, note)
        super().__init__(tick, timestamp=timestamp)
        self.note = note
        self.duration = self._refine_duration(duration)
        self.is_forced = is_forced
        self.is_tap = is_tap

    @staticmethod
    def _validate_duration(duration, note):
        if isinstance(duration, int):
            NoteEvent._validate_int_duration(duration)
        elif isinstance(duration, list):
            NoteEvent._validate_list_duration(duration, note)
        else:
            raise TypeError(f"duration {duration} must be type list, or int.")

    @staticmethod
    def _validate_int_duration(duration):
        if duration < 0:
            raise ValueError(f"int duration {duration} must be positive.")

    @staticmethod
    def _validate_list_duration(duration, note):
        if len(duration) != len(note.value):
            raise ValueError(f"list duration {duration} must have length {len(note.value)}")
        for note_lane_value, duration_lane_value in zip(note.value, duration):
            lane_is_active = note_lane_value == 1
            duration_is_set = duration_lane_value is not None
            if lane_is_active != duration_is_set:
                raise ValueError(
                    f"list duration {duration} must have "
                    "values for exactly the active note lanes."
                )

    @staticmethod
    def _refine_duration(duration):
        if isinstance(duration, list):
            if all(d is None for d in duration):
                return 0
            first_non_none_duration = next(d for d in duration if d is not None)
            if all(d is None or d == first_non_none_duration for d in duration):
                return first_non_none_duration
        return duration

    def __str__(self):  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": {self.note}")
        if self.duration:
            to_join.append(f" duration={self.duration}")

        flags = []
        if self.is_forced:
            flags.append("F")
        if self.is_tap:
            flags.append("T")
        if flags:
            to_join.extend([" [flags=", "".join(flags), "]"])

        return "".join(to_join)


class EventsEvent(Event, DictPropertiesEqMixin):
    # Match 1: Tick
    # Match 2: Event command
    # Match 3: Event parameters (optional)
    _regex = r"^\s*?(\d+?)\s=\sE\s\"([a-z0-9_]+?)(?:\s(.+?))?\"\s*?$"
    _regex_prog = re.compile(_regex)

    def __init__(self, tick, command, timestamp=None, params=None):
        super().__init__(tick, timestamp=timestamp)
        self.command = command
        self.params = params

    @classmethod
    def from_chart_line(cls, line):
        m = cls._regex_prog.match(line)
        if not m:
            raise RegexFatalNotMatchError(cls._regex, line)
        tick, command, params = int(m.group(1)), m.group(2), m.group(3)
        return cls(tick, command, params=params)

    def __str__(self):  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": {self.command}")
        if self.params:
            to_join.append(f" [params={self.params}]")
        return "".join(to_join)
