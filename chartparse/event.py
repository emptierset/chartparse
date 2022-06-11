# TODO: Rename to `events.py`

import re

from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.util import DictPropertiesEqMixin, DictReprMixin


class Event(DictPropertiesEqMixin, DictReprMixin):
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


class DurationedEvent(Event):
    def __init__(self, tick, duration, timestamp=None):
        super().__init__(tick, timestamp=timestamp)
        self.duration = duration

    def __str__(self):  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": duration={self.duration}")
        return "".join(to_join)


class TimeSignatureEvent(Event):
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
