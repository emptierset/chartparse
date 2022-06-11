import pytest

from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.enums import Note
from chartparse.event import BPMEvent, TimeSignatureEvent, StarPowerEvent, NoteEvent
from chartparse.globalevents import GlobalEvent


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


class TestStarPowerEvent(object):
    def test_init(self, star_power_event):
        assert star_power_event.duration == pytest.default_duration

    def test_from_chart_line(self, generate_valid_star_power_line):
        line = generate_valid_star_power_line()
        event = StarPowerEvent.from_chart_line(line)
        assert event.tick == pytest.default_tick
        assert event.duration == pytest.default_duration

    def test_from_chart_line_no_match(self, generate_valid_note_line):
        line = generate_valid_note_line()
        with pytest.raises(RegexFatalNotMatchError):
            _ = StarPowerEvent.from_chart_line(line)


class TestNoteEvent(object):
    def test_init(self, note_event_with_all_optionals_set):
        assert note_event_with_all_optionals_set.note == pytest.default_note
        assert note_event_with_all_optionals_set.duration == pytest.default_duration
        assert note_event_with_all_optionals_set.is_forced == True
        assert note_event_with_all_optionals_set.is_tap == True

    def test_validate_duration(self):
        NoteEvent._validate_duration(0, Note.G)
        NoteEvent._validate_duration([100, None, None, None, None], Note.G)
        with pytest.raises(TypeError):
            NoteEvent._validate_duration((100, None, None, None, None), Note.G)

    def test_validate_int_duration_negative(self):
        with pytest.raises(ValueError):
            NoteEvent._validate_int_duration(-1)

    @pytest.mark.parametrize(
        "duration, note",
        [
            pytest.param(
                [None, None, None, None], pytest.default_note, id="incorrect_length_list"
            ),
            pytest.param([100, 100, None, None, None], Note.G, id="mismatched_set_lanes"),
        ],
    )
    def test_validate_list_duration_raises_ValueError(self, duration, note):
        with pytest.raises(ValueError):
            NoteEvent._validate_list_duration(duration, note)

    @pytest.mark.parametrize(
        "duration, want",
        [
            pytest.param([None, None, None, None, None], 0, id="all_none"),
            pytest.param([100, None, None, 100, None], 100, id="all_the_same"),
            pytest.param(100, 100, id="int_pass_through"),
            pytest.param(
                [100, 0, None, None, None], [100, 0, None, None, None], id="list_pass_through"
            ),
        ],
    )
    def test_refine_duration(self, duration, want):
        assert NoteEvent._refine_duration(duration) == want
