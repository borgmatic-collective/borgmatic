import pytest
from flexmock import flexmock

from borgmatic.commands import arguments as module


def test_make_argument_description_with_object_adds_example():
    assert (
        module.make_argument_description(
            schema={
                'description': 'Thing.',
                'type': 'object',
                'example': {'bar': 'baz'},
            },
            flag_name='flag',
        )
        # Apparently different versions of ruamel.yaml serialize this
        # differently.
        in ('Thing. Example value: "bar: baz"' 'Thing. Example value: "{bar: baz}"')
    )


def test_make_argument_description_with_array_adds_example():
    assert (
        module.make_argument_description(
            schema={
                'description': 'Thing.',
                'type': 'array',
                'example': [1, '- foo', {'bar': 'baz'}],
            },
            flag_name='flag',
        )
        # Apparently different versions of ruamel.yaml serialize this
        # differently.
        in (
            'Thing. Example value: "[1, \'- foo\', bar: baz]"'
            'Thing. Example value: "[1, \'- foo\', {bar: baz}]"'
        )
    )


def test_add_array_element_arguments_adds_arguments_for_array_index_flags():
    parser = module.ArgumentParser(allow_abbrev=False, add_help=False)
    arguments_group = parser.add_argument_group('arguments')
    arguments_group.add_argument(
        '--foo[0].val',
        action='store_true',
        dest='--foo[0].val',
    )

    flexmock(arguments_group).should_receive('add_argument').with_args(
        '--foo[25].val',
        action='store_true',
        default=False,
        dest='foo[25].val',
        required=object,
    ).once()

    module.add_array_element_arguments(
        arguments_group=arguments_group,
        unparsed_arguments=('--foo[25].val', 'fooval', '--bar[1].val', 'barval'),
        flag_name='foo[0].val',
    )


def test_add_arguments_from_schema_with_nested_object_adds_flag_for_each_option():
    parser = module.ArgumentParser(allow_abbrev=False, add_help=False)
    arguments_group = parser.add_argument_group('arguments')
    flexmock(arguments_group).should_receive('add_argument').with_args(
        '--foo.bar',
        type=int,
        metavar='BAR',
        help='help 1',
    ).once()
    flexmock(arguments_group).should_receive('add_argument').with_args(
        '--foo.baz',
        type=str,
        metavar='BAZ',
        help='help 2',
    ).once()

    module.add_arguments_from_schema(
        arguments_group=arguments_group,
        schema={
            'type': 'object',
            'properties': {
                'foo': {
                    'type': 'object',
                    'properties': {
                        'bar': {'type': 'integer', 'description': 'help 1'},
                        'baz': {'type': 'string', 'description': 'help 2'},
                    },
                }
            },
        },
        unparsed_arguments=(),
    )


def test_add_arguments_from_schema_with_array_and_nested_object_adds_multiple_flags():
    parser = module.ArgumentParser(allow_abbrev=False, add_help=False)
    arguments_group = parser.add_argument_group('arguments')
    flexmock(arguments_group).should_receive('add_argument').with_args(
        '--foo[0].bar',
        type=int,
        metavar='BAR',
        help=object,
    ).once()
    flexmock(arguments_group).should_receive('add_argument').with_args(
        '--foo',
        type=str,
        metavar='FOO',
        help='help 2',
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
                                'description': 'help 1',
                            }
                        },
                    },
                    'description': 'help 2',
                }
            },
        },
        unparsed_arguments=(),
    )


def test_parse_arguments_with_no_arguments_uses_defaults():
    config_paths = ['default']
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(config_paths)

    arguments = module.parse_arguments({})

    global_arguments = arguments['global']
    assert global_arguments.config_paths == config_paths


def test_parse_arguments_with_multiple_config_flags_parses_as_list():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    arguments = module.parse_arguments({}, '--config', 'myconfig', '--config', 'otherconfig')

    global_arguments = arguments['global']
    assert global_arguments.config_paths == ['myconfig', 'otherconfig']


