from flexmock import flexmock

from borgmatic.commands import arguments as module


def test_parse_subparser_arguments_consumes_subparser_arguments_before_subparser_name():
    global_namespace = flexmock()
    action_namespace = flexmock(foo=True)
    top_level_parser = flexmock(parse_args=lambda arguments: global_namespace)
    subparsers = flexmock(
        choices={
            'action': flexmock(parse_known_args=lambda arguments: (action_namespace, [])),
            'other': flexmock(),
        }
    )

    arguments = module.parse_subparser_arguments(
        ('--foo', 'true', 'action'), top_level_parser, subparsers
    )

    assert arguments == {'action': action_namespace, 'global': global_namespace}


def test_parse_subparser_arguments_consumes_subparser_arguments_after_subparser_name():
    global_namespace = flexmock()
    action_namespace = flexmock(foo=True)
    top_level_parser = flexmock(parse_args=lambda arguments: global_namespace)
    subparsers = flexmock(
        choices={
            'action': flexmock(parse_known_args=lambda arguments: (action_namespace, [])),
            'other': flexmock(),
        }
    )

    arguments = module.parse_subparser_arguments(
        ('action', '--foo', 'true'), top_level_parser, subparsers
    )

    assert arguments == {'action': action_namespace, 'global': global_namespace}


def test_parse_subparser_arguments_consumes_global_arguments_before_subparser_name():
    global_namespace = flexmock(verbosity='lots')
    action_namespace = flexmock()
    top_level_parser = flexmock(parse_args=lambda arguments: global_namespace)
    subparsers = flexmock(
        choices={
            'action': flexmock(
                parse_known_args=lambda arguments: (action_namespace, ['--verbosity', 'lots'])
            ),
            'other': flexmock(),
        }
    )

    arguments = module.parse_subparser_arguments(
        ('--verbosity', 'lots', 'action'), top_level_parser, subparsers
    )

    assert arguments == {'action': action_namespace, 'global': global_namespace}


def test_parse_subparser_arguments_consumes_global_arguments_after_subparser_name():
    global_namespace = flexmock(verbosity='lots')
    action_namespace = flexmock()
    top_level_parser = flexmock(parse_args=lambda arguments: global_namespace)
    subparsers = flexmock(
        choices={
            'action': flexmock(
                parse_known_args=lambda arguments: (action_namespace, ['--verbosity', 'lots'])
            ),
            'other': flexmock(),
        }
    )

    arguments = module.parse_subparser_arguments(
        ('action', '--verbosity', 'lots'), top_level_parser, subparsers
    )

    assert arguments == {'action': action_namespace, 'global': global_namespace}


def test_parse_subparser_arguments_consumes_subparser_arguments_with_alias():
    global_namespace = flexmock()
    action_namespace = flexmock(foo=True)
    top_level_parser = flexmock(parse_args=lambda arguments: global_namespace)
    action_subparser = flexmock(parse_known_args=lambda arguments: (action_namespace, []))
    subparsers = flexmock(
        choices={
            'action': action_subparser,
            '-a': action_subparser,
            'other': flexmock(),
            '-o': flexmock(),
        }
    )
    flexmock(module).SUBPARSER_ALIASES = {'action': ['-a'], 'other': ['-o']}

    arguments = module.parse_subparser_arguments(
        ('-a', '--foo', 'true'), top_level_parser, subparsers
    )

    assert arguments == {'action': action_namespace, 'global': global_namespace}


def test_parse_subparser_arguments_consumes_multiple_subparser_arguments():
    global_namespace = flexmock()
    action_namespace = flexmock(foo=True)
    other_namespace = flexmock(bar=3)
    top_level_parser = flexmock(parse_args=lambda arguments: global_namespace)
    subparsers = flexmock(
        choices={
            'action': flexmock(
                parse_known_args=lambda arguments: (action_namespace, ['--bar', '3'])
            ),
            'other': flexmock(parse_known_args=lambda arguments: (other_namespace, [])),
        }
    )

    arguments = module.parse_subparser_arguments(
        ('action', '--foo', 'true', 'other', '--bar', '3'), top_level_parser, subparsers
    )

    assert arguments == {
        'action': action_namespace,
        'other': other_namespace,
        'global': global_namespace,
    }


def test_parse_subparser_arguments_applies_default_subparsers():
    global_namespace = flexmock()
    prune_namespace = flexmock()
    create_namespace = flexmock(progress=True)
    check_namespace = flexmock()
    top_level_parser = flexmock(parse_args=lambda arguments: global_namespace)
    subparsers = flexmock(
        choices={
            'prune': flexmock(parse_known_args=lambda arguments: (prune_namespace, ['--progress'])),
            'create': flexmock(parse_known_args=lambda arguments: (create_namespace, [])),
            'check': flexmock(parse_known_args=lambda arguments: (check_namespace, [])),
            'other': flexmock(),
        }
    )

    arguments = module.parse_subparser_arguments(('--progress'), top_level_parser, subparsers)

    assert arguments == {
        'prune': prune_namespace,
        'create': create_namespace,
        'check': check_namespace,
        'global': global_namespace,
    }


def test_parse_subparser_arguments_with_help_does_not_apply_default_subparsers():
    global_namespace = flexmock(verbosity='lots')
    action_namespace = flexmock()
    top_level_parser = flexmock(parse_args=lambda arguments: global_namespace)
    subparsers = flexmock(
        choices={
            'action': flexmock(
                parse_known_args=lambda arguments: (action_namespace, ['--verbosity', 'lots'])
            ),
            'other': flexmock(),
        }
    )

    arguments = module.parse_subparser_arguments(
        ('--verbosity', 'lots', '--help'), top_level_parser, subparsers
    )

    assert arguments == {'global': global_namespace}
