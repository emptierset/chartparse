import pytest

from chartparse.exceptions import RegexNotMatchError
from chartparse.track import parse_events_from_chart_lines


class TestParseEventsFromChartLines(object):
    @pytest.mark.parametrize(
        "from_chart_line_return_value,from_chart_line_side_effect,include_timestamp_getter,want",
        [
            pytest.param(
                pytest.default_time_signature_event,
                None,
                True,
                [pytest.default_time_signature_event],
                id="with_timestamp_getter",
            ),
            pytest.param(
                pytest.default_bpm_event,
                None,
                False,
                [pytest.default_bpm_event],
                id="without_timestamp_getter",
            ),
            pytest.param(
                None,
                RegexNotMatchError(pytest.unmatchable_regex, pytest.invalid_chart_line),
                True,
                [],
                id="regex_no_match_ignored",
            ),
        ],
    )
    def test_basic(
        self,
        mocker,
        invalid_chart_line,
        minimal_timestamp_getter,
        from_chart_line_return_value,
        from_chart_line_side_effect,
        include_timestamp_getter,
        want,
    ):
        from_chart_line_fn_mock = mocker.Mock(
            return_value=from_chart_line_return_value, side_effect=from_chart_line_side_effect
        )

        args = [
            pytest.default_resolution,
            [invalid_chart_line],
            from_chart_line_fn_mock,
        ]
        if include_timestamp_getter:
            args.append(minimal_timestamp_getter)

        got = parse_events_from_chart_lines(*args)
        assert got == want
