import subprocess

from flexmock import flexmock

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
