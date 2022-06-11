import pytest

from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.globalevents import GlobalEvent, TextEvent, SectionEvent, LyricEvent


class TestGlobalEventsTrack(object):
    def test_init(self, basic_global_events_track):
        assert basic_global_events_track.text_events == pytest.default_text_event_list
        assert basic_global_events_track.section_events == pytest.default_section_event_list
        assert basic_global_events_track.lyric_events == pytest.default_lyric_event_list


class TestGlobalEvent(object):
    def test_init(self):
        event = GlobalEvent(pytest.default_tick, pytest.default_global_event_value)
        assert event.value == pytest.default_global_event_value

    def test_from_chart_line_not_implemented(self, invalid_chart_line):
        with pytest.raises(NotImplementedError):
            _ = GlobalEvent.from_chart_line(invalid_chart_line)


class TestTextEvent(object):
    def test_from_chart_line(self, generate_valid_text_event_line):
        line = generate_valid_text_event_line()
        event = TextEvent.from_chart_line(line)
        assert event.tick == pytest.default_tick
        assert event.value == pytest.default_text_event_value

    def test_from_chart_line_no_match(self, invalid_chart_line):
        with pytest.raises(RegexFatalNotMatchError):
            _ = TextEvent.from_chart_line(invalid_chart_line)


class TestSectionEvent(object):
    def test_from_chart_line(self, generate_valid_section_event_line):
        line = generate_valid_section_event_line()
        event = SectionEvent.from_chart_line(line)
        assert event.tick == pytest.default_tick
        assert event.value == pytest.default_section_event_value

    def test_from_chart_line_no_match(self, invalid_chart_line):
        with pytest.raises(RegexFatalNotMatchError):
            _ = SectionEvent.from_chart_line(invalid_chart_line)


class TestLyricEvent(object):
    def test_from_chart_line(self, generate_valid_lyric_event_line):
        line = generate_valid_lyric_event_line()
        event = LyricEvent.from_chart_line(line)
        assert event.tick == pytest.default_tick
        assert event.value == pytest.default_lyric_event_value

    def test_from_chart_line_no_match(self, invalid_chart_line):
        with pytest.raises(RegexFatalNotMatchError):
            _ = LyricEvent.from_chart_line(invalid_chart_line)
