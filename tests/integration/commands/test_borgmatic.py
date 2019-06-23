import subprocess

import pytest
from flexmock import flexmock

from borgmatic.commands import borgmatic as module


def test_parse_arguments_with_no_arguments_uses_defaults():
    config_paths = ['default']
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(config_paths)

    arguments = module.parse_arguments()

    global_arguments = arguments['global']
    assert global_arguments.config_paths == config_paths
    assert global_arguments.excludes_filename is None
    assert global_arguments.verbosity == 0
    assert global_arguments.syslog_verbosity == 0


def test_parse_arguments_with_multiple_config_paths_parses_as_list():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    arguments = module.parse_arguments('--config', 'myconfig', 'otherconfig')

    global_arguments = arguments['global']
    assert global_arguments.config_paths == ['myconfig', 'otherconfig']
    assert global_arguments.verbosity == 0
    assert global_arguments.syslog_verbosity == 0


def test_parse_arguments_with_verbosity_overrides_default():
    config_paths = ['default']
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(config_paths)

    arguments = module.parse_arguments('--verbosity', '1')

    global_arguments = arguments['global']
    assert global_arguments.config_paths == config_paths
    assert global_arguments.excludes_filename is None
    assert global_arguments.verbosity == 1
    assert global_arguments.syslog_verbosity == 0


def test_parse_arguments_with_syslog_verbosity_overrides_default():
    config_paths = ['default']
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(config_paths)

    arguments = module.parse_arguments('--syslog-verbosity', '2')

    global_arguments = arguments['global']
    assert global_arguments.config_paths == config_paths
    assert global_arguments.excludes_filename is None
    assert global_arguments.verbosity == 0
    assert global_arguments.syslog_verbosity == 2


def test_parse_arguments_with_list_json_overrides_default():
    arguments = module.parse_arguments('list', '--json')

    assert 'list' in arguments
    assert arguments['list'].json is True


def test_parse_arguments_with_dashed_list_json_overrides_default():
    arguments = module.parse_arguments('--list', '--json')

    assert 'list' in arguments
    assert arguments['list'].json is True


def test_parse_arguments_with_no_actions_defaults_to_all_actions_enabled():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    arguments = module.parse_arguments()

    assert 'prune' in arguments
    assert 'create' in arguments
    assert 'check' in arguments


def test_parse_arguments_with_help_and_no_actions_shows_global_help(capsys):
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit) as exit:
        module.parse_arguments('--help')

    assert exit.value.code == 0
    captured = capsys.readouterr()
    assert 'global arguments:' in captured.out
    assert 'actions:' in captured.out


def test_parse_arguments_with_help_and_action_shows_action_help(capsys):
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit) as exit:
        module.parse_arguments('create', '--help')

    assert exit.value.code == 0
    captured = capsys.readouterr()
    assert 'global arguments:' not in captured.out
    assert 'actions:' not in captured.out
    assert 'create arguments:' in captured.out


def test_parse_arguments_with_prune_action_leaves_other_actions_disabled():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    arguments = module.parse_arguments('prune')

    assert 'prune' in arguments
    assert 'create' not in arguments
    assert 'check' not in arguments


def test_parse_arguments_with_dashed_prune_action_leaves_other_actions_disabled():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    arguments = module.parse_arguments('--prune')

    assert 'prune' in arguments
    assert 'create' not in arguments
    assert 'check' not in arguments


def test_parse_arguments_with_multiple_actions_leaves_other_action_disabled():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    arguments = module.parse_arguments('create', 'check')

    assert 'prune' not in arguments
    assert 'create' in arguments
    assert 'check' in arguments


def test_parse_arguments_with_multiple_dashed_actions_leaves_other_action_disabled():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    arguments = module.parse_arguments('--create', '--check')

    assert 'prune' not in arguments
    assert 'create' in arguments
    assert 'check' in arguments


def test_parse_arguments_with_invalid_arguments_exits():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit):
        module.parse_arguments('--posix-me-harder')


def test_parse_arguments_disallows_deprecated_excludes_option():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments('--config', 'myconfig', '--excludes', 'myexcludes')