def test_parse_arguments_with_action_after_config_path_omits_action():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    arguments = module.parse_arguments({}, '--config', 'myconfig', 'list', '--json')

    global_arguments = arguments['global']
    assert global_arguments.config_paths == ['myconfig']
    assert 'list' in arguments
    assert arguments['list'].json


def test_parse_arguments_with_action_after_config_path_omits_aliased_action():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    arguments = module.parse_arguments(
        {}, '--config', 'myconfig', 'init', '--encryption', 'repokey'
    )

    global_arguments = arguments['global']
    assert global_arguments.config_paths == ['myconfig']
    assert 'repo-create' in arguments
    assert arguments['repo-create'].encryption_mode == 'repokey'


def test_parse_arguments_with_action_and_positional_arguments_after_config_path_omits_action_and_arguments():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    arguments = module.parse_arguments({}, '--config', 'myconfig', 'borg', 'key', 'export')

    global_arguments = arguments['global']
    assert global_arguments.config_paths == ['myconfig']
    assert 'borg' in arguments
    assert arguments['borg'].options == ['key', 'export']


def test_parse_arguments_with_single_override_parses():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    arguments = module.parse_arguments({}, '--override', 'foo.bar=baz')

    global_arguments = arguments['global']
    assert global_arguments.overrides == ['foo.bar=baz']


def test_parse_arguments_with_multiple_overrides_flags_parses():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    arguments = module.parse_arguments(
        {}, '--override', 'foo.bar=baz', '--override', 'foo.quux=7', '--override', 'this.that=8'
    )

    global_arguments = arguments['global']
    assert global_arguments.overrides == ['foo.bar=baz', 'foo.quux=7', 'this.that=8']


def test_parse_arguments_with_list_json_overrides_default():
    arguments = module.parse_arguments({}, 'list', '--json')

    assert 'list' in arguments
    assert arguments['list'].json is True


def test_parse_arguments_with_no_actions_defaults_to_all_actions_enabled():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    arguments = module.parse_arguments({})

    assert 'prune' in arguments
    assert 'create' in arguments
    assert 'check' in arguments


def test_parse_arguments_with_no_actions_passes_argument_to_relevant_actions():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    arguments = module.parse_arguments({}, '--stats', '--list')

    assert 'prune' in arguments
    assert arguments['prune'].statistics
    assert arguments['prune'].list_details
    assert 'create' in arguments
    assert arguments['create'].statistics
    assert arguments['create'].list_details
    assert 'check' in arguments


def test_parse_arguments_with_help_and_no_actions_shows_global_help(capsys):
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit) as exit:
        module.parse_arguments({}, '--help')

    assert exit.value.code == 0
    captured = capsys.readouterr()
    assert 'global arguments:' in captured.out
    assert 'actions:' in captured.out


def test_parse_arguments_with_help_and_action_shows_action_help(capsys):
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit) as exit:
        module.parse_arguments({}, 'create', '--help')

    assert exit.value.code == 0
    captured = capsys.readouterr()
    assert 'global arguments:' not in captured.out
    assert 'actions:' not in captured.out
    assert 'create arguments:' in captured.out


def test_parse_arguments_with_action_before_global_options_parses_options():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    arguments = module.parse_arguments({}, 'prune', '--dry-run')

    assert 'prune' in arguments
    assert arguments['global'].dry_run


def test_parse_arguments_with_global_options_before_action_parses_options():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    arguments = module.parse_arguments({}, '--dry-run', 'prune')

    assert 'prune' in arguments
    assert arguments['global'].dry_run


def test_parse_arguments_with_prune_action_leaves_other_actions_disabled():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    arguments = module.parse_arguments({}, 'prune')

    assert 'prune' in arguments
    assert 'create' not in arguments
    assert 'check' not in arguments


def test_parse_arguments_with_multiple_actions_leaves_other_action_disabled():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    arguments = module.parse_arguments({}, 'create', 'check')

    assert 'prune' not in arguments
    assert 'create' in arguments
    assert 'check' in arguments


def test_parse_arguments_disallows_invalid_argument():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments({}, '--posix-me-harder')


