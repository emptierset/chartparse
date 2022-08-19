import pytest

from chartparse.exceptions import RegexNotMatchError
from chartparse.track import parse_events_from_chart_lines


class TestParseEventsFromChartLines(object):
    @pytest.mark.parametrize(
        "from_chart_line_return_value,from_chart_line_side_effect,include_tatter,want",
        [
            pytest.param(
                pytest.defaults.time_signature_event,
                None,
                True,
                [pytest.defaults.time_signature_event],
                id="with_timestamp_getter",
            ),
            pytest.param(
                pytest.defaults.bpm_event,
                None,
                False,
                [pytest.defaults.bpm_event],
                id="without_timestamp_getter",
            ),
            pytest.param(
                None,
                RegexNotMatchError(pytest.unmatchable_regex, pytest.invalid_chart_line),
                True,
                [],
                id="event_regex_no_match_ignored",
            ),
            pytest.param(
                None,
                RegexNotMatchError(pytest.unmatchable_regex, pytest.invalid_chart_line),
                False,
                [],
                id="bpm_event_regex_no_match_ignored",
            ),
        ],
    )
    def test(
        self,
        mocker,
        invalid_chart_line,
        minimal_tatter,
        from_chart_line_return_value,
        from_chart_line_side_effect,
        include_tatter,
        want,
    ):
        from_chart_line_fn_mock = mocker.Mock(
            return_value=from_chart_line_return_value, side_effect=from_chart_line_side_effect
        )

        args = [
            [invalid_chart_line],
            from_chart_line_fn_mock,
        ]
        if include_tatter:
            args.append(minimal_tatter)
        else:
            args.append(pytest.defaults.resolution)

        got = parse_events_from_chart_lines(*args)
        assert got == want
