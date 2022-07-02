import pytest

from chartparse.exceptions import RegexNotMatchError


class TestParseEventsFromIterable(object):
    def test_parse_events_from_iterable(self, bare_event_track, generate_valid_bpm_line):
        lines = [generate_valid_bpm_line()]

        def fake_from_chart_line_fn(_):
            return pytest.default_bpm_event

        assert bare_event_track._parse_events_from_chart_lines(lines, fake_from_chart_line_fn) == [
            pytest.default_bpm_event
        ]

    def test_parse_events_from_iterable_regex_no_match(
        self, bare_event_track, invalid_chart_line, unmatchable_regex
    ):
        def fake_from_chart_line_fn(_):
            raise RegexNotMatchError(unmatchable_regex, invalid_chart_line)

        events = bare_event_track._parse_events_from_chart_lines(
            [invalid_chart_line], fake_from_chart_line_fn
        )
        assert len(events) == 0