def test_parse_arguments_disallows_encryption_mode_without_init():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments({}, '--config', 'myconfig', '--encryption', 'repokey')


def test_parse_arguments_allows_encryption_mode_with_init():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, '--config', 'myconfig', 'init', '--encryption', 'repokey')


def test_parse_arguments_disallows_append_only_without_init():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments({}, '--config', 'myconfig', '--append-only')


def test_parse_arguments_disallows_storage_quota_without_init():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments({}, '--config', 'myconfig', '--storage-quota', '5G')


def test_parse_arguments_allows_init_and_prune():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, '--config', 'myconfig', 'init', '--encryption', 'repokey', 'prune')


def test_parse_arguments_allows_init_and_create():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, '--config', 'myconfig', 'init', '--encryption', 'repokey', 'create')


def test_parse_arguments_allows_repository_with_extract():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments(
        {}, '--config', 'myconfig', 'extract', '--repository', 'test.borg', '--archive', 'test'
    )


def test_parse_arguments_allows_repository_with_mount():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments(
        {},
        '--config',
        'myconfig',
        'mount',
        '--repository',
        'test.borg',
        '--archive',
        'test',
        '--mount-point',
        '/mnt',
    )


def test_parse_arguments_allows_repository_with_list():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, '--config', 'myconfig', 'list', '--repository', 'test.borg')


def test_parse_arguments_disallows_archive_unless_action_consumes_it():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments({}, '--config', 'myconfig', '--archive', 'test')


def test_parse_arguments_disallows_paths_unless_action_consumes_it():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments({}, '--config', 'myconfig', '--path', 'test')


def test_parse_arguments_disallows_other_actions_with_config_bootstrap():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments({}, 'config', 'bootstrap', '--repository', 'test.borg', 'list')


def test_parse_arguments_allows_archive_with_extract():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, '--config', 'myconfig', 'extract', '--archive', 'test')


def test_parse_arguments_allows_archive_with_mount():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments(
        {}, '--config', 'myconfig', 'mount', '--archive', 'test', '--mount-point', '/mnt'
    )


def test_parse_arguments_allows_archive_with_restore():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, '--config', 'myconfig', 'restore', '--archive', 'test')


def test_parse_arguments_allows_archive_with_list():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, '--config', 'myconfig', 'list', '--archive', 'test')


def test_parse_arguments_requires_archive_with_extract():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit):
        module.parse_arguments({}, '--config', 'myconfig', 'extract')


def test_parse_arguments_requires_archive_with_restore():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit):
        module.parse_arguments({}, '--config', 'myconfig', 'restore')


def test_parse_arguments_requires_mount_point_with_mount():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit):
        module.parse_arguments({}, '--config', 'myconfig', 'mount', '--archive', 'test')


def test_parse_arguments_requires_mount_point_with_umount():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit):
        module.parse_arguments({}, '--config', 'myconfig', 'umount')


def test_parse_arguments_allows_progress_before_create():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, '--progress', 'create', 'list')


def test_parse_arguments_allows_progress_after_create():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, 'create', '--progress', 'list')


def test_parse_arguments_allows_progress_and_extract():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, '--progress', 'extract', '--archive', 'test', 'list')


def test_parse_arguments_disallows_progress_without_create():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments({}, '--progress', 'list')


def test_parse_arguments_with_stats_and_create_flags_does_not_raise():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, '--stats', 'create', 'list')


def test_parse_arguments_with_stats_and_prune_flags_does_not_raise():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, '--stats', 'prune', 'list')


def test_parse_arguments_with_stats_flag_but_no_create_or_prune_flag_raises_value_error():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments({}, '--stats', 'list')


def test_parse_arguments_with_list_and_create_flags_does_not_raise():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, '--list', 'create')


def test_parse_arguments_with_list_and_prune_flags_does_not_raise():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, '--list', 'prune')


def test_parse_arguments_with_list_flag_but_no_relevant_action_raises_value_error():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments({}, '--list', 'repo-create')


