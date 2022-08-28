import pytest

from chartparse.exceptions import RegexNotMatchError
from chartparse.track import parse_events_from_chart_lines
from chartparse.sync import BPMEvent


class TestParseEventsFromChartLines(object):
    @pytest.mark.parametrize(
        "from_chart_line_return_value,from_chart_line_side_effect,want",
        [
            pytest.param(
                pytest.defaults.time_signature_event,
                None,
                [pytest.defaults.time_signature_event],
                id="with_timestamp_getter",
            ),
            pytest.param(
                pytest.defaults.bpm_event,
                None,
                [pytest.defaults.bpm_event],
                id="without_timestamp_getter",
            ),
            pytest.param(
                None,
                RegexNotMatchError(pytest.unmatchable_regex, pytest.invalid_chart_line),
                [],
                id="event_regex_no_match_ignored",
            ),
            pytest.param(
                None,
                RegexNotMatchError(pytest.unmatchable_regex, pytest.invalid_chart_line),
                [],
                id="bpm_event_regex_no_match_ignored",
            ),
        ],
    )
    def test(
        self,
        mocker,
        invalid_chart_line,
        default_tatter,
        from_chart_line_return_value,
        from_chart_line_side_effect,
        want,
    ):
        from_chart_line_fn_mock = mocker.Mock(
            return_value=from_chart_line_return_value, side_effect=from_chart_line_side_effect
        )
        if isinstance(from_chart_line_return_value, BPMEvent):
            resolution_or_tatter = pytest.defaults.resolution
        else:
            resolution_or_tatter = default_tatter

        got = parse_events_from_chart_lines(
            [invalid_chart_line], from_chart_line_fn_mock, resolution_or_tatter
        )

        assert got == want
        from_chart_line_fn_mock.assert_called_once_with(
            invalid_chart_line, None, resolution_or_tatter
        )
