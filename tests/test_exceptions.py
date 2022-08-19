import pytest

from chartparse.exceptions import MissingRequiredField, RegexNotMatchError, ProgrammerError, raise_


class TestRaise(object):
    def test(self):
        with pytest.raises(ValueError):
            raise_(ValueError)

        with pytest.raises(TypeError):
            raise_(TypeError)


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

    def test_regex_and_s(self):
        got = RegexNotMatchError(r"\d+", "foo")
        assert got.regex == r"\d+"
        assert got.message == r"string 'foo' failed to match regex '\d+'"

    def test_regex_and_collection(self):
        got = RegexNotMatchError(r"\d+", ["foo", "bar"])
        assert got.regex == r"\d+"
        assert got.message == r"none of 2 strings matched regex '\d+'"


class TestProgrammerError(object):
    def test(self):
        got = ProgrammerError()
        assert got.message == ProgrammerError.message
