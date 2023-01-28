from __future__ import annotations

import pytest

from chartparse.exceptions import (
    MissingRequiredField,
    RegexNotMatchError,
    UnreachableError,
    raise_,
)

# TODO: typecheck the tests in this file by adding "-> None" annotations to each test function.

class TestRaise(object):
    def test(self):
        with pytest.raises(ValueError):
            raise_(ValueError)


class TestMissingRequiredField(object):
    def test(self):
        got = MissingRequiredField("foo")
        assert got.field_name == "foo"
        assert got.message == "unable to find a chart line matching required field 'foo'"


class TestRegexNotMatchError(object):
    def test_regex_only(self):
        got = RegexNotMatchError(r"\d+")
        assert got.regex == r"\d+"
        assert got.message == r"regex '\d+' failed to match"

    def test_regex_and_s(self, invalid_chart_line):
        got = RegexNotMatchError(r"\d+", invalid_chart_line)
        assert got.regex == r"\d+"
        assert got.message == rf"string '{invalid_chart_line}' failed to match regex '\d+'"

    def test_regex_and_collection(self, invalid_chart_line):
        got = RegexNotMatchError(r"\d+", [invalid_chart_line, invalid_chart_line])
        assert got.regex == r"\d+"
        assert got.message == r"none of 2 strings matched regex '\d+'"


class TestUnreachableError(object):
    def test(self):
        reason = "can't be reached"
        got = UnreachableError(reason)
        assert got.message == reason
