import pytest

from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.track import _parse_events_from_iterable


class TestParseEventsFromIterable(object):
    def test_parse_events_from_iterable(self, generate_valid_bpm_line):
        lines = [generate_valid_bpm_line()]

        def fake_from_chart_line_fn(_):
            return pytest.default_bpm_event

        assert _parse_events_from_iterable(lines, fake_from_chart_line_fn) == [
            pytest.default_bpm_event
        ]

    def test_parse_events_from_iterable_regex_no_match(
        self, invalid_chart_line, unmatchable_regex
    ):
        def fake_from_chart_line(_):
            raise RegexFatalNotMatchError(unmatchable_regex, invalid_chart_line)

        assert _parse_events_from_iterable([invalid_chart_line], fake_from_chart_line) == []
