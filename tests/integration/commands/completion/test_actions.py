import borgmatic.commands.arguments
from borgmatic.commands.completion import actions as module


def test_available_actions_uses_only_subactions_for_action_with_subactions():
    unused_top_level_parser, subparsers = borgmatic.commands.arguments.make_parsers()

    actions = module.available_actions(subparsers, 'config')

    assert 'bootstrap' in actions
    assert 'list' not in actions


def test_available_actions_omits_subactions_for_action_without_subactions():
    unused_top_level_parser, subparsers = borgmatic.commands.arguments.make_parsers()

    actions = module.available_actions(subparsers, 'list')

    assert 'bootstrap' not in actions
    assert 'config' in actions
