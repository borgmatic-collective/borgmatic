import collections

import pytest
from flexmock import flexmock

from borgmatic.commands import arguments as module


def test_get_subaction_parsers_with_no_subactions_returns_empty_result():
    assert module.get_subaction_parsers(flexmock(_subparsers=None)) == {}


def test_get_subaction_parsers_with_subactions_returns_one_entry_per_subaction():
    foo_parser = flexmock()
    bar_parser = flexmock()
    baz_parser = flexmock()

    assert module.get_subaction_parsers(
        flexmock(
            _subparsers=flexmock(
                _group_actions=(
                    flexmock(choices={'foo': foo_parser, 'bar': bar_parser}),
                    flexmock(choices={'baz': baz_parser}),
                )
            )
        )
    ) == {'foo': foo_parser, 'bar': bar_parser, 'baz': baz_parser}


def test_get_subactions_for_actions_with_no_subactions_returns_empty_result():
    assert module.get_subactions_for_actions({'action': flexmock(_subparsers=None)}) == {}


def test_get_subactions_for_actions_with_subactions_returns_one_entry_per_action():
    assert module.get_subactions_for_actions(
        {
            'action': flexmock(
                _subparsers=flexmock(
                    _group_actions=(
                        flexmock(choices={'foo': flexmock(), 'bar': flexmock()}),
                        flexmock(choices={'baz': flexmock()}),
                    )
                )
            ),
            'other': flexmock(
                _subparsers=flexmock(_group_actions=(flexmock(choices={'quux': flexmock()}),))
            ),
        }
    ) == {'action': ('foo', 'bar', 'baz'), 'other': ('quux',)}


def test_omit_values_colliding_with_action_names_drops_action_names_that_have_been_parsed_as_values():
    assert module.omit_values_colliding_with_action_names(
        ('check', '--only', 'extract', '--some-list', 'borg'),
        {'check': flexmock(only='extract', some_list=['borg'])},
    ) == ('check', '--only', '--some-list')


def test_omit_values_colliding_twice_with_action_names_drops_action_names_that_have_been_parsed_as_values():
    assert module.omit_values_colliding_with_action_names(
        ('config', 'bootstrap', '--local-path', '--remote-path', 'borg'),
        {'bootstrap': flexmock(local_path='borg', remote_path='borg')},
    ) == ('config', 'bootstrap', '--local-path', '--remote-path')


def test_parse_and_record_action_arguments_without_action_name_leaves_arguments_untouched():
    unparsed_arguments = ('--foo', '--bar')
    flexmock(module).should_receive('omit_values_colliding_with_action_names').and_return(
        unparsed_arguments
    )

    assert (
        module.parse_and_record_action_arguments(
            unparsed_arguments, flexmock(), flexmock(), 'action'
        )
        == unparsed_arguments
    )


def test_parse_and_record_action_arguments_updates_parsed_arguments_and_returns_remaining():
    unparsed_arguments = ('action', '--foo', '--bar', '--verbosity', '1')
    other_parsed_arguments = flexmock()
    parsed_arguments = {'other': other_parsed_arguments}
    action_parsed_arguments = flexmock()
    flexmock(module).should_receive('omit_values_colliding_with_action_names').and_return(
        unparsed_arguments
    )
    action_parser = flexmock()
    flexmock(action_parser).should_receive('parse_known_args').and_return(
        action_parsed_arguments, ('action', '--verbosity', '1')
    )

    assert module.parse_and_record_action_arguments(
        unparsed_arguments, parsed_arguments, action_parser, 'action'
    ) == ('--verbosity', '1')
    assert parsed_arguments == {'other': other_parsed_arguments, 'action': action_parsed_arguments}


def test_parse_and_record_action_arguments_with_alias_updates_canonical_parsed_arguments():
    unparsed_arguments = ('action', '--foo', '--bar', '--verbosity', '1')
    other_parsed_arguments = flexmock()
    parsed_arguments = {'other': other_parsed_arguments}
    action_parsed_arguments = flexmock()
    flexmock(module).should_receive('omit_values_colliding_with_action_names').and_return(
        unparsed_arguments
    )
    action_parser = flexmock()
    flexmock(action_parser).should_receive('parse_known_args').and_return(
        action_parsed_arguments, ('action', '--verbosity', '1')
    )

    assert module.parse_and_record_action_arguments(
        unparsed_arguments, parsed_arguments, action_parser, 'action', canonical_name='doit'
    ) == ('--verbosity', '1')
    assert parsed_arguments == {'other': other_parsed_arguments, 'doit': action_parsed_arguments}


def test_parse_and_record_action_arguments_with_borg_action_consumes_arguments_after_action_name():
    unparsed_arguments = ('--verbosity', '1', 'borg', 'list')
    parsed_arguments = {}
    borg_parsed_arguments = flexmock(options=flexmock())
    flexmock(module).should_receive('omit_values_colliding_with_action_names').and_return(
        unparsed_arguments
    )
    borg_parser = flexmock()
    flexmock(borg_parser).should_receive('parse_known_args').and_return(
        borg_parsed_arguments, ('--verbosity', '1', 'borg', 'list')
    )

    assert module.parse_and_record_action_arguments(
        unparsed_arguments,
        parsed_arguments,
        borg_parser,
        'borg',
    ) == ('--verbosity', '1')
    assert parsed_arguments == {'borg': borg_parsed_arguments}
    assert borg_parsed_arguments.options == ('list',)


