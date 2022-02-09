from flexmock import flexmock

from borgmatic.commands import arguments as module


def test_parse_subparser_arguments_consumes_subparser_arguments_before_subparser_name():
    action_namespace = flexmock(foo=True)
    subparsers = {
        'action': flexmock(parse_known_args=lambda arguments: (action_namespace, ['action'])),
        'other': flexmock(),
    }

    arguments, remaining_arguments = module.parse_subparser_arguments(
        ('--foo', 'true', 'action'), subparsers
    )

    assert arguments == {'action': action_namespace}
    assert remaining_arguments == []


def test_parse_subparser_arguments_consumes_subparser_arguments_after_subparser_name():
    action_namespace = flexmock(foo=True)
    subparsers = {
        'action': flexmock(parse_known_args=lambda arguments: (action_namespace, ['action'])),
        'other': flexmock(),
    }

    arguments, remaining_arguments = module.parse_subparser_arguments(
        ('action', '--foo', 'true'), subparsers
    )

    assert arguments == {'action': action_namespace}
    assert remaining_arguments == []


def test_parse_subparser_arguments_consumes_subparser_arguments_with_alias():
    action_namespace = flexmock(foo=True)
    action_subparser = flexmock(parse_known_args=lambda arguments: (action_namespace, ['action']))
    subparsers = {
        'action': action_subparser,
        '-a': action_subparser,
        'other': flexmock(),
        '-o': flexmock(),
    }
    flexmock(module).SUBPARSER_ALIASES = {'action': ['-a'], 'other': ['-o']}

    arguments, remaining_arguments = module.parse_subparser_arguments(
        ('-a', '--foo', 'true'), subparsers
    )

    assert arguments == {'action': action_namespace}
    assert remaining_arguments == []


def test_parse_subparser_arguments_consumes_multiple_subparser_arguments():
    action_namespace = flexmock(foo=True)
    other_namespace = flexmock(bar=3)
    subparsers = {
        'action': flexmock(
            parse_known_args=lambda arguments: (action_namespace, ['action', '--bar', '3'])
        ),
        'other': flexmock(parse_known_args=lambda arguments: (other_namespace, [])),
    }

    arguments, remaining_arguments = module.parse_subparser_arguments(
        ('action', '--foo', 'true', 'other', '--bar', '3'), subparsers
    )

    assert arguments == {'action': action_namespace, 'other': other_namespace}
    assert remaining_arguments == []


def test_parse_subparser_arguments_applies_default_subparsers():
    prune_namespace = flexmock()
    compact_namespace = flexmock()
    create_namespace = flexmock(progress=True)
    check_namespace = flexmock()
    subparsers = {
        'prune': flexmock(
            parse_known_args=lambda arguments: (prune_namespace, ['prune', '--progress'])
        ),
        'compact': flexmock(parse_known_args=lambda arguments: (compact_namespace, [])),
        'create': flexmock(parse_known_args=lambda arguments: (create_namespace, [])),
        'check': flexmock(parse_known_args=lambda arguments: (check_namespace, [])),
        'other': flexmock(),
    }

    arguments, remaining_arguments = module.parse_subparser_arguments(('--progress'), subparsers)

    assert arguments == {
        'prune': prune_namespace,
        'compact': compact_namespace,
        'create': create_namespace,
        'check': check_namespace,
    }
    assert remaining_arguments == []


def test_parse_subparser_arguments_passes_through_unknown_arguments_before_subparser_name():
    action_namespace = flexmock()
    subparsers = {
        'action': flexmock(
            parse_known_args=lambda arguments: (action_namespace, ['action', '--verbosity', 'lots'])
        ),
        'other': flexmock(),
    }

    arguments, remaining_arguments = module.parse_subparser_arguments(
        ('--verbosity', 'lots', 'action'), subparsers
    )

    assert arguments == {'action': action_namespace}
    assert remaining_arguments == ['--verbosity', 'lots']


def test_parse_subparser_arguments_passes_through_unknown_arguments_after_subparser_name():
    action_namespace = flexmock()
    subparsers = {
        'action': flexmock(
            parse_known_args=lambda arguments: (action_namespace, ['action', '--verbosity', 'lots'])
        ),
        'other': flexmock(),
    }

    arguments, remaining_arguments = module.parse_subparser_arguments(
        ('action', '--verbosity', 'lots'), subparsers
    )

    assert arguments == {'action': action_namespace}
    assert remaining_arguments == ['--verbosity', 'lots']


def test_parse_subparser_arguments_parses_borg_options_and_skips_other_subparsers():
    action_namespace = flexmock(options=[])
    subparsers = {
        'borg': flexmock(parse_known_args=lambda arguments: (action_namespace, ['borg', 'list'])),
        'list': flexmock(),
    }

    arguments, remaining_arguments = module.parse_subparser_arguments(('borg', 'list'), subparsers)

    assert arguments == {'borg': action_namespace}
    assert arguments['borg'].options == ['list']
    assert remaining_arguments == []
