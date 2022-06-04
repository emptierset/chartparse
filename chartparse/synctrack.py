import re

import chartparse.event
import chartparse.track

from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.event import Event
from chartparse.util import DictPropertiesEqMixin


class SyncTrack(DictPropertiesEqMixin):
    def __init__(self, iterator_getter):
        self.time_signature_events = chartparse.track.parse_events_from_iterable(
                iterator_getter(), TimeSignatureEvent.from_chart_line)
        if self.time_signature_events[0].tick != 0:
            raise ValueError(f"first TimeSignatureEvent {self.time_signature_events[0]} must have tick 0")

        self.bpm_events = chartparse.track.parse_events_from_iterable(
                iterator_getter(), BPMEvent.from_chart_line)
        if self.bpm_events[0].tick != 0:
            raise ValueError(f"first BPMEvent {self.bpm_events[0]} must have tick 0")


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
        lower_numeral = 2**int(m.group(3)) if m.group(3) else 4
        return cls(tick, upper_numeral, lower_numeral)

    def __str__(self):  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": {self.upper_numeral}/{self.lower_numeral}")
        return ''.join(to_join)

    def __repr__(self):
        return str(self.__dict__)  # pragma: no cover


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
        bpm_decimal_part = int(bpm_decimal_part_str)/1000
        bpm = bpm_whole_part + bpm_decimal_part
        return cls(tick, bpm)

    def __str__(self):  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": {self.bpm} BPM")
        return ''.join(to_join)

    def __repr__(self):
        return str(self.__dict__)  # pragma: no cover