@pytest.mark.parametrize(
    'argument, expected',
    [
        ('--foo', True),
        ('foo', False),
        (33, False),
    ],
)
def test_argument_is_flag_only_for_string_starting_with_double_dash(argument, expected):
    assert module.argument_is_flag(argument) == expected


@pytest.mark.parametrize(
    'arguments, expected',
    [
        # Ending with a valueless flag.
        (
            ('--foo', '--bar', 33, '--baz'),
            (
                ('--foo',),
                ('--bar', 33),
                ('--baz',),
            ),
        ),
        # Ending with a flag and its corresponding value.
        (
            ('--foo', '--bar', 33, '--baz', '--quux', 'thing'),
            (('--foo',), ('--bar', 33), ('--baz',), ('--quux', 'thing')),
        ),
        # Starting with an action name.
        (
            ('check', '--foo', '--bar', 33, '--baz'),
            (
                ('check',),
                ('--foo',),
                ('--bar', 33),
                ('--baz',),
            ),
        ),
        # Action name that one could mistake for a flag value.
        (('--progress', 'list'), (('--progress',), ('list',))),
        # No arguments.
        ((), ()),
    ],
)
def test_group_arguments_with_values_returns_flags_with_corresponding_values(arguments, expected):
    flexmock(module).should_receive('argument_is_flag').with_args('--foo').and_return(True)
    flexmock(module).should_receive('argument_is_flag').with_args('--bar').and_return(True)
    flexmock(module).should_receive('argument_is_flag').with_args('--baz').and_return(True)
    flexmock(module).should_receive('argument_is_flag').with_args('--quux').and_return(True)
    flexmock(module).should_receive('argument_is_flag').with_args('--progress').and_return(True)
    flexmock(module).should_receive('argument_is_flag').with_args(33).and_return(False)
    flexmock(module).should_receive('argument_is_flag').with_args('thing').and_return(False)
    flexmock(module).should_receive('argument_is_flag').with_args('check').and_return(False)
    flexmock(module).should_receive('argument_is_flag').with_args('list').and_return(False)

    assert module.group_arguments_with_values(arguments) == expected


@pytest.mark.parametrize(
    'arguments, grouped_arguments, expected',
    [
        # An unparsable flag remaining from each parsed action.
        (
            (
                ('--latest', 'archive', 'prune', 'extract', 'list', '--flag'),
                ('--latest', 'archive', 'check', 'extract', 'list', '--flag'),
                ('prune', 'check', 'list', '--flag'),
                ('prune', 'check', 'extract', '--flag'),
            ),
            (
                (
                    ('--latest',),
                    ('archive',),
                    ('prune',),
                    ('extract',),
                    ('list',),
                    ('--flag',),
                ),
                (
                    ('--latest',),
                    ('archive',),
                    ('check',),
                    ('extract',),
                    ('list',),
                    ('--flag',),
                ),
                (('prune',), ('check',), ('list',), ('--flag',)),
                (('prune',), ('check',), ('extract',), ('--flag',)),
            ),
            ('--flag',),
        ),
        # No unparsable flags remaining.
        (
            (
                ('--archive', 'archive', 'prune', 'extract', 'list'),
                ('--archive', 'archive', 'check', 'extract', 'list'),
                ('prune', 'check', 'list'),
                ('prune', 'check', 'extract'),
            ),
            (
                (
                    (
                        '--archive',
                        'archive',
                    ),
                    ('prune',),
                    ('extract',),
                    ('list',),
                ),
                (
                    (
                        '--archive',
                        'archive',
                    ),
                    ('check',),
                    ('extract',),
                    ('list',),
                ),
                (('prune',), ('check',), ('list',)),
                (('prune',), ('check',), ('extract',)),
            ),
            (),
        ),
        # No unparsable flags remaining, but some values in common.
        (
            (
                ('--verbosity', '5', 'archive', 'prune', 'extract', 'list'),
                ('--last', '5', 'archive', 'check', 'extract', 'list'),
                ('prune', 'check', 'list', '--last', '5'),
                ('prune', 'check', '--verbosity', '5', 'extract'),
            ),
            (
                (('--verbosity', '5'), ('archive',), ('prune',), ('extract',), ('list',)),
                (
                    (
                        '--last',
                        '5',
                    ),
                    ('archive',),
                    ('check',),
                    ('extract',),
                    ('list',),
                ),
                (('prune',), ('check',), ('list',), ('--last', '5')),
                (
                    ('prune',),
                    ('check',),
                    (
                        '--verbosity',
                        '5',
                    ),
                    ('extract',),
                ),
            ),
            (),
        ),
        # No flags.
        ((), (), ()),
    ],
)
def test_get_unparsable_arguments_returns_remaining_arguments_that_no_action_can_parse(
    arguments, grouped_arguments, expected
):
    for action_arguments, grouped_action_arguments in zip(arguments, grouped_arguments):
        flexmock(module).should_receive('group_arguments_with_values').with_args(
            action_arguments
        ).and_return(grouped_action_arguments)

    assert module.get_unparsable_arguments(arguments) == expected