def test_parse_arguments_allows_json_with_list_or_info():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, 'list', '--json')
    module.parse_arguments({}, 'info', '--json')


def test_parse_arguments_disallows_json_with_both_list_and_info():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments({}, 'list', 'info', '--json')


def test_parse_arguments_disallows_json_with_both_list_and_repo_info():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments({}, 'list', 'repo-info', '--json')


def test_parse_arguments_disallows_json_with_both_repo_info_and_info():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments({}, 'repo-info', 'info', '--json')


def test_parse_arguments_disallows_list_with_both_prefix_and_match_archives():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments({}, 'list', '--prefix', 'foo', '--match-archives', 'sh:*bar')


def test_parse_arguments_disallows_repo_list_with_both_prefix_and_match_archives():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments({}, 'repo-list', '--prefix', 'foo', '--match-archives', 'sh:*bar')


def test_parse_arguments_disallows_info_with_both_archive_and_match_archives():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments({}, 'info', '--archive', 'foo', '--match-archives', 'sh:*bar')


def test_parse_arguments_disallows_info_with_both_archive_and_prefix():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments({}, 'info', '--archive', 'foo', '--prefix', 'bar')


def test_parse_arguments_disallows_info_with_both_prefix_and_match_archives():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments({}, 'info', '--prefix', 'foo', '--match-archives', 'sh:*bar')


def test_parse_arguments_check_only_extract_does_not_raise_extract_subparser_error():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, 'check', '--only', 'extract')


def test_parse_arguments_extract_archive_check_does_not_raise_check_subparser_error():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, 'extract', '--archive', 'check')


def test_parse_arguments_extract_with_check_only_extract_does_not_raise():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, 'extract', '--archive', 'name', 'check', '--only', 'extract')


def test_parse_arguments_bootstrap_without_config_errors():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments({}, 'bootstrap')


def test_parse_arguments_config_with_no_subaction_errors():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments({}, 'config')


def test_parse_arguments_config_with_help_shows_config_help(capsys):
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit) as exit:
        module.parse_arguments({}, 'config', '--help')

    assert exit.value.code == 0
    captured = capsys.readouterr()
    assert 'global arguments:' not in captured.out
    assert 'config arguments:' in captured.out
    assert 'config sub-actions:' in captured.out


def test_parse_arguments_config_with_subaction_but_missing_flags_errors():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit) as exit:
        module.parse_arguments({}, 'config', 'bootstrap')

    assert exit.value.code == 2


def test_parse_arguments_config_with_subaction_and_help_shows_subaction_help(capsys):
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit) as exit:
        module.parse_arguments({}, 'config', 'bootstrap', '--help')

    assert exit.value.code == 0
    captured = capsys.readouterr()
    assert 'config bootstrap arguments:' in captured.out


def test_parse_arguments_config_with_subaction_and_required_flags_does_not_raise():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, 'config', 'bootstrap', '--repository', 'repo.borg')


def test_parse_arguments_config_with_subaction_and_global_flags_at_start_does_not_raise():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, '--dry-run', 'config', 'bootstrap', '--repository', 'repo.borg')


def test_parse_arguments_config_with_subaction_and_global_flags_at_end_does_not_raise():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, 'config', 'bootstrap', '--repository', 'repo.borg', '--dry-run')


def test_parse_arguments_config_with_subaction_and_explicit_config_file_does_not_raise():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments(
        {}, 'config', 'bootstrap', '--repository', 'repo.borg', '--config', 'test.yaml'
    )


def test_parse_arguments_with_borg_action_and_dry_run_raises():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments({}, '--dry-run', 'borg', 'list')


def test_parse_arguments_with_borg_action_and_no_dry_run_does_not_raise():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments({}, 'borg', 'list')


def test_parse_arguments_with_argument_from_schema_does_not_raise():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments(
        {
            'type': 'object',
            'properties': {'foo': {'type': 'object', 'properties': {'bar': {'type': 'integer'}}}},
        },
        '--foo.bar',
        '3',
    )
