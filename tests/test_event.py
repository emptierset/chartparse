import pytest
import re

from chartparse.event import Event, FromChartLineMixin
from chartparse.exceptions import RegexFatalNotMatchError


_test_regex = r"^T (\d+?) V (.*?)$"


class TestFromChartLineMixin(object):
    def teardown_method(self):
        try:
            del FromChartLineMixin._regex
            del FromChartLineMixin._regex_prog
        except AttributeError:
            pass

    def test_from_chart_line_not_implemented(self, mocker):
        with pytest.raises(NotImplementedError):
            _ = FromChartLineMixin.from_chart_line("")

    def test_from_chart_line(self, mocker):
        FromChartLineMixin._regex = _test_regex
        FromChartLineMixin._regex_prog = re.compile(FromChartLineMixin._regex)

        mock_init = mocker.patch.object(FromChartLineMixin, "__init__", return_value=None)
        _ = FromChartLineMixin.from_chart_line(
            f"T {pytest.default_tick} V {pytest.default_global_event_value}"
        )
        mock_init.assert_called_once_with(pytest.default_tick, pytest.default_global_event_value)

    def test_from_chart_line_no_match(self, invalid_chart_line):
        FromChartLineMixin._regex = _test_regex
        FromChartLineMixin._regex_prog = re.compile(FromChartLineMixin._regex)

        with pytest.raises(RegexFatalNotMatchError):
            _ = FromChartLineMixin.from_chart_line(invalid_chart_line)


class TestEvent(object):
    def test_init(self, tick_having_event):
        assert tick_having_event.tick == pytest.default_tick

    def test_init_with_timestamp(self):
        e = Event(pytest.default_tick, pytest.default_timestamp)
        assert e.timestamp == pytest.default_timestamp
