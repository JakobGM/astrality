"""Tests for the test utils module."""

from .utils import RegexCompare


def test_use_of_regex_compare():
    regex_compare = RegexCompare(r'test')

    assert regex_compare == 'test'
    assert 'test' == regex_compare

    assert not 'ttest' == regex_compare


def test_more_complicated_regex_comparisons():
    regex_compare = RegexCompare(r'\[Compiling\] .+test\.template"')

    assert regex_compare == '[Compiling] something "/a/b/c/test.template"'
    assert not regex_compare == '[Compiling] something "/a/b/c/test.templates"'
