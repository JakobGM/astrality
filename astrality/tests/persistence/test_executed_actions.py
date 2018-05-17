"""Tests for astrality.persistence.ExecutedActions."""

import logging

from astrality.persistence import ExecutedActions


def test_that_executed_action_path_is_monkeypatched_in_all_files():
    """Autouse fixture should monkeypatch path property of ExecutedActions."""
    executed_actions = ExecutedActions(module_name='github::user/repo::module')
    path = executed_actions.path
    assert path.is_file()
    assert path.name == 'setup.yml'
    assert path.parent.name == 'astrality'
    assert 'test' in path.parents[3].name


def test_that_actions_are_saved_to_file(caplog):
    """Saved actions should be persisted properly."""
    action_option = {'shell': 'echo setup'}
    executed_actions = ExecutedActions(module_name='github::user/repo::module')

    # This action has not been executed yet.
    assert executed_actions.is_new(
        action_type='run',
        action_options=action_option,
    )

    # We save checked actions, and now it should count as executed.
    executed_actions.write()
    assert not executed_actions.is_new(
        action_type='run',
        action_options=action_option,
    )

    # The action should still be counted as executed between object lifetimes.
    del executed_actions
    executed_actions = ExecutedActions(module_name='github::user/repo::module')
    assert not executed_actions.is_new(
        action_type='run',
        action_options=action_option,
    )

    # But when we reset the module, it should be counted as new
    del executed_actions
    executed_actions = ExecutedActions(module_name='github::user/repo::module')

    caplog.clear()
    executed_actions.reset()
    assert executed_actions.is_new(
        action_type='run',
        action_options=action_option,
    )

    # Check that info is logged on success
    assert caplog.record_tuples[0][1] == logging.INFO

    # It should also be reset after loading from disk again
    executed_actions.reset()
    del executed_actions
    executed_actions = ExecutedActions(module_name='github::user/repo::module')
    assert executed_actions.is_new(
        action_type='run',
        action_options=action_option,
    )

    # Check that error is logged on invalid module name
    caplog.clear()
    ExecutedActions(module_name='i_do_not_exist').reset()
    assert caplog.record_tuples[0][1] == logging.ERROR
