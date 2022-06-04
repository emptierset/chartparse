import pytest
import re
import unittest.mock

from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.track import parse_events_from_iterable


def _fake_from_chart_line(_):
    return pytest.default_bpm_event


def test_parse_events_from_iterable(mocker, generate_valid_bpm_line):
    lines = [generate_valid_bpm_line()]
    assert parse_events_from_iterable(lines, _fake_from_chart_line) == [pytest.default_bpm_event]


def test_parse_events_from_iterable_regex_no_match(mocker, invalid_chart_line, unmatchable_regex):
    def fake_from_chart_line(_):
        raise RegexFatalNotMatchError(unmatchable_regex, invalid_chart_line)
    assert parse_events_from_iterable([invalid_chart_line], fake_from_chart_line) == []