def test_parse_arguments_for_actions_consumes_action_arguments_after_action_name():
    action_namespace = flexmock(foo=True)
    remaining = flexmock()
    flexmock(module).should_receive('get_subaction_parsers').and_return({})
    flexmock(module).should_receive('parse_and_record_action_arguments').replace_with(
        lambda unparsed, parsed, parser, action, canonical=None: parsed.update(
            {action: action_namespace}
        )
        or remaining
    )
    flexmock(module).should_receive('get_subactions_for_actions').and_return({})
    action_parsers = {'action': flexmock(), 'other': flexmock()}
    global_namespace = flexmock(config_paths=[])
    global_parser = flexmock()
    global_parser.should_receive('parse_known_args').and_return((global_namespace, ()))

    arguments, remaining_action_arguments = module.parse_arguments_for_actions(
        ('action', '--foo', 'true'), action_parsers, global_parser
    )

    assert arguments == {'global': global_namespace, 'action': action_namespace}
    assert remaining_action_arguments == (remaining, ())


def test_parse_arguments_for_actions_consumes_action_arguments_with_alias():
    action_namespace = flexmock(foo=True)
    remaining = flexmock()
    flexmock(module).should_receive('get_subaction_parsers').and_return({})
    flexmock(module).should_receive('parse_and_record_action_arguments').replace_with(
        lambda unparsed, parsed, parser, action, canonical=None: parsed.update(
            {canonical or action: action_namespace}
        )
        or remaining
    )
    flexmock(module).should_receive('get_subactions_for_actions').and_return({})
    action_parsers = {
        'action': flexmock(),
        '-a': flexmock(),
        'other': flexmock(),
        '-o': flexmock(),
    }
    global_namespace = flexmock(config_paths=[])
    global_parser = flexmock()
    global_parser.should_receive('parse_known_args').and_return((global_namespace, ()))
    flexmock(module).ACTION_ALIASES = {'action': ['-a'], 'other': ['-o']}

    arguments, remaining_action_arguments = module.parse_arguments_for_actions(
        ('-a', '--foo', 'true'), action_parsers, global_parser
    )

    assert arguments == {'global': global_namespace, 'action': action_namespace}
    assert remaining_action_arguments == (remaining, ())


def test_parse_arguments_for_actions_consumes_multiple_action_arguments():
    action_namespace = flexmock(foo=True)
    other_namespace = flexmock(bar=3)
    flexmock(module).should_receive('get_subaction_parsers').and_return({})
    flexmock(module).should_receive('parse_and_record_action_arguments').replace_with(
        lambda unparsed, parsed, parser, action, canonical=None: parsed.update(
            {action: action_namespace if action == 'action' else other_namespace}
        )
        or ()
    ).and_return(('other', '--bar', '3')).and_return('action', '--foo', 'true')
    flexmock(module).should_receive('get_subactions_for_actions').and_return({})
    action_parsers = {
        'action': flexmock(),
        'other': flexmock(),
    }
    global_namespace = flexmock(config_paths=[])
    global_parser = flexmock()
    global_parser.should_receive('parse_known_args').and_return((global_namespace, ()))

    arguments, remaining_action_arguments = module.parse_arguments_for_actions(
        ('action', '--foo', 'true', 'other', '--bar', '3'), action_parsers, global_parser
    )

    assert arguments == {
        'global': global_namespace,
        'action': action_namespace,
        'other': other_namespace,
    }
    assert remaining_action_arguments == ((), (), ())


def test_parse_arguments_for_actions_respects_command_line_action_ordering():
    other_namespace = flexmock()
    action_namespace = flexmock(foo=True)
    flexmock(module).should_receive('get_subaction_parsers').and_return({})
    flexmock(module).should_receive('parse_and_record_action_arguments').replace_with(
        lambda unparsed, parsed, parser, action, canonical=None: parsed.update(
            {action: other_namespace if action == 'other' else action_namespace}
        )
        or ()
    ).and_return(('action',)).and_return(('other', '--foo', 'true'))
    flexmock(module).should_receive('get_subactions_for_actions').and_return({})
    action_parsers = {
        'action': flexmock(),
        'other': flexmock(),
    }
    global_namespace = flexmock(config_paths=[])
    global_parser = flexmock()
    global_parser.should_receive('parse_known_args').and_return((global_namespace, ()))

    arguments, remaining_action_arguments = module.parse_arguments_for_actions(
        ('other', '--foo', 'true', 'action'), action_parsers, global_parser
    )

    assert arguments == collections.OrderedDict(
        [('other', other_namespace), ('action', action_namespace), ('global', global_namespace)]
    )
    assert remaining_action_arguments == ((), (), ())


