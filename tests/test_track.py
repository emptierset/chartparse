import pytest

import chartparse.track
from chartparse.exceptions import RegexNotMatchError
from chartparse.track import parse_events_from_data, parse_data_from_chart_lines
from chartparse.sync import BPMEvent

from tests.helpers.fruit import Fruit
from tests.helpers.log import LogChecker


class TestParseEventsFromData(object):
    @pytest.mark.parametrize(
        "from_data_return_value,want",
        [
            pytest.param(
                pytest.defaults.time_signature_event,
                [pytest.defaults.time_signature_event],
                id="with_timestamp_getter",
            ),
            pytest.param(
                pytest.defaults.bpm_event,
                [pytest.defaults.bpm_event],
                id="without_timestamp_getter",
            ),
        ],
    )
    def test(
        self,
        mocker,
        invalid_chart_line,
        default_tatter,
        from_data_return_value,
        want,
    ):
        from_data_fn_mock = mocker.Mock(return_value=from_data_return_value)
        if isinstance(from_data_return_value, BPMEvent):
            resolution_or_tatter = pytest.defaults.resolution
        else:
            resolution_or_tatter = default_tatter

        got = parse_events_from_data(
            pytest.invalid_chart_lines, from_data_fn_mock, resolution_or_tatter
        )

        assert got == want
        from_data_fn_mock.assert_called_once_with(invalid_chart_line, None, resolution_or_tatter)


class TestParseDataFromChartLines(object):
    def test(self):
        class AppleReturner(object):
            class ParsedData(object):
                def from_chart_line(_line):
                    return Fruit.APPLE

        class RegexNotMatchErrorRaiser(object):
            class ParsedData(object):
                def from_chart_line(_line):
                    raise RegexNotMatchError(pytest.unmatchable_regex, pytest.invalid_chart_line)

        got = parse_data_from_chart_lines(
            (RegexNotMatchErrorRaiser, AppleReturner), pytest.invalid_chart_lines
        )
        want = {AppleReturner: [Fruit.APPLE]}

        assert got == want

    def test_no_suitable_parsers(self, mocker, caplog):
        _ = parse_data_from_chart_lines(tuple(), pytest.invalid_chart_lines)
        logchecker = LogChecker(caplog)
        logchecker.assert_contains_string_in_one_line(
            chartparse.track._unparsable_line_msg_tmpl.format(pytest.invalid_chart_line)
        )
