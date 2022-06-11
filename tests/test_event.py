import pytest

from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.event import BPMEvent, TimeSignatureEvent


class TestTimeSignatureEvent(object):
    def test_init(self, time_signature_event):
        assert time_signature_event.upper_numeral == pytest.default_upper_time_signature_numeral
        assert time_signature_event.lower_numeral == pytest.default_lower_time_signature_numeral

    def test_from_chart_line_short(self, generate_valid_short_time_signature_line):
        line = generate_valid_short_time_signature_line()
        event = TimeSignatureEvent.from_chart_line(line)
        assert event.tick == pytest.default_tick
        assert event.upper_numeral == pytest.default_upper_time_signature_numeral

    def test_from_chart_line_long(self, generate_valid_long_time_signature_line):
        line = generate_valid_long_time_signature_line()
        event = TimeSignatureEvent.from_chart_line(line)
        assert event.tick == pytest.default_tick
        assert event.upper_numeral == pytest.default_upper_time_signature_numeral
        assert event.lower_numeral == pytest.default_lower_time_signature_numeral

    def test_from_chart_line_no_match(self, generate_valid_bpm_line):
        line = generate_valid_bpm_line()
        with pytest.raises(RegexFatalNotMatchError):
            _ = TimeSignatureEvent.from_chart_line(line)


class TestBPMEvent(object):
    def test_init(self, bpm_event):
        assert bpm_event.bpm == pytest.default_bpm

    def test_from_chart_line(self, generate_valid_bpm_line):
        line = generate_valid_bpm_line()
        event = BPMEvent.from_chart_line(line)
        assert event.tick == pytest.default_tick
        assert event.bpm == pytest.default_bpm

    def test_from_chart_line_no_match(self, generate_valid_short_time_signature_line):
        line = generate_valid_short_time_signature_line()
        with pytest.raises(RegexFatalNotMatchError):
            _ = BPMEvent.from_chart_line(line)