def test_parse_arguments_for_actions_applies_default_action_parsers():
    global_namespace = flexmock(config_paths=[])
    namespaces = {
        'global': global_namespace,
        'prune': flexmock(),
        'compact': flexmock(),
        'create': flexmock(progress=True),
        'check': flexmock(),
    }

    flexmock(module).should_receive('get_subaction_parsers').and_return({})
    flexmock(module).should_receive('parse_and_record_action_arguments').replace_with(
        lambda unparsed, parsed, parser, action, canonical=None: parsed.update(
            {action: namespaces.get(action)}
        )
        or ()
    ).and_return(())
    flexmock(module).should_receive('get_subactions_for_actions').and_return({})
    action_parsers = {
        'prune': flexmock(),
        'compact': flexmock(),
        'create': flexmock(),
        'check': flexmock(),
        'other': flexmock(),
    }
    global_parser = flexmock()
    global_parser.should_receive('parse_known_args').and_return((global_namespace, ()))

    arguments, remaining_action_arguments = module.parse_arguments_for_actions(
        ('--progress'), action_parsers, global_parser
    )

    assert arguments == namespaces
    assert remaining_action_arguments == ((), (), (), (), ())


def test_parse_arguments_for_actions_consumes_global_arguments():
    action_namespace = flexmock()
    flexmock(module).should_receive('get_subaction_parsers').and_return({})
    flexmock(module).should_receive('parse_and_record_action_arguments').replace_with(
        lambda unparsed, parsed, parser, action, canonical=None: parsed.update(
            {action: action_namespace}
        )
        or ('--verbosity', 'lots')
    )
    flexmock(module).should_receive('get_subactions_for_actions').and_return({})
    action_parsers = {
        'action': flexmock(),
        'other': flexmock(),
    }
    global_namespace = flexmock(config_paths=[])
    global_parser = flexmock()
    global_parser.should_receive('parse_known_args').and_return((global_namespace, ()))

    arguments, remaining_action_arguments = module.parse_arguments_for_actions(
        ('action', '--verbosity', 'lots'), action_parsers, global_parser
    )

    assert arguments == {'global': global_namespace, 'action': action_namespace}
    assert remaining_action_arguments == (('--verbosity', 'lots'), ())


def test_parse_arguments_for_actions_passes_through_unknown_arguments_before_action_name():
    action_namespace = flexmock()
    flexmock(module).should_receive('get_subaction_parsers').and_return({})
    flexmock(module).should_receive('parse_and_record_action_arguments').replace_with(
        lambda unparsed, parsed, parser, action, canonical=None: parsed.update(
            {action: action_namespace}
        )
        or ('--wtf', 'yes')
    )
    flexmock(module).should_receive('get_subactions_for_actions').and_return({})
    action_parsers = {
        'action': flexmock(),
        'other': flexmock(),
    }
    global_namespace = flexmock(config_paths=[])
    global_parser = flexmock()
    global_parser.should_receive('parse_known_args').and_return((global_namespace, ()))

    arguments, remaining_action_arguments = module.parse_arguments_for_actions(
        ('--wtf', 'yes', 'action'), action_parsers, global_parser
    )

    assert arguments == {'global': global_namespace, 'action': action_namespace}
    assert remaining_action_arguments == (('--wtf', 'yes'), ())


def test_parse_arguments_for_actions_passes_through_unknown_arguments_after_action_name():
    action_namespace = flexmock()
    flexmock(module).should_receive('get_subaction_parsers').and_return({})
    flexmock(module).should_receive('parse_and_record_action_arguments').replace_with(
        lambda unparsed, parsed, parser, action, canonical=None: parsed.update(
            {action: action_namespace}
        )
        or ('--wtf', 'yes')
    )
    flexmock(module).should_receive('get_subactions_for_actions').and_return({})
    action_parsers = {
        'action': flexmock(),
        'other': flexmock(),
    }
    global_namespace = flexmock(config_paths=[])
    global_parser = flexmock()
    global_parser.should_receive('parse_known_args').and_return((global_namespace, ()))

    arguments, remaining_action_arguments = module.parse_arguments_for_actions(
        ('action', '--wtf', 'yes'), action_parsers, global_parser
    )

    assert arguments == {'global': global_namespace, 'action': action_namespace}
    assert remaining_action_arguments == (('--wtf', 'yes'), ())


def test_parse_arguments_for_actions_with_borg_action_skips_other_action_parsers():
    action_namespace = flexmock(options=[])
    flexmock(module).should_receive('get_subaction_parsers').and_return({})
    flexmock(module).should_receive('parse_and_record_action_arguments').replace_with(
        lambda unparsed, parsed, parser, action, canonical=None: parsed.update(
            {action: action_namespace}
        )
        or ()
    ).and_return(())
    flexmock(module).should_receive('get_subactions_for_actions').and_return({})
    action_parsers = {
        'borg': flexmock(),
        'list': flexmock(),
    }
    global_namespace = flexmock(config_paths=[])
    global_parser = flexmock()
    global_parser.should_receive('parse_known_args').and_return((global_namespace, ()))

    arguments, remaining_action_arguments = module.parse_arguments_for_actions(
        ('borg', 'list'), action_parsers, global_parser
    )

    assert arguments == {'global': global_namespace, 'borg': action_namespace}
    assert remaining_action_arguments == ((), ())


