import pytest

from chartparse.exceptions import MissingRequiredField, RegexNotMatchError, raise_


class TestRaise(object):
    def test_basic(self):
        with pytest.raises(ValueError):
            raise_(ValueError)

        with pytest.raises(TypeError):
            raise_(TypeError)


class TestMissingRequiredField(object):
    def test_basic(self):
        e = MissingRequiredField("foo")
        assert e.field_name == "foo"
        assert e.message == "unable to find a chart line matching required field 'foo'"


class TestRegexNotMatchError(object):
    def test_regex_only(self):
        e = RegexNotMatchError(r"\d+")
        assert e.regex == r"\d+"
        assert e.message == r"regex '\d+' failed to match"

    def test_regex_and_s(self):
        e = RegexNotMatchError(r"\d+", "foo")
        assert e.regex == r"\d+"
        assert e.message == r"string 'foo' failed to match regex '\d+'"

    def test_regex_and_collection(self):
        e = RegexNotMatchError(r"\d+", ["foo", "bar"])
        assert e.regex == r"\d+"
        assert e.message == r"none of 2 strings matched regex '\d+'"