def test_parse_arguments_disallows_encryption_mode_without_init():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit):
        module.parse_arguments('--config', 'myconfig', '--encryption', 'repokey')


def test_parse_arguments_allows_encryption_mode_with_init():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments('--config', 'myconfig', 'init', '--encryption', 'repokey')


def test_parse_arguments_allows_encryption_mode_with_dashed_init():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments('--config', 'myconfig', '--init', '--encryption', 'repokey')


def test_parse_arguments_requires_encryption_mode_with_init():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit):
        module.parse_arguments('--config', 'myconfig', 'init')


def test_parse_arguments_disallows_append_only_without_init():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit):
        module.parse_arguments('--config', 'myconfig', '--append-only')


def test_parse_arguments_disallows_storage_quota_without_init():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit):
        module.parse_arguments('--config', 'myconfig', '--storage-quota', '5G')


def test_parse_arguments_allows_init_and_prune():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments('--config', 'myconfig', 'init', '--encryption', 'repokey', 'prune')


def test_parse_arguments_allows_init_and_create():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments('--config', 'myconfig', 'init', '--encryption', 'repokey', 'create')


def test_parse_arguments_disallows_init_and_dry_run():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments(
            '--config', 'myconfig', 'init', '--encryption', 'repokey', '--dry-run'
        )


def test_parse_arguments_disallows_repository_without_extract_or_list():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit):
        module.parse_arguments('--config', 'myconfig', '--repository', 'test.borg')


def test_parse_arguments_allows_repository_with_extract():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments(
        '--config', 'myconfig', 'extract', '--repository', 'test.borg', '--archive', 'test'
    )


def test_parse_arguments_allows_repository_with_list():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments('--config', 'myconfig', 'list', '--repository', 'test.borg')


def test_parse_arguments_disallows_archive_without_extract_or_list():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit):
        module.parse_arguments('--config', 'myconfig', '--archive', 'test')


def test_parse_arguments_disallows_restore_paths_without_extract():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit):
        module.parse_arguments('--config', 'myconfig', '--restore-path', 'test')


def test_parse_arguments_allows_archive_with_extract():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments('--config', 'myconfig', 'extract', '--archive', 'test')


def test_parse_arguments_allows_archive_with_dashed_extract():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments('--config', 'myconfig', '--extract', '--archive', 'test')


def test_parse_arguments_allows_archive_with_list():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments('--config', 'myconfig', 'list', '--archive', 'test')


def test_parse_arguments_requires_archive_with_extract():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit):
        module.parse_arguments('--config', 'myconfig', 'extract')


def test_parse_arguments_allows_progress_before_create():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments('--progress', 'create', 'list')


def test_parse_arguments_allows_progress_after_create():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments('create', '--progress', 'list')


def test_parse_arguments_allows_progress_and_extract():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments('--progress', 'extract', '--archive', 'test', 'list')


def test_parse_arguments_disallows_progress_without_create():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit):
        module.parse_arguments('--progress', 'list')


def test_parse_arguments_with_stats_and_create_flags_does_not_raise():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments('--stats', 'create', 'list')


def test_parse_arguments_with_stats_and_prune_flags_does_not_raise():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments('--stats', 'prune', 'list')


def test_parse_arguments_with_stats_flag_but_no_create_or_prune_flag_raises_value_error():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit):
        module.parse_arguments('--stats', 'list')


def test_parse_arguments_with_just_stats_flag_does_not_raise():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments('--stats')


def test_parse_arguments_allows_json_with_list_or_info():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments('list', '--json')
    module.parse_arguments('info', '--json')


def test_parse_arguments_allows_json_with_dashed_info():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    module.parse_arguments('--info', '--json')


def test_parse_arguments_disallows_json_with_both_list_and_info():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(ValueError):
        module.parse_arguments('list', 'info', '--json')


def test_borgmatic_version_matches_news_version():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    borgmatic_version = subprocess.check_output(('borgmatic', '--version')).decode('ascii')
    news_version = open('NEWS').readline()

    assert borgmatic_version == news_version