def test_parse_arguments_for_actions_raises_error_when_no_action_is_specified():
    flexmock(module).should_receive('get_subaction_parsers').and_return({'bootstrap': [flexmock()]})
    flexmock(module).should_receive('parse_and_record_action_arguments').and_return(flexmock())
    flexmock(module).should_receive('get_subactions_for_actions').and_return(
        {'config': ['bootstrap']}
    )
    action_parsers = {'config': flexmock()}
    global_parser = flexmock()
    global_parser.should_receive('parse_known_args').and_return((flexmock(), ()))

    with pytest.raises(ValueError):
        module.parse_arguments_for_actions(('config',), action_parsers, global_parser)


def test_make_argument_description_with_object_adds_example():
    buffer = flexmock()
    buffer.should_receive('getvalue').and_return('{foo: example}')
    flexmock(module.io).should_receive('StringIO').and_return(buffer)
    yaml = flexmock()
    yaml.should_receive('dump')
    flexmock(module.ruamel.yaml).should_receive('YAML').and_return(yaml)

    assert (
        module.make_argument_description(
            schema={
                'description': 'Thing.',
                'type': 'object',
                'example': {'foo': 'example'},
            },
            flag_name='flag',
        )
        == 'Thing. Example value: "{foo: example}"'
    )


def test_make_argument_description_without_description_and_with_object_sets_example():
    buffer = flexmock()
    buffer.should_receive('getvalue').and_return('{foo: example}')
    flexmock(module.io).should_receive('StringIO').and_return(buffer)
    yaml = flexmock()
    yaml.should_receive('dump')
    flexmock(module.ruamel.yaml).should_receive('YAML').and_return(yaml)

    assert (
        module.make_argument_description(
            schema={
                'type': 'object',
                'example': {'foo': 'example'},
            },
            flag_name='flag',
        )
        == 'Example value: "{foo: example}"'
    )


def test_make_argument_description_with_object_skips_missing_example():
    flexmock(module.ruamel.yaml).should_receive('YAML').never()

    assert (
        module.make_argument_description(
            schema={
                'description': 'Thing.',
                'type': 'object',
            },
            flag_name='flag',
        )
        == 'Thing.'
    )


def test_make_argument_description_with_array_adds_example():
    buffer = flexmock()
    buffer.should_receive('getvalue').and_return('[example]')
    flexmock(module.io).should_receive('StringIO').and_return(buffer)
    yaml = flexmock()
    yaml.should_receive('dump')
    flexmock(module.ruamel.yaml).should_receive('YAML').and_return(yaml)

    assert (
        module.make_argument_description(
            schema={
                'description': 'Thing.',
                'type': 'array',
                'example': ['example'],
            },
            flag_name='flag',
        )
        == 'Thing. Example value: "[example]"'
    )


def test_make_argument_description_without_description_and_with_array_sets_example():
    buffer = flexmock()
    buffer.should_receive('getvalue').and_return('[example]')
    flexmock(module.io).should_receive('StringIO').and_return(buffer)
    yaml = flexmock()
    yaml.should_receive('dump')
    flexmock(module.ruamel.yaml).should_receive('YAML').and_return(yaml)

    assert (
        module.make_argument_description(
            schema={
                'type': 'array',
                'example': ['example'],
            },
            flag_name='flag',
        )
        == 'Example value: "[example]"'
    )


def test_make_argument_description_with_array_skips_missing_example():
    flexmock(module.ruamel.yaml).should_receive('YAML').never()

    assert (
        module.make_argument_description(
            schema={
                'description': 'Thing.',
                'type': 'array',
            },
            flag_name='flag',
        )
        == 'Thing.'
    )


def test_make_argument_description_with_array_index_in_flag_name_adds_to_description():
    assert 'list element' in module.make_argument_description(
        schema={
            'description': 'Thing.',
            'type': 'something',
        },
        flag_name='flag[0]',
    )


def test_make_argument_description_without_description_and_with_array_index_in_flag_name_sets_description():
    assert 'list element' in module.make_argument_description(
        schema={
            'type': 'something',
        },
        flag_name='flag[0]',
    )


def test_make_argument_description_escapes_percent_character():
    assert (
        module.make_argument_description(
            schema={
                'description': '% Thing.',
                'type': 'something',
            },
            flag_name='flag',
        )
        == '%% Thing.'
    )


def test_add_array_element_arguments_without_array_index_bails():
    arguments_group = flexmock()
    arguments_group.should_receive('add_argument').never()

    module.add_array_element_arguments(
        arguments_group=arguments_group,
        unparsed_arguments=(),
        flag_name='foo',
    )


def test_add_array_element_arguments_with_help_flag_bails():
    arguments_group = flexmock()
    arguments_group.should_receive('add_argument').never()

    module.add_array_element_arguments(
        arguments_group=arguments_group,
        unparsed_arguments=('--foo', '--help', '--bar'),
        flag_name='foo[0]',
    )


def test_add_array_element_arguments_without_any_flags_bails():
    arguments_group = flexmock()
    arguments_group.should_receive('add_argument').never()

    module.add_array_element_arguments(
        arguments_group=arguments_group,
        unparsed_arguments=(),
        flag_name='foo[0]',
    )


# Use this instead of a flexmock because it's not easy to check the type() of a flexmock instance.
Group_action = collections.namedtuple(
    'Group_action',
    (
        'option_strings',
        'choices',
        'default',
        'nargs',
        'required',
        'type',
    ),
    defaults=(
        flexmock(),
        flexmock(),
        flexmock(),
        flexmock(),
        flexmock(),
    ),
)


