import subprocess

from flexmock import flexmock

import borgmatic.hooks.command
from borgmatic.commands import borgmatic as module


def test_borgmatic_version_matches_news_version():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    borgmatic_version = subprocess.check_output(('borgmatic', '--version')).decode('ascii')
    news_version = open('NEWS').readline()

    assert borgmatic_version == news_version


def test_run_configuration_without_error_pings_monitoring_hooks_start_and_finish():
    config = {'repositories': [{'path': 'foo'}]}
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False), 'create': flexmock()}
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module).should_receive('run_actions').and_return([])
    flexmock(module.dispatch).should_receive('call_hooks')
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        config,
        module.dispatch.Hook_type.MONITORING,
        'test.yaml',
        module.monitor.State.START,
        object,
        object,
    ).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        config,
        module.dispatch.Hook_type.MONITORING,
        'test.yaml',
        module.monitor.State.FINISH,
        object,
        object,
    ).once()

    list(module.run_configuration('test.yaml', config, ['/tmp/test.yaml'], arguments))


def test_run_configuration_with_borg_version_error_pings_after_command_hook_with_fail_state():
    config = {
        'repositories': [{'path': 'foo'}],
        'commands': ({'after': 'configuration', 'run': ['echo after'], 'states': ['fail']},),
    }
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False), 'create': flexmock()}
    flexmock(module.borg_version).should_receive('local_borg_version').and_raise(ValueError)
    flexmock(module).should_receive('run_actions').and_return([])
    flexmock(module.dispatch).should_receive('call_hooks')
    flexmock(borgmatic.hooks.command).should_receive('execute_hooks')
    flexmock(borgmatic.hooks.command).should_receive('execute_hooks').with_args(
        config['commands'],
        umask=object,
        working_directory=object,
        dry_run=False,
        log_file=object,
        configuration_filename=object,
    ).once()

    list(module.run_configuration('test.yaml', config, ['/tmp/test.yaml'], arguments))


def test_run_configuration_with_action_error_pings_monioring_hooks_start_and_fail():
    config = {'repositories': [{'path': 'foo'}]}
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False), 'create': flexmock()}
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module).should_receive('run_actions').and_raise(OSError)
    flexmock(module.dispatch).should_receive('call_hooks')
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        config,
        module.dispatch.Hook_type.MONITORING,
        'test.yaml',
        module.monitor.State.START,
        object,
        object,
    ).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        config,
        module.dispatch.Hook_type.MONITORING,
        'test.yaml',
        module.monitor.State.FAIL,
        object,
        object,
    ).once()

    list(module.run_configuration('test.yaml', config, ['/tmp/test.yaml'], arguments))
