from astrality import compiler

import pytest


@pytest.fixture
def context_config():
    return {
        'module/whatever': {},
        'nonsenical_entry': 5,
        'context/general': {
            'font': 'comic sans',
            'monitor': 'HDMI1',
        },
        'context/colors': {
            'foreground': 'white',
            'background': 'black',
            1: 'white',
            2: 'black',
        },
    }


@pytest.fixture
def context(context_config):
    return compiler.context(context_config)


def test_context_contents(context):
    assert context == {
        'general': {
            'font': 'comic sans',
            'monitor': 'HDMI1',
        },
        'colors': {
            'foreground': 'white',
            'background': 'black',
            1: 'white',
            2: 'black',
        },
    }


def test_context_integer_index_resolution(context):
    assert context['colors'][3] == 'black'


def test_context_initialization_with_no_context_blocks():
    application_config = {'module/whatever': {'timer': {'type': 'solar'}}}
    assert compiler.context(application_config) == {}