def test_add_array_element_arguments_without_array_index_flags_bails():
    arguments_group = flexmock(
        _group_actions=(
            Group_action(
                option_strings=('--foo[0].val',),
            ),
        ),
        _registries={'action': {'store_stuff': Group_action}},
    )
    arguments_group.should_receive('add_argument').never()

    module.add_array_element_arguments(
        arguments_group=arguments_group,
        unparsed_arguments=('--foo', '--bar'),
        flag_name='foo[0].val',
    )


def test_add_array_element_arguments_with_non_matching_array_index_flags_bails():
    arguments_group = flexmock(
        _group_actions=(
            Group_action(
                option_strings=('--foo[0].val',),
            ),
        ),
        _registries={'action': {'store_stuff': Group_action}},
    )
    arguments_group.should_receive('add_argument').never()

    module.add_array_element_arguments(
        arguments_group=arguments_group,
        unparsed_arguments=('--foo', '--bar[25].val', 'barval'),
        flag_name='foo[0].val',
    )


def test_add_array_element_arguments_with_identical_array_index_flag_bails():
    arguments_group = flexmock(
        _group_actions=(
            Group_action(
                option_strings=('--foo[0].val',),
            ),
        ),
        _registries={'action': {'store_stuff': Group_action}},
    )
    arguments_group.should_receive('add_argument').never()

    module.add_array_element_arguments(
        arguments_group=arguments_group,
        unparsed_arguments=('--foo[0].val', 'fooval', '--bar'),
        flag_name='foo[0].val',
    )


def test_add_array_element_arguments_without_action_type_in_registry_bails():
    arguments_group = flexmock(
        _group_actions=(
            Group_action(
                option_strings=('--foo[0].val',),
                choices=flexmock(),
                default=flexmock(),
                nargs=flexmock(),
                required=flexmock(),
                type=flexmock(),
            ),
        ),
        _registries={'action': {'store_stuff': bool}},
    )
    arguments_group.should_receive('add_argument').never()

    module.add_array_element_arguments(
        arguments_group=arguments_group,
        unparsed_arguments=('--foo[25].val', 'fooval', '--bar[1].val', 'barval'),
        flag_name='foo[0].val',
    )


def test_add_array_element_arguments_adds_arguments_for_array_index_flags():
    arguments_group = flexmock(
        _group_actions=(
            Group_action(
                option_strings=('--foo[0].val',),
                choices=flexmock(),
                default=flexmock(),
                nargs=flexmock(),
                required=flexmock(),
                type=flexmock(),
            ),
        ),
        _registries={'action': {'store_stuff': Group_action}},
    )
    arguments_group.should_receive('add_argument').with_args(
        '--foo[25].val',
        action='store_stuff',
        choices=object,
        default=object,
        dest='foo[25].val',
        nargs=object,
        required=object,
        type=object,
    ).once()

    module.add_array_element_arguments(
        arguments_group=arguments_group,
        unparsed_arguments=('--foo[25].val', 'fooval', '--bar[1].val', 'barval'),
        flag_name='foo[0].val',
    )


def test_add_array_element_arguments_adds_arguments_for_array_index_flags_with_equals_sign():
    arguments_group = flexmock(
        _group_actions=(
            Group_action(
                option_strings=('--foo[0].val',),
                choices=flexmock(),
                default=flexmock(),
                nargs=flexmock(),
                required=flexmock(),
                type=flexmock(),
            ),
        ),
        _registries={'action': {'store_stuff': Group_action}},
    )
    arguments_group.should_receive('add_argument').with_args(
        '--foo[25].val',
        action='store_stuff',
        choices=object,
        default=object,
        dest='foo[25].val',
        nargs=object,
        required=object,
        type=object,
    ).once()

    module.add_array_element_arguments(
        arguments_group=arguments_group,
        unparsed_arguments=('--foo[25].val=fooval', '--bar[1].val=barval'),
        flag_name='foo[0].val',
    )


def test_add_array_element_arguments_adds_arguments_for_array_index_flags_with_dashes():
    arguments_group = flexmock(
        _group_actions=(
            Group_action(
                option_strings=('--foo[0].val-and-stuff',),
                choices=flexmock(),
                default=flexmock(),
                nargs=flexmock(),
                required=flexmock(),
                type=flexmock(),
            ),
        ),
        _registries={'action': {'store_stuff': Group_action}},
    )
    arguments_group.should_receive('add_argument').with_args(
        '--foo[25].val-and-stuff',
        action='store_stuff',
        choices=object,
        default=object,
        dest='foo[25].val_and_stuff',
        nargs=object,
        required=object,
        type=object,
    ).once()

    module.add_array_element_arguments(
        arguments_group=arguments_group,
        unparsed_arguments=('--foo[25].val-and-stuff', 'fooval', '--bar[1].val', 'barval'),
        flag_name='foo[0].val-and-stuff',
    )


def test_add_arguments_from_schema_with_non_dict_schema_bails():
    arguments_group = flexmock()
    flexmock(module).should_receive('make_argument_description').never()
    flexmock(module.borgmatic.config.schema).should_receive('parse_type').never()
    arguments_group.should_receive('add_argument').never()

    module.add_arguments_from_schema(
        arguments_group=arguments_group, schema='foo', unparsed_arguments=()
    )


def test_add_arguments_from_schema_with_nested_object_adds_flag_for_each_option():
    arguments_group = flexmock()
    flexmock(module).should_receive('make_argument_description').and_return('help 1').and_return(
        'help 2'
    )
    flexmock(module.borgmatic.config.schema).should_receive('parse_type').and_return(
        int
    ).and_return(str)
    arguments_group.should_receive('add_argument').with_args(
        '--foo.bar',
        type=int,
        metavar='BAR',
        help='help 1',
    ).once()
    arguments_group.should_receive('add_argument').with_args(
        '--foo.baz',
        type=str,
        metavar='BAZ',
        help='help 2',
    ).once()
    flexmock(module).should_receive('add_array_element_arguments')

    module.add_arguments_from_schema(
        arguments_group=arguments_group,
        schema={
            'type': 'object',
            'properties': {
                'foo': {
                    'type': 'object',
                    'properties': {
                        'bar': {'type': 'integer'},
                        'baz': {'type': 'str'},
                    },
                }
            },
        },
        unparsed_arguments=(),
    )


def test_add_arguments_from_schema_uses_first_non_null_type_from_multi_type_object():
    arguments_group = flexmock()
    flexmock(module).should_receive('make_argument_description').and_return('help 1')
    flexmock(module.borgmatic.config.schema).should_receive('parse_type').and_return(int)
    arguments_group.should_receive('add_argument').with_args(
        '--foo.bar',
        type=int,
        metavar='BAR',
        help='help 1',
    ).once()
    flexmock(module).should_receive('add_array_element_arguments')

    module.add_arguments_from_schema(
        arguments_group=arguments_group,
        schema={
            'type': 'object',
            'properties': {
                'foo': {
                    'type': ['null', 'object', 'boolean'],
                    'properties': {
                        'bar': {'type': 'integer'},
                    },
                }
            },
        },
        unparsed_arguments=(),
    )


def test_add_arguments_from_schema_with_empty_multi_type_raises():
    arguments_group = flexmock()
    flexmock(module).should_receive('make_argument_description').and_return('help 1')
    flexmock(module.borgmatic.config.schema).should_receive('parse_type').and_return(int)
    arguments_group.should_receive('add_argument').never()
    flexmock(module).should_receive('add_array_element_arguments').never()

    with pytest.raises(ValueError):
        module.add_arguments_from_schema(
            arguments_group=arguments_group,
            schema={
                'type': 'object',
                'properties': {
                    'foo': {
                        'type': [],
                        'properties': {
                            'bar': {'type': 'integer'},
                        },
                    }
                },
            },
            unparsed_arguments=(),
        )


def test_add_arguments_from_schema_with_propertyless_option_adds_flag():
    arguments_group = flexmock()
    flexmock(module).should_receive('make_argument_description').and_return('help')
    flexmock(module.borgmatic.config.schema).should_receive('parse_type').and_return(str)
    arguments_group.should_receive('add_argument').with_args(
        '--foo',
        type=str,
        metavar='FOO',
        help='help',
    ).once()
    flexmock(module).should_receive('add_array_element_arguments')

    module.add_arguments_from_schema(
        arguments_group=arguments_group,
        schema={
            'type': 'object',
            'properties': {
                'foo': {
                    'type': 'object',
                }
            },
        },
        unparsed_arguments=(),
    )


def test_add_arguments_from_schema_with_array_of_scalars_adds_multiple_flags():
    arguments_group = flexmock()
    flexmock(module).should_receive('make_argument_description').and_return('help')
    flexmock(module.borgmatic.config.schema).should_receive('parse_type').with_args(
        'integer', object=str, array=str
    ).and_return(int)
    flexmock(module.borgmatic.config.schema).should_receive('parse_type').with_args(
        'array', object=str, array=str
    ).and_return(str)
    arguments_group.should_receive('add_argument').with_args(
        '--foo[0]',
        type=int,
        metavar='FOO[0]',
        help='help',
    ).once()
    arguments_group.should_receive('add_argument').with_args(
        '--foo',
        type=str,
        metavar='FOO',
        help='help',
    ).once()
    flexmock(module).should_receive('add_array_element_arguments')

    module.add_arguments_from_schema(
        arguments_group=arguments_group,
        schema={
            'type': 'object',
            'properties': {
                'foo': {
                    'type': 'array',
                    'items': {
                        'type': 'integer',
                    },
                }
            },
        },
        unparsed_arguments=(),
    )


def test_add_arguments_from_schema_with_array_of_objects_adds_multiple_flags():
    arguments_group = flexmock()
    flexmock(module).should_receive('make_argument_description').and_return('help 1').and_return(
        'help 2'
    )
    flexmock(module.borgmatic.config.schema).should_receive('parse_type').and_return(
        int
    ).and_return(str)
    arguments_group.should_receive('add_argument').with_args(
        '--foo[0].bar',
        type=int,
        metavar='BAR',
        help='help 1',
    ).once()
    arguments_group.should_receive('add_argument').with_args(
        '--foo',
        type=str,
        metavar='FOO',
        help='help 2',
    ).once()
    flexmock(module).should_receive('add_array_element_arguments')
    flexmock(module).should_receive('add_array_element_arguments').with_args(
        arguments_group=arguments_group,
        unparsed_arguments=(),
        flag_name='foo[0].bar',
    ).once()

    module.add_arguments_from_schema(
        arguments_group=arguments_group,
        schema={
            'type': 'object',
            'properties': {
                'foo': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'bar': {
                                'type': 'integer',
                            }
                        },
                    },
                }
            },
        },
        unparsed_arguments=(),
    )


def test_add_arguments_from_schema_with_boolean_adds_two_valueless_flags():
    arguments_group = flexmock()
    flexmock(module).should_receive('make_argument_description').and_return('help')
    flexmock(module.borgmatic.config.schema).should_receive('parse_type').and_return(bool)
    arguments_group.should_receive('add_argument').with_args(
        '--foo',
        action='store_true',
        default=None,
        help='help',
    ).once()
    arguments_group.should_receive('add_argument').with_args(
        '--no-foo',
        dest='foo',
        action='store_false',
        default=None,
        help=object,
    ).once()
    flexmock(module).should_receive('add_array_element_arguments')

    module.add_arguments_from_schema(
        arguments_group=arguments_group,
        schema={
            'type': 'object',
            'properties': {
                'foo': {
                    'type': 'boolean',
                }
            },
        },
        unparsed_arguments=(),
    )


def test_add_arguments_from_schema_with_nested_boolean_adds_two_valueless_flags():
    arguments_group = flexmock()
    flexmock(module).should_receive('make_argument_description').and_return('help')
    flexmock(module.borgmatic.config.schema).should_receive('parse_type').and_return(bool)
    arguments_group.should_receive('add_argument').with_args(
        '--foo.bar.baz-quux',
        action='store_true',
        default=None,
        help='help',
    ).once()
    arguments_group.should_receive('add_argument').with_args(
        '--foo.bar.no-baz-quux',
        dest='foo.bar.baz_quux',
        action='store_false',
        default=None,
        help=object,
    ).once()
    flexmock(module).should_receive('add_array_element_arguments')

    module.add_arguments_from_schema(
        arguments_group=arguments_group,
        schema={
            'type': 'object',
            'properties': {
                'baz_quux': {
                    'type': 'boolean',
                }
            },
        },
        unparsed_arguments=(),
        names=('foo', 'bar'),
    )


def test_add_arguments_from_schema_with_boolean_with_name_prefixed_with_no_adds_two_valueless_flags_and_removes_the_no_for_one():
    arguments_group = flexmock()
    flexmock(module).should_receive('make_argument_description').and_return('help')
    flexmock(module.borgmatic.config.schema).should_receive('parse_type').and_return(bool)
    arguments_group.should_receive('add_argument').with_args(
        '--no-foo',
        action='store_true',
        default=None,
        help='help',
    ).once()
    arguments_group.should_receive('add_argument').with_args(
        '--foo',
        dest='no_foo',
        action='store_false',
        default=None,
        help=object,
    ).once()
    flexmock(module).should_receive('add_array_element_arguments')

    module.add_arguments_from_schema(
        arguments_group=arguments_group,
        schema={
            'type': 'object',
            'properties': {
                'no_foo': {
                    'type': 'boolean',
                }
            },
        },
        unparsed_arguments=(),
    )


def test_add_arguments_from_schema_skips_omitted_flag_name():
    arguments_group = flexmock()
    flexmock(module).should_receive('make_argument_description').and_return('help')
    flexmock(module.borgmatic.config.schema).should_receive('parse_type').and_return(str)
    arguments_group.should_receive('add_argument').with_args(
        '--match-archives',
        type=object,
        metavar=object,
        help=object,
    ).never()
    arguments_group.should_receive('add_argument').with_args(
        '--foo',
        type=str,
        metavar='FOO',
        help='help',
    ).once()
    flexmock(module).should_receive('add_array_element_arguments')

    module.add_arguments_from_schema(
        arguments_group=arguments_group,
        schema={
            'type': 'object',
            'properties': {
                'match_archives': {
                    'type': 'string',
                },
                'foo': {
                    'type': 'string',
                },
            },
        },
        unparsed_arguments=(),
    )


def test_add_arguments_from_schema_rewrites_option_name_to_flag_name():
    arguments_group = flexmock()
    flexmock(module).should_receive('make_argument_description').and_return('help')
    flexmock(module.borgmatic.config.schema).should_receive('parse_type').and_return(str)
    arguments_group.should_receive('add_argument').with_args(
        '--foo-and-stuff',
        type=str,
        metavar='FOO_AND_STUFF',
        help='help',
    ).once()
    flexmock(module).should_receive('add_array_element_arguments')

    module.add_arguments_from_schema(
        arguments_group=arguments_group,
        schema={
            'type': 'object',
            'properties': {
                'foo_and_stuff': {
                    'type': 'string',
                },
            },
        },
        unparsed_arguments=(),
    )
