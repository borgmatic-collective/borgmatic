import logging
import subprocess
import time

import pytest
from flexmock import flexmock

import borgmatic.hooks.command
from borgmatic.commands import borgmatic as module


@pytest.mark.parametrize(
    'config,arguments,expected_actions',
    (
        ({}, {}, []),
        ({'skip_actions': []}, {}, []),
        ({'skip_actions': ['prune', 'check']}, {}, ['prune', 'check']),
        (
            {'skip_actions': ['prune', 'check']},
            {'check': flexmock(force=False)},
            ['prune', 'check'],
        ),
        ({'skip_actions': ['prune', 'check']}, {'check': flexmock(force=True)}, ['prune']),
    ),
)
def test_get_skip_actions_uses_config_and_arguments(config, arguments, expected_actions):
    assert module.get_skip_actions(config, arguments) == expected_actions


def test_monitoring_hooks_with_monioring_disabled_bails():
    flexmock(module).should_receive('get_verbosity').and_return(module.logging.INFO)
    flexmock(module).should_receive('verbosity_to_log_level').and_return(module.DISABLED)
    flexmock(module.dispatch).should_receive('call_hooks').never()

    with module.Monitoring_hooks(
        config_filename='test.yaml',
        config={},
        arguments={'create': flexmock()},
        global_arguments=flexmock(monitoring_verbosity=99, dry_run=False),
    ):
        pass


def test_monitoring_hooks_with_non_primary_action_bails():
    flexmock(module).should_receive('get_verbosity').and_return(module.logging.INFO)
    flexmock(module).should_receive('verbosity_to_log_level').and_return(flexmock())
    flexmock(module.dispatch).should_receive('call_hooks').never()

    with module.Monitoring_hooks(
        config_filename='test.yaml',
        config={},
        arguments={'extract': flexmock()},
        global_arguments=flexmock(monitoring_verbosity=99, dry_run=False),
    ):
        pass


def test_monitoring_hooks_pings_monitors():
    flexmock(module).should_receive('get_verbosity').and_return(module.logging.INFO)
    flexmock(module).should_receive('verbosity_to_log_level').and_return(flexmock())
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'initialize_monitor',
        object,
        object,
        object,
        object,
        object,
    ).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        object,
        object,
        object,
        module.monitor.State.START,
        object,
        object,
    ).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        object,
        object,
        object,
        module.monitor.State.LOG,
        object,
        object,
    ).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        object,
        object,
        object,
        module.monitor.State.FINISH,
        object,
        object,
    ).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        object,
        object,
        object,
        module.monitor.State.FAIL,
        object,
        object,
    ).never()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'destroy_monitor',
        object,
        object,
        object,
        object,
    ).once()

    with module.Monitoring_hooks(
        config_filename='test.yaml',
        config={},
        arguments={'create': flexmock()},
        global_arguments=flexmock(monitoring_verbosity=99, dry_run=False),
    ):
        pass


def test_monitoring_hooks_with_start_ping_error_raises():
    flexmock(module).should_receive('get_verbosity').and_return(module.logging.INFO)
    flexmock(module).should_receive('verbosity_to_log_level').and_return(flexmock())
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'initialize_monitor',
        object,
        object,
        object,
        object,
        object,
    ).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        object,
        object,
        object,
        module.monitor.State.START,
        object,
        object,
    ).and_raise(OSError).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        object,
        object,
        object,
        module.monitor.State.LOG,
        object,
        object,
    ).never()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        object,
        object,
        object,
        module.monitor.State.FINISH,
        object,
        object,
    ).never()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'destroy_monitor',
        object,
        object,
        object,
        object,
    ).never()

    with pytest.raises(ValueError):
        with module.Monitoring_hooks(
            config_filename='test.yaml',
            config={},
            arguments={'create': flexmock()},
            global_arguments=flexmock(monitoring_verbosity=99, dry_run=False),
        ):
            assert False  # This should never get called.


def test_monitoring_hooks_with_log_ping_error_raises():
    flexmock(module).should_receive('get_verbosity').and_return(module.logging.INFO)
    flexmock(module).should_receive('verbosity_to_log_level').and_return(flexmock())
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'initialize_monitor',
        object,
        object,
        object,
        object,
        object,
    ).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        object,
        object,
        object,
        module.monitor.State.START,
        object,
        object,
    ).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        object,
        object,
        object,
        module.monitor.State.LOG,
        object,
        object,
    ).and_raise(OSError).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        object,
        object,
        object,
        module.monitor.State.FINISH,
        object,
        object,
    ).never()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'destroy_monitor',
        object,
        object,
        object,
        object,
    ).never()

    with pytest.raises(ValueError):
        with module.Monitoring_hooks(
            config_filename='test.yaml',
            config={},
            arguments={'create': flexmock()},
            global_arguments=flexmock(monitoring_verbosity=99, dry_run=False),
        ):
            pass


def test_monitoring_hooks_with_finish_ping_error_raises():
    flexmock(module).should_receive('get_verbosity').and_return(module.logging.INFO)
    flexmock(module).should_receive('verbosity_to_log_level').and_return(flexmock())
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'initialize_monitor',
        object,
        object,
        object,
        object,
        object,
    ).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        object,
        object,
        object,
        module.monitor.State.START,
        object,
        object,
    ).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        object,
        object,
        object,
        module.monitor.State.LOG,
        object,
        object,
    ).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        object,
        object,
        object,
        module.monitor.State.FINISH,
        object,
        object,
    ).and_raise(OSError).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'destroy_monitor',
        object,
        object,
        object,
        object,
    ).never()

    with pytest.raises(ValueError):
        with module.Monitoring_hooks(
            config_filename='test.yaml',
            config={},
            arguments={'create': flexmock()},
            global_arguments=flexmock(monitoring_verbosity=99, dry_run=False),
        ):
            pass


def test_monitoring_hooks_with_wrapped_code_error_pings_fail():
    flexmock(module).should_receive('get_verbosity').and_return(module.logging.INFO)
    flexmock(module).should_receive('verbosity_to_log_level').and_return(flexmock())
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'initialize_monitor',
        object,
        object,
        object,
        object,
        object,
    ).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        object,
        object,
        object,
        module.monitor.State.START,
        object,
        object,
    ).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        object,
        object,
        object,
        module.monitor.State.LOG,
        object,
        object,
    ).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        object,
        object,
        object,
        module.monitor.State.FINISH,
        object,
        object,
    ).never()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        object,
        object,
        object,
        module.monitor.State.FAIL,
        object,
        object,
    ).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'destroy_monitor',
        object,
        object,
        object,
        object,
    ).once()

    with pytest.raises(OSError):
        with module.Monitoring_hooks(
            config_filename='test.yaml',
            config={},
            arguments={'create': flexmock()},
            global_arguments=flexmock(monitoring_verbosity=99, dry_run=False),
        ):
            raise OSError()


def test_monitoring_hooks_with_fail_ping_error_raise_original_error():
    flexmock(module).should_receive('get_verbosity').and_return(module.logging.INFO)
    flexmock(module).should_receive('verbosity_to_log_level').and_return(flexmock())
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'initialize_monitor',
        object,
        object,
        object,
        object,
        object,
    ).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        object,
        object,
        object,
        module.monitor.State.START,
        object,
        object,
    ).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        object,
        object,
        object,
        module.monitor.State.LOG,
        object,
        object,
    ).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        object,
        object,
        object,
        module.monitor.State.FINISH,
        object,
        object,
    ).never()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'ping_monitor',
        object,
        object,
        object,
        module.monitor.State.FAIL,
        object,
        object,
    ).and_raise(OSError).once()
    flexmock(module.dispatch).should_receive('call_hooks').with_args(
        'destroy_monitor',
        object,
        object,
        object,
        object,
    ).never()

    with pytest.raises(OSError):
        with module.Monitoring_hooks(
            config_filename='test.yaml',
            config={},
            arguments={'create': flexmock()},
            global_arguments=flexmock(monitoring_verbosity=99, dry_run=False),
        ):
            raise OSError()


def test_run_configuration_runs_actions_for_each_repository():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module).should_receive('Monitoring_hooks').and_return(flexmock())
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    expected_results = [flexmock(), flexmock()]
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_actions').and_return(expected_results[:1]).and_return(
        expected_results[1:]
    )
    config = {'repositories': [{'path': 'foo'}, {'path': 'bar'}]}
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False)}

    results = list(module.run_configuration('test.yaml', config, ['/tmp/test.yaml'], arguments))

    assert results == expected_results


def test_run_configuration_with_skip_actions_does_not_raise():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module).should_receive('get_skip_actions').and_return(['compact'])
    flexmock(module).should_receive('Monitoring_hooks').and_return(flexmock())
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_actions').and_return(flexmock()).and_return(flexmock())
    config = {'repositories': [{'path': 'foo'}, {'path': 'bar'}], 'skip_actions': ['compact']}
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False)}

    list(module.run_configuration('test.yaml', config, ['/tmp/test.yaml'], arguments))


def test_run_configuration_with_invalid_borg_version_errors():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module).should_receive('Monitoring_hooks').and_return(flexmock())
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(module.borg_version).should_receive('local_borg_version').and_raise(ValueError)
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_actions').never()
    config = {'repositories': [{'path': 'foo'}]}
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'prune': flexmock(),
    }

    list(module.run_configuration('test.yaml', config, ['/tmp/test.yaml'], arguments))


def test_run_configuration_logs_actions_error():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module).should_receive('Monitoring_hooks').and_return(flexmock())
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    expected_results = [flexmock(), flexmock()]
    flexmock(module).should_receive('log_error_records').and_return(
        expected_results[:1]
    ).and_return(expected_results[1:])
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_actions').and_raise(OSError)
    flexmock(module.command).should_receive('filter_hooks')
    flexmock(module.command).should_receive('execute_hooks')
    config = {'repositories': [{'path': 'foo'}]}
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False)}

    results = list(module.run_configuration('test.yaml', config, ['/tmp/test.yaml'], arguments))

    assert results == expected_results


def test_run_configuration_skips_remaining_actions_for_actions_soft_failure_but_still_runs_next_repository_actions():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module).should_receive('Monitoring_hooks').and_return(flexmock())
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    error = subprocess.CalledProcessError(borgmatic.hooks.command.SOFT_FAIL_EXIT_CODE, 'try again')
    log = flexmock()
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_actions').twice().and_raise(error).and_yield(log)
    flexmock(module).should_receive('log_error_records').never()
    flexmock(module.command).should_receive('considered_soft_failure').and_return(True)
    config = {'repositories': [{'path': 'foo'}, {'path': 'bar'}]}
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'create': flexmock(),
    }

    results = list(module.run_configuration('test.yaml', config, ['/tmp/test.yaml'], arguments))

    assert results == [log]


def test_run_configuration_does_not_call_monitoring_hooks_if_monitoring_hooks_are_disabled():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(module.DISABLED)
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module).should_receive('Monitoring_hooks').and_return(flexmock())
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())

    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_actions').and_return([])

    config = {'repositories': [{'path': 'foo'}]}
    arguments = {
        'global': flexmock(monitoring_verbosity=-2, dry_run=False),
        'create': flexmock(),
    }
    results = list(module.run_configuration('test.yaml', config, ['/tmp/test.yaml'], arguments))
    assert results == []


def test_run_configuration_logs_on_error_hook_error():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module).should_receive('Monitoring_hooks').and_return(flexmock())
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module.command).should_receive('filter_hooks')
    flexmock(module.command).should_receive('execute_hooks').and_raise(OSError)
    expected_results = [flexmock(), flexmock()]
    flexmock(module).should_receive('log_error_records').and_return(
        expected_results[:1]
    ).and_return(expected_results[1:2]).and_return(expected_results[2:])
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_actions').and_raise(OSError)
    config = {'repositories': [{'path': 'foo'}]}
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'create': flexmock(),
    }

    results = list(module.run_configuration('test.yaml', config, ['/tmp/test.yaml'], arguments))

    assert results == expected_results


def test_run_configuration_logs_on_before_command_hook_error():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module).should_receive('Monitoring_hooks').and_return(flexmock())
    flexmock(module.command).should_receive('Before_after_hooks').and_raise(OSError)
    flexmock(module.borg_version).should_receive('local_borg_version').never()
    flexmock(module.command).should_receive('filter_hooks')
    flexmock(module.command).should_receive('execute_hooks')
    expected_results = [flexmock()]
    flexmock(module).should_receive('log_error_records').and_return(expected_results)
    flexmock(module).should_receive('Log_prefix').never()
    flexmock(module).should_receive('run_actions').never()
    config = {'repositories': [{'path': 'foo'}]}
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'create': flexmock(),
    }

    results = list(module.run_configuration('test.yaml', config, ['/tmp/test.yaml'], arguments))

    assert results == expected_results


def test_run_configuration_logs_on_monitoring_hook_error():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module).should_receive('Monitoring_hooks').and_raise(OSError)
    flexmock(module.command).should_receive('Before_after_hooks').never()
    flexmock(module.borg_version).should_receive('local_borg_version').never()
    flexmock(module.command).should_receive('filter_hooks')
    flexmock(module.command).should_receive('execute_hooks')
    expected_results = [flexmock()]
    flexmock(module).should_receive('log_error_records').and_return(expected_results)
    flexmock(module).should_receive('Log_prefix').never()
    flexmock(module).should_receive('run_actions').never()
    config = {'repositories': [{'path': 'foo'}]}
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'create': flexmock(),
    }

    results = list(module.run_configuration('test.yaml', config, ['/tmp/test.yaml'], arguments))

    assert results == expected_results


def test_run_configuration_bails_for_on_error_hook_soft_failure():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module).should_receive('Monitoring_hooks').and_return(flexmock())
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    error = subprocess.CalledProcessError(borgmatic.hooks.command.SOFT_FAIL_EXIT_CODE, 'try again')
    flexmock(module.command).should_receive('filter_hooks')
    flexmock(module.command).should_receive('execute_hooks').and_raise(error)
    expected_results = [flexmock(), flexmock()]
    flexmock(module).should_receive('log_error_records').and_return(
        expected_results[:1]
    ).and_return(expected_results[1:])
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_actions').and_raise(OSError)
    config = {'repositories': [{'path': 'foo'}]}
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'create': flexmock(),
    }

    results = list(module.run_configuration('test.yaml', config, ['/tmp/test.yaml'], arguments))

    assert results == expected_results


def test_run_configuration_retries_soft_error():
    # Run action first fails, second passes.
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module).should_receive('Monitoring_hooks').and_return(flexmock())
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_actions').and_raise(OSError).and_return([])
    flexmock(module).should_receive('log_error_records').and_return([flexmock()]).once()
    flexmock(module.command).should_receive('filter_hooks').never()
    flexmock(module.command).should_receive('execute_hooks').never()
    config = {'repositories': [{'path': 'foo'}], 'retries': 1}
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'create': flexmock(),
    }

    results = list(module.run_configuration('test.yaml', config, ['/tmp/test.yaml'], arguments))

    assert results == []


def test_run_configuration_retries_hard_error():
    # Run action fails twice.
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module).should_receive('Monitoring_hooks').and_return(flexmock())
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_actions').and_raise(OSError).times(2)
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running actions for repository',
        OSError,
        levelno=logging.WARNING,
        log_command_error_output=True,
    ).and_return([flexmock()])
    error_logs = [flexmock(), flexmock()]
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running actions for repository',
        OSError,
    ).and_return(error_logs[:1]).ordered()
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running configuration',
    ).and_return(error_logs[1:]).ordered()
    flexmock(module.command).should_receive('filter_hooks')
    flexmock(module.command).should_receive('execute_hooks')
    config = {'repositories': [{'path': 'foo'}], 'retries': 1}
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'create': flexmock(),
    }

    results = list(module.run_configuration('test.yaml', config, ['/tmp/test.yaml'], arguments))

    assert results == error_logs


def test_run_configuration_retries_repositories_in_order():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module).should_receive('Monitoring_hooks').and_return(flexmock())
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_actions').and_raise(OSError).times(2)
    expected_results = [flexmock(), flexmock(), flexmock()]
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running actions for repository', OSError
    ).and_return(expected_results[:1]).ordered()
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running actions for repository', OSError
    ).and_return(expected_results[1:2]).ordered()
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running configuration',
    ).and_return(expected_results[2:]).ordered()
    flexmock(module.command).should_receive('filter_hooks')
    flexmock(module.command).should_receive('execute_hooks')
    config = {'repositories': [{'path': 'foo'}, {'path': 'bar'}]}
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'create': flexmock(),
    }

    results = list(module.run_configuration('test.yaml', config, ['/tmp/test.yaml'], arguments))

    assert results == expected_results


def test_run_configuration_retries_round_robin():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module).should_receive('Monitoring_hooks').and_return(flexmock())
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_actions').and_raise(OSError).times(4)
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running actions for repository',
        OSError,
        levelno=logging.WARNING,
        log_command_error_output=True,
    ).and_return([flexmock()]).ordered()
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running actions for repository',
        OSError,
        levelno=logging.WARNING,
        log_command_error_output=True,
    ).and_return([flexmock()]).ordered()
    foo_error_logs = [flexmock()]
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running actions for repository', OSError
    ).and_return(foo_error_logs).ordered()
    bar_error_logs = [flexmock()]
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running actions for repository', OSError
    ).and_return(bar_error_logs).ordered()
    config_error_logs = [flexmock()]
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running configuration',
    ).and_return(config_error_logs).ordered()
    flexmock(module.command).should_receive('filter_hooks')
    flexmock(module.command).should_receive('execute_hooks')
    config = {
        'repositories': [{'path': 'foo'}, {'path': 'bar'}],
        'retries': 1,
    }
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'create': flexmock(),
    }

    results = list(module.run_configuration('test.yaml', config, ['/tmp/test.yaml'], arguments))

    assert results == foo_error_logs + bar_error_logs + config_error_logs


def test_run_configuration_with_one_retry():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module).should_receive('Monitoring_hooks').and_return(flexmock())
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_actions').and_raise(OSError).and_raise(OSError).and_return(
        []
    ).and_raise(OSError).times(4)
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running actions for repository',
        OSError,
        levelno=logging.WARNING,
        log_command_error_output=True,
    ).and_return([flexmock()]).ordered()
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running actions for repository',
        OSError,
        levelno=logging.WARNING,
        log_command_error_output=True,
    ).and_return(flexmock()).ordered()
    error_logs = [flexmock(), flexmock()]
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running actions for repository', OSError
    ).and_return(error_logs[:1]).ordered()
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running configuration',
    ).and_return(error_logs[1:]).ordered()
    flexmock(module.command).should_receive('filter_hooks')
    flexmock(module.command).should_receive('execute_hooks')
    config = {
        'repositories': [{'path': 'foo'}, {'path': 'bar'}],
        'retries': 1,
    }
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'create': flexmock(),
    }

    results = list(module.run_configuration('test.yaml', config, ['/tmp/test.yaml'], arguments))

    assert results == error_logs


def test_run_configuration_with_retry_wait_does_backoff_after_each_retry():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module).should_receive('Monitoring_hooks').and_return(flexmock())
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_actions').and_raise(OSError).times(4)
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running actions for repository',
        OSError,
        levelno=logging.WARNING,
        log_command_error_output=True,
    ).and_return([flexmock()]).ordered()

    flexmock(time).should_receive('sleep').with_args(10).and_return().ordered()
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running actions for repository',
        OSError,
        levelno=logging.WARNING,
        log_command_error_output=True,
    ).and_return([flexmock()]).ordered()

    flexmock(time).should_receive('sleep').with_args(20).and_return().ordered()
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running actions for repository',
        OSError,
        levelno=logging.WARNING,
        log_command_error_output=True,
    ).and_return([flexmock()]).ordered()

    flexmock(time).should_receive('sleep').with_args(30).and_return().ordered()
    error_logs = [flexmock(), flexmock()]
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running actions for repository', OSError
    ).and_return(error_logs[:1]).ordered()
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running configuration',
    ).and_return(error_logs[1:]).ordered()
    flexmock(module.command).should_receive('filter_hooks')
    flexmock(module.command).should_receive('execute_hooks')
    config = {
        'repositories': [{'path': 'foo'}],
        'retries': 3,
        'retry_wait': 10,
    }
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'create': flexmock(),
    }

    results = list(module.run_configuration('test.yaml', config, ['/tmp/test.yaml'], arguments))

    assert results == error_logs


def test_run_configuration_with_multiple_repositories_retries_with_timeout():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module).should_receive('Monitoring_hooks').and_return(flexmock())
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_actions').and_raise(OSError).and_raise(OSError).and_return(
        []
    ).and_raise(OSError).times(4)
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running actions for repository',
        OSError,
        levelno=logging.WARNING,
        log_command_error_output=True,
    ).and_return([flexmock()]).ordered()
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running actions for repository',
        OSError,
        levelno=logging.WARNING,
        log_command_error_output=True,
    ).and_return([flexmock()]).ordered()

    # Sleep before retrying foo (and passing)
    flexmock(time).should_receive('sleep').with_args(10).and_return().ordered()

    # Sleep before retrying bar (and failing)
    flexmock(time).should_receive('sleep').with_args(10).and_return().ordered()
    error_logs = [flexmock(), flexmock()]
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running actions for repository', OSError
    ).and_return(error_logs[:1]).ordered()
    flexmock(module).should_receive('log_error_records').with_args(
        'Error running configuration',
    ).and_return(error_logs[1:]).ordered()
    flexmock(module.command).should_receive('filter_hooks')
    flexmock(module.command).should_receive('execute_hooks')
    config = {
        'repositories': [{'path': 'foo'}, {'path': 'bar'}],
        'retries': 1,
        'retry_wait': 10,
    }
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'create': flexmock(),
    }

    results = list(module.run_configuration('test.yaml', config, ['/tmp/test.yaml'], arguments))

    assert results == error_logs


def test_run_actions_runs_repo_create():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(borgmatic.actions.repo_create).should_receive('run_repo_create').once()

    tuple(
        module.run_actions(
            arguments={
                'global': flexmock(dry_run=False),
                'repo-create': flexmock(),
            },
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )


def test_run_actions_adds_label_file_to_hook_context():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    expected = flexmock()
    flexmock(borgmatic.actions.create).should_receive('run_create').with_args(
        config_filename=object,
        repository={'path': 'repo', 'label': 'my repo'},
        config={'repositories': []},
        config_paths=[],
        local_borg_version=object,
        create_arguments=object,
        global_arguments=object,
        dry_run_label='',
        local_path=object,
        remote_path=object,
    ).once().and_return(expected)

    result = tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'create': flexmock()},
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo', 'label': 'my repo'},
        )
    )
    assert result == (expected,)


def test_run_actions_adds_log_file_to_hook_context():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    expected = flexmock()
    flexmock(borgmatic.actions.create).should_receive('run_create').with_args(
        config_filename=object,
        repository={'path': 'repo'},
        config={'repositories': [], 'log_file': 'foo'},
        config_paths=[],
        local_borg_version=object,
        create_arguments=object,
        global_arguments=object,
        dry_run_label='',
        local_path=object,
        remote_path=object,
    ).once().and_return(expected)

    result = tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'create': flexmock()},
            config_filename=flexmock(),
            config={'repositories': [], 'log_file': 'foo'},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )
    assert result == (expected,)


def test_run_actions_runs_transfer():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(borgmatic.actions.transfer).should_receive('run_transfer').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'transfer': flexmock()},
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )


def test_run_actions_runs_create():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    expected = flexmock()
    flexmock(borgmatic.actions.create).should_receive('run_create').and_yield(expected).once()

    result = tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'create': flexmock()},
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )
    assert result == (expected,)


def test_run_actions_with_skip_actions_does_not_run_action_or_action_command_hooks():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return(['create'])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(module.command).should_receive('Before_after_hooks').with_args(
        command_hooks=object,
        before_after='action',
        umask=object,
        working_directory=object,
        dry_run=object,
        action_names=object,
        configuration_filename=object,
        repository_label=object,
        log_file=object,
        repositories=object,
        repository=object,
    ).never()
    flexmock(borgmatic.actions.create).should_receive('run_create').never()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'create': flexmock()},
            config_filename=flexmock(),
            config={'repositories': [], 'skip_actions': ['create']},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )


def test_run_actions_runs_recreate():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())

    flexmock(borgmatic.actions.recreate).should_receive('run_recreate').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'recreate': flexmock()},
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )


def test_run_actions_runs_prune():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(borgmatic.actions.prune).should_receive('run_prune').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'prune': flexmock()},
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )


def test_run_actions_runs_compact():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(borgmatic.actions.compact).should_receive('run_compact').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'compact': flexmock()},
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )


def test_run_actions_runs_check_when_repository_enabled_for_checks():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(module.checks).should_receive('repository_enabled_for_checks').and_return(True)
    flexmock(borgmatic.actions.check).should_receive('run_check').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'check': flexmock()},
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )


def test_run_actions_skips_check_when_repository_not_enabled_for_checks():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(module.checks).should_receive('repository_enabled_for_checks').and_return(False)
    flexmock(borgmatic.actions.check).should_receive('run_check').never()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'check': flexmock()},
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )


def test_run_actions_runs_extract():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(borgmatic.actions.extract).should_receive('run_extract').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'extract': flexmock()},
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )


def test_run_actions_runs_export_tar():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(borgmatic.actions.export_tar).should_receive('run_export_tar').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'export-tar': flexmock()},
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )


def test_run_actions_runs_mount():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(borgmatic.actions.mount).should_receive('run_mount').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'mount': flexmock()},
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )


def test_run_actions_runs_restore():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(borgmatic.actions.restore).should_receive('run_restore').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'restore': flexmock()},
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )


def test_run_actions_runs_repo_list():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    expected = flexmock()
    flexmock(borgmatic.actions.repo_list).should_receive('run_repo_list').and_yield(expected).once()

    result = tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'repo-list': flexmock()},
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )
    assert result == (expected,)


def test_run_actions_runs_list():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    expected = flexmock()
    flexmock(borgmatic.actions.list).should_receive('run_list').and_yield(expected).once()

    result = tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'list': flexmock()},
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )
    assert result == (expected,)


def test_run_actions_runs_repo_info():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    expected = flexmock()
    flexmock(borgmatic.actions.repo_info).should_receive('run_repo_info').and_yield(expected).once()

    result = tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'repo-info': flexmock()},
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )
    assert result == (expected,)


def test_run_actions_runs_info():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    expected = flexmock()
    flexmock(borgmatic.actions.info).should_receive('run_info').and_yield(expected).once()

    result = tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'info': flexmock()},
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )
    assert result == (expected,)


def test_run_actions_runs_break_lock():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(borgmatic.actions.break_lock).should_receive('run_break_lock').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'break-lock': flexmock()},
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )


def test_run_actions_runs_export_key():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(borgmatic.actions.export_key).should_receive('run_export_key').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'export': flexmock()},
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )


def test_run_actions_runs_import_key():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(borgmatic.actions.import_key).should_receive('run_import_key').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'import': flexmock()},
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )


def test_run_actions_runs_change_passphrase():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(borgmatic.actions.change_passphrase).should_receive('run_change_passphrase').once()

    tuple(
        module.run_actions(
            arguments={
                'global': flexmock(dry_run=False),
                'change-passphrase': flexmock(),
            },
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )


def test_run_actions_runs_delete():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(borgmatic.actions.delete).should_receive('run_delete').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'delete': flexmock()},
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )


def test_run_actions_runs_repo_delete():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(borgmatic.actions.repo_delete).should_receive('run_repo_delete').once()

    tuple(
        module.run_actions(
            arguments={
                'global': flexmock(dry_run=False),
                'repo-delete': flexmock(),
            },
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )


def test_run_actions_runs_borg():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(borgmatic.actions.borg).should_receive('run_borg').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'borg': flexmock()},
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )


def test_run_actions_runs_multiple_actions_in_argument_order():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())
    flexmock(borgmatic.actions.borg).should_receive('run_borg').once().ordered()
    flexmock(borgmatic.actions.restore).should_receive('run_restore').once().ordered()

    tuple(
        module.run_actions(
            arguments={
                'global': flexmock(dry_run=False),
                'borg': flexmock(),
                'restore': flexmock(),
            },
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )


def test_run_actions_runs_action_hooks_for_one_action_at_a_time():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('get_skip_actions').and_return([])
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.command).should_receive('Before_after_hooks').and_return(flexmock())

    for action_name in ('borg', 'restore'):
        flexmock(module.command).should_receive('Before_after_hooks').with_args(
            command_hooks=object,
            before_after='action',
            umask=object,
            working_directory=object,
            dry_run=object,
            action_names=(action_name,),
            configuration_filename=object,
            repository_label=object,
            log_file=object,
            repositories=object,
            repository=object,
        ).and_return(flexmock()).once()

    flexmock(borgmatic.actions.borg).should_receive('run_borg')
    flexmock(borgmatic.actions.restore).should_receive('run_restore')

    tuple(
        module.run_actions(
            arguments={
                'global': flexmock(dry_run=False),
                'borg': flexmock(),
                'restore': flexmock(),
            },
            config_filename=flexmock(),
            config={'repositories': []},
            config_paths=[],
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository={'path': 'repo'},
        )
    )


@pytest.mark.parametrize(
    'resolve_env',
    ((True, False),),
)
def test_load_configurations_collects_parsed_configurations_and_logs(resolve_env):
    configuration = flexmock()
    other_configuration = flexmock()
    test_expected_logs = [flexmock(), flexmock()]
    other_expected_logs = [flexmock(), flexmock()]
    flexmock(module.validate).should_receive('parse_configuration').and_return(
        configuration, ['/tmp/test.yaml'], test_expected_logs
    ).and_return(other_configuration, ['/tmp/other.yaml'], other_expected_logs)

    configs, config_paths, logs = tuple(
        module.load_configurations(
            ('test.yaml', 'other.yaml'),
            arguments=flexmock(),
            resolve_env=resolve_env,
        )
    )

    assert configs == {'test.yaml': configuration, 'other.yaml': other_configuration}
    assert config_paths == ['/tmp/other.yaml', '/tmp/test.yaml']
    assert set(logs) >= set(test_expected_logs + other_expected_logs)


def test_load_configurations_logs_warning_for_permission_error():
    flexmock(module.validate).should_receive('parse_configuration').and_raise(PermissionError)

    configs, config_paths, logs = tuple(
        module.load_configurations(('test.yaml',), arguments=flexmock())
    )

    assert configs == {}
    assert config_paths == []
    assert max(log.levelno for log in logs) == logging.WARNING


def test_load_configurations_logs_critical_for_parse_error():
    flexmock(module.validate).should_receive('parse_configuration').and_raise(ValueError)

    configs, config_paths, logs = tuple(
        module.load_configurations(('test.yaml',), arguments=flexmock())
    )

    assert configs == {}
    assert config_paths == []
    assert max(log.levelno for log in logs) == logging.CRITICAL


def test_log_record_does_not_raise():
    module.log_record(levelno=1, foo='bar', baz='quux')


def test_log_record_with_suppress_does_not_raise():
    module.log_record(levelno=1, foo='bar', baz='quux', suppress_log=True)


def test_log_error_records_generates_output_logs_for_message_only():
    flexmock(module).should_receive('log_record').replace_with(dict).once()

    logs = tuple(module.log_error_records('Error'))

    assert {log['levelno'] for log in logs} == {logging.CRITICAL}


def test_log_error_records_generates_output_logs_for_called_process_error_with_bytes_ouput():
    flexmock(module).should_receive('log_record').replace_with(dict).times(3)
    flexmock(module.logger).should_receive('getEffectiveLevel').and_return(logging.WARNING)

    logs = tuple(
        module.log_error_records('Error', subprocess.CalledProcessError(1, 'ls', b'error output'))
    )

    assert {log['levelno'] for log in logs} == {logging.CRITICAL}
    assert any(log for log in logs if 'error output' in str(log))


def test_log_error_records_generates_output_logs_for_called_process_error_with_string_ouput():
    flexmock(module).should_receive('log_record').replace_with(dict).times(3)
    flexmock(module.logger).should_receive('getEffectiveLevel').and_return(logging.WARNING)

    logs = tuple(
        module.log_error_records('Error', subprocess.CalledProcessError(1, 'ls', 'error output'))
    )

    assert {log['levelno'] for log in logs} == {logging.CRITICAL}
    assert any(log for log in logs if 'error output' in str(log))


def test_log_error_records_generates_work_around_output_logs_for_called_process_error_with_repository_access_aborted_exit_code():
    flexmock(module).should_receive('log_record').replace_with(dict).times(4)
    flexmock(module.logger).should_receive('getEffectiveLevel').and_return(logging.WARNING)

    logs = tuple(
        module.log_error_records(
            'Error',
            subprocess.CalledProcessError(
                module.BORG_REPOSITORY_ACCESS_ABORTED_EXIT_CODE, 'ls', 'error output'
            ),
        )
    )

    assert {log['levelno'] for log in logs} == {logging.CRITICAL}
    assert any(log for log in logs if 'error output' in str(log))
    assert any(log for log in logs if 'To work around this' in str(log))


def test_log_error_records_splits_called_process_error_with_multiline_ouput_into_multiple_logs():
    flexmock(module).should_receive('log_record').replace_with(dict).times(4)
    flexmock(module.logger).should_receive('getEffectiveLevel').and_return(logging.WARNING)

    logs = tuple(
        module.log_error_records(
            'Error', subprocess.CalledProcessError(1, 'ls', 'error output\nanother line')
        )
    )

    assert {log['levelno'] for log in logs} == {logging.CRITICAL}
    assert any(log for log in logs if 'error output' in str(log))


def test_log_error_records_generates_logs_for_value_error():
    flexmock(module).should_receive('log_record').replace_with(dict).twice()

    logs = tuple(module.log_error_records('Error', ValueError()))

    assert {log['levelno'] for log in logs} == {logging.CRITICAL}


def test_log_error_records_generates_logs_for_os_error():
    flexmock(module).should_receive('log_record').replace_with(dict).twice()

    logs = tuple(module.log_error_records('Error', OSError()))

    assert {log['levelno'] for log in logs} == {logging.CRITICAL}


def test_log_error_records_generates_nothing_for_other_error():
    flexmock(module).should_receive('log_record').never()

    logs = tuple(module.log_error_records('Error', KeyError()))

    assert logs == ()


def test_get_local_path_uses_configuration_value():
    assert module.get_local_path({'test.yaml': {'local_path': 'borg1'}}) == 'borg1'


def test_get_local_path_without_local_path_defaults_to_borg():
    assert module.get_local_path({'test.yaml': {}}) == 'borg'


def test_collect_highlander_action_summary_logs_info_for_success_with_bootstrap():
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module.borgmatic.actions.config.bootstrap).should_receive('run_bootstrap')
    arguments = {
        'bootstrap': flexmock(repository='repo', local_path='borg7'),
        'global': flexmock(dry_run=False),
    }

    logs = tuple(
        module.collect_highlander_action_summary_logs(
            {'test.yaml': {}}, arguments=arguments, configuration_parse_errors=False
        )
    )
    assert {log.levelno for log in logs} == {logging.ANSWER}


def test_collect_highlander_action_summary_logs_error_on_bootstrap_failure():
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module.borgmatic.actions.config.bootstrap).should_receive('run_bootstrap').and_raise(
        ValueError
    )
    arguments = {
        'bootstrap': flexmock(repository='repo', local_path='borg7'),
        'global': flexmock(dry_run=False),
    }

    logs = tuple(
        module.collect_highlander_action_summary_logs(
            {'test.yaml': {}}, arguments=arguments, configuration_parse_errors=False
        )
    )

    assert {log.levelno for log in logs} == {logging.CRITICAL}


def test_collect_highlander_action_summary_logs_error_on_bootstrap_local_borg_version_failure():
    flexmock(module.borg_version).should_receive('local_borg_version').and_raise(ValueError)
    flexmock(module.borgmatic.actions.config.bootstrap).should_receive('run_bootstrap').never()
    arguments = {
        'bootstrap': flexmock(repository='repo', local_path='borg7'),
        'global': flexmock(dry_run=False),
    }

    logs = tuple(
        module.collect_highlander_action_summary_logs(
            {'test.yaml': {}}, arguments=arguments, configuration_parse_errors=False
        )
    )

    assert {log.levelno for log in logs} == {logging.CRITICAL}


def test_collect_highlander_action_summary_logs_info_for_success_with_generate():
    flexmock(module.borgmatic.actions.config.generate).should_receive('run_generate')
    arguments = {
        'generate': flexmock(destination='test.yaml'),
        'global': flexmock(dry_run=False),
    }

    logs = tuple(
        module.collect_highlander_action_summary_logs(
            {'test.yaml': {}}, arguments=arguments, configuration_parse_errors=False
        )
    )
    assert {log.levelno for log in logs} == {logging.ANSWER}


def test_collect_highlander_action_summary_logs_error_on_generate_failure():
    flexmock(module.borgmatic.actions.config.generate).should_receive('run_generate').and_raise(
        ValueError
    )
    arguments = {
        'generate': flexmock(destination='test.yaml'),
        'global': flexmock(dry_run=False),
    }

    logs = tuple(
        module.collect_highlander_action_summary_logs(
            {'test.yaml': {}}, arguments=arguments, configuration_parse_errors=False
        )
    )

    assert {log.levelno for log in logs} == {logging.CRITICAL}


def test_collect_highlander_action_summary_logs_info_for_success_with_validate():
    flexmock(module.borgmatic.actions.config.validate).should_receive('run_validate')
    arguments = {
        'validate': flexmock(),
        'global': flexmock(dry_run=False),
    }

    logs = tuple(
        module.collect_highlander_action_summary_logs(
            {'test.yaml': {}}, arguments=arguments, configuration_parse_errors=False
        )
    )
    assert {log.levelno for log in logs} == {logging.ANSWER}


def test_collect_highlander_action_summary_logs_error_on_validate_parse_failure():
    flexmock(module.borgmatic.actions.config.validate).should_receive('run_validate')
    arguments = {
        'validate': flexmock(),
        'global': flexmock(dry_run=False),
    }

    logs = tuple(
        module.collect_highlander_action_summary_logs(
            {'test.yaml': {}}, arguments=arguments, configuration_parse_errors=True
        )
    )

    assert {log.levelno for log in logs} == {logging.CRITICAL}


def test_collect_highlander_action_summary_logs_error_on_run_validate_failure():
    flexmock(module.borgmatic.actions.config.validate).should_receive('run_validate').and_raise(
        ValueError
    )
    arguments = {
        'validate': flexmock(),
        'global': flexmock(dry_run=False),
    }

    logs = tuple(
        module.collect_highlander_action_summary_logs(
            {'test.yaml': {}}, arguments=arguments, configuration_parse_errors=False
        )
    )

    assert {log.levelno for log in logs} == {logging.CRITICAL}


def test_collect_configuration_run_summary_logs_info_for_success():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module.command).should_receive('filter_hooks').with_args(
        object, before='everything', action_names=object
    )
    flexmock(module.command).should_receive('filter_hooks').with_args(
        object, after='everything', action_names=object, state_names=['finish']
    )
    flexmock(module.command).should_receive('execute_hooks')
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_configuration').and_return([])
    arguments = {'global': flexmock(dry_run=False)}

    logs = tuple(
        module.collect_configuration_run_summary_logs(
            {'test.yaml': {}},
            config_paths=['/tmp/test.yaml'],
            arguments=arguments,
            log_file_path=None,
        )
    )

    assert {log.levelno for log in logs} == {logging.INFO}


def test_collect_configuration_run_summary_executes_hooks_for_create():
    before_everything_hook = {'before': 'everything', 'run': ['echo hi']}
    after_everything_hook = {'after': 'everything', 'run': ['echo hi']}
    command_hooks = (before_everything_hook, after_everything_hook)
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module.command).should_receive('filter_hooks').with_args(
        command_hooks, before='everything', action_names=object
    ).and_return([before_everything_hook])
    flexmock(module.command).should_receive('filter_hooks').with_args(
        command_hooks, after='everything', action_names=object, state_names=['finish']
    ).and_return([after_everything_hook])
    flexmock(module.command).should_receive('execute_hooks').twice()
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_configuration').and_return([])
    arguments = {
        'create': flexmock(),
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
    }

    logs = tuple(
        module.collect_configuration_run_summary_logs(
            {'test.yaml': {'commands': command_hooks}},
            config_paths=['/tmp/test.yaml'],
            arguments=arguments,
            log_file_path=None,
        )
    )

    assert {log.levelno for log in logs} == {logging.INFO}


def test_collect_configuration_run_summary_deduplicates_everything_hooks_across_config_files():
    before_everything_hook = {'before': 'everything', 'run': ['echo hi']}
    after_everything_hook = {'after': 'everything', 'run': ['echo hi']}
    command_hooks = (before_everything_hook, after_everything_hook)
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module.command).should_receive('filter_hooks').with_args(
        command_hooks, before='everything', action_names=object
    ).and_return([before_everything_hook]).once()
    flexmock(module.command).should_receive('filter_hooks').with_args(
        (after_everything_hook,), before='everything', action_names=object
    ).and_return([]).once()
    flexmock(module.command).should_receive('filter_hooks').with_args(
        command_hooks, after='everything', action_names=object, state_names=['finish']
    ).and_return([after_everything_hook]).once()
    flexmock(module.command).should_receive('filter_hooks').with_args(
        (before_everything_hook,), after='everything', action_names=object, state_names=['finish']
    ).and_return([]).once()
    flexmock(module.command).should_receive('execute_hooks').twice()
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_configuration').and_return([])
    arguments = {
        'create': flexmock(),
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
    }

    logs = tuple(
        module.collect_configuration_run_summary_logs(
            {'test.yaml': {'commands': command_hooks}, 'other.yaml': {'commands': command_hooks}},
            config_paths=['/tmp/test.yaml', '/tmp/other.yaml'],
            arguments=arguments,
            log_file_path=None,
        )
    )

    assert {log.levelno for log in logs} == {logging.INFO}


def test_collect_configuration_run_summary_logs_info_for_success_with_extract():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module.command).should_receive('filter_hooks').with_args(
        object, before='everything', action_names=object
    )
    flexmock(module.command).should_receive('filter_hooks').with_args(
        object, after='everything', action_names=object, state_names=['finish']
    )
    flexmock(module.command).should_receive('execute_hooks')
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_configuration').and_return([])
    arguments = {
        'extract': flexmock(repository='repo'),
        'global': flexmock(dry_run=False),
    }

    logs = tuple(
        module.collect_configuration_run_summary_logs(
            {'test.yaml': {}},
            config_paths=['/tmp/test.yaml'],
            arguments=arguments,
            log_file_path=None,
        )
    )

    assert {log.levelno for log in logs} == {logging.INFO}


def test_collect_configuration_run_summary_logs_extract_with_repository_error():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository').and_raise(
        ValueError
    )
    expected_logs = (flexmock(),)
    flexmock(module).should_receive('log_error_records').and_return(expected_logs)
    arguments = {'extract': flexmock(repository='repo')}

    logs = tuple(
        module.collect_configuration_run_summary_logs(
            {'test.yaml': {}},
            config_paths=['/tmp/test.yaml'],
            arguments=arguments,
            log_file_path=None,
        )
    )

    assert logs == expected_logs


def test_collect_configuration_run_summary_logs_info_for_success_with_mount():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module.command).should_receive('filter_hooks').with_args(
        object, before='everything', action_names=object
    )
    flexmock(module.command).should_receive('filter_hooks').with_args(
        object, after='everything', action_names=object, state_names=['finish']
    )
    flexmock(module.command).should_receive('execute_hooks')
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_configuration').and_return([])
    arguments = {
        'mount': flexmock(repository='repo'),
        'global': flexmock(dry_run=False),
    }

    logs = tuple(
        module.collect_configuration_run_summary_logs(
            {'test.yaml': {}},
            config_paths=['/tmp/test.yaml'],
            arguments=arguments,
            log_file_path=None,
        )
    )

    assert {log.levelno for log in logs} == {logging.INFO}


def test_collect_configuration_run_summary_logs_mount_with_repository_error():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository').and_raise(
        ValueError
    )
    expected_logs = (flexmock(),)
    flexmock(module).should_receive('log_error_records').and_return(expected_logs)
    arguments = {
        'mount': flexmock(repository='repo'),
        'global': flexmock(dry_run=False),
    }

    logs = tuple(
        module.collect_configuration_run_summary_logs(
            {'test.yaml': {}},
            config_paths=['/tmp/test.yaml'],
            arguments=arguments,
            log_file_path=None,
        )
    )

    assert logs == expected_logs


def test_collect_configuration_run_summary_logs_missing_configs_error():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module.command).should_receive('filter_hooks').with_args(
        object, before='everything', action_names=object
    )
    flexmock(module.command).should_receive('filter_hooks').with_args(
        object, after='everything', action_names=object, state_names=['fail']
    )
    flexmock(module.command).should_receive('execute_hooks')
    arguments = {'global': flexmock(config_paths=[])}
    expected_logs = (flexmock(),)
    flexmock(module).should_receive('log_error_records').and_return(expected_logs)

    logs = tuple(
        module.collect_configuration_run_summary_logs(
            {}, config_paths=[], arguments=arguments, log_file_path=None
        )
    )

    assert logs == expected_logs


def test_collect_configuration_run_summary_logs_before_hook_error():
    before_everything_hook = {'before': 'everything', 'run': ['echo hi']}
    after_everything_hook = {'after': 'everything', 'run': ['echo hi']}
    command_hooks = (before_everything_hook, after_everything_hook)
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module.command).should_receive('filter_hooks').with_args(
        object, before='everything', action_names=object
    ).and_return([before_everything_hook])
    flexmock(module.command).should_receive('filter_hooks').with_args(
        object, after='everything', action_names=object, state_names=['fail']
    ).and_return([after_everything_hook])
    flexmock(module.command).should_receive('execute_hooks').and_raise(ValueError)
    expected_logs = (flexmock(),)
    flexmock(module).should_receive('log_error_records').and_return(expected_logs)
    arguments = {
        'create': flexmock(),
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
    }

    logs = tuple(
        module.collect_configuration_run_summary_logs(
            {'test.yaml': {'commands': command_hooks}},
            config_paths=['/tmp/test.yaml'],
            arguments=arguments,
            log_file_path=None,
        )
    )

    assert logs == expected_logs


def test_collect_configuration_run_summary_logs_after_hook_error():
    before_everything_hook = {'before': 'everything', 'run': ['echo hi']}
    after_everything_hook = {'after': 'everything', 'run': ['echo hi']}
    command_hooks = (before_everything_hook, after_everything_hook)
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module.command).should_receive('filter_hooks').with_args(
        object, before='everything', action_names=object
    ).and_return([before_everything_hook])
    flexmock(module.command).should_receive('filter_hooks').with_args(
        object, after='everything', action_names=object, state_names=['finish']
    ).and_return([after_everything_hook])
    flexmock(module.command).should_receive('execute_hooks').and_return(None).and_raise(ValueError)
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_configuration').and_return([])
    expected_logs = (flexmock(),)
    flexmock(module).should_receive('log_error_records').and_return(expected_logs)
    arguments = {
        'create': flexmock(),
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
    }

    logs = tuple(
        module.collect_configuration_run_summary_logs(
            {'test.yaml': {'commands': command_hooks}},
            config_paths=['/tmp/test.yaml'],
            arguments=arguments,
            log_file_path=None,
        )
    )

    assert expected_logs[0] in logs


def test_collect_configuration_run_summary_logs_for_list_with_archive_and_repository_error():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository').and_raise(
        ValueError
    )
    expected_logs = (flexmock(),)
    flexmock(module).should_receive('log_error_records').and_return(expected_logs)
    arguments = {
        'list': flexmock(repository='repo', archive='test'),
        'global': flexmock(dry_run=False),
    }

    logs = tuple(
        module.collect_configuration_run_summary_logs(
            {'test.yaml': {}},
            config_paths=['/tmp/test.yaml'],
            arguments=arguments,
            log_file_path=None,
        )
    )

    assert logs == expected_logs


def test_collect_configuration_run_summary_logs_info_for_success_with_list():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module.command).should_receive('filter_hooks').with_args(
        object, before='everything', action_names=object
    )
    flexmock(module.command).should_receive('filter_hooks').with_args(
        object, after='everything', action_names=object, state_names=['finish']
    )
    flexmock(module.command).should_receive('execute_hooks')
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_configuration').and_return([])
    arguments = {
        'list': flexmock(repository='repo', archive=None),
        'global': flexmock(dry_run=False),
    }

    logs = tuple(
        module.collect_configuration_run_summary_logs(
            {'test.yaml': {}},
            config_paths=['/tmp/test.yaml'],
            arguments=arguments,
            log_file_path=None,
        )
    )

    assert {log.levelno for log in logs} == {logging.INFO}


def test_collect_configuration_run_summary_logs_run_configuration_error_logs():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module.command).should_receive('filter_hooks').with_args(
        object, before='everything', action_names=object
    )
    flexmock(module.command).should_receive('filter_hooks').with_args(
        object, after='everything', action_names=object, state_names=['fail']
    )
    flexmock(module.command).should_receive('execute_hooks')
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_configuration').and_return(
        [logging.makeLogRecord(dict(levelno=logging.CRITICAL, levelname='CRITICAL', msg='Error'))]
    )
    flexmock(module).should_receive('log_error_records').and_return([])
    arguments = {'global': flexmock(dry_run=False)}

    logs = tuple(
        module.collect_configuration_run_summary_logs(
            {'test.yaml': {}},
            config_paths=['/tmp/test.yaml'],
            arguments=arguments,
            log_file_path=None,
        )
    )

    assert {log.levelno for log in logs} == {logging.CRITICAL}


def test_collect_configuration_run_summary_logs_run_umount_error():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module.command).should_receive('filter_hooks').with_args(
        object, before='everything', action_names=object
    )
    flexmock(module.command).should_receive('filter_hooks').with_args(
        object, after='everything', action_names=object, state_names=['fail']
    )
    flexmock(module.command).should_receive('execute_hooks')
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_configuration').and_return([])
    flexmock(module.borg_umount).should_receive('unmount_archive').and_raise(OSError)
    flexmock(module).should_receive('log_error_records').and_return(
        [logging.makeLogRecord(dict(levelno=logging.CRITICAL, levelname='CRITICAL', msg='Error'))]
    )
    arguments = {
        'umount': flexmock(mount_point='/mnt'),
        'global': flexmock(dry_run=False),
    }

    logs = tuple(
        module.collect_configuration_run_summary_logs(
            {'test.yaml': {}},
            config_paths=['/tmp/test.yaml'],
            arguments=arguments,
            log_file_path=None,
        )
    )

    assert {log.levelno for log in logs} == {logging.INFO, logging.CRITICAL}


def test_collect_configuration_run_summary_logs_outputs_merged_json_results():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module.command).should_receive('filter_hooks').with_args(
        object, before='everything', action_names=object
    )
    flexmock(module.command).should_receive('filter_hooks').with_args(
        object, after='everything', action_names=object, state_names=['finish']
    )
    flexmock(module.command).should_receive('execute_hooks')
    flexmock(module).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('run_configuration').and_return(['foo', 'bar']).and_return(
        ['baz']
    )
    stdout = flexmock()
    stdout.should_receive('write').with_args('["foo", "bar", "baz"]').once()
    flexmock(module.sys).stdout = stdout
    arguments = {'global': flexmock(dry_run=False)}

    tuple(
        module.collect_configuration_run_summary_logs(
            {'test.yaml': {}, 'test2.yaml': {}},
            config_paths=['/tmp/test.yaml', '/tmp/test2.yaml'],
            arguments=arguments,
            log_file_path=None,
        )
    )


def test_check_and_show_help_on_no_args_shows_help_when_no_args_and_default_actions_false():
    flexmock(module.sys).should_receive('argv').and_return(['borgmatic'])
    flexmock(module).should_receive('parse_arguments').with_args('--help').once()
    flexmock(module.sys).should_receive('exit').with_args(0).once()
    module.check_and_show_help_on_no_args({'test.yaml': {'default_actions': False}})


def test_check_and_show_help_on_no_args_does_not_show_help_when_no_args_and_default_actions_true():
    flexmock(module.sys).should_receive('argv').and_return(['borgmatic'])
    flexmock(module).should_receive('parse_arguments').never()
    flexmock(module.sys).should_receive('exit').never()
    module.check_and_show_help_on_no_args({'test.yaml': {'default_actions': True}})


def test_check_and_show_help_on_no_args_does_not_show_help_when_args_provided():
    flexmock(module.sys).should_receive('argv').and_return(['borgmatic', '--create'])
    flexmock(module).should_receive('parse_arguments').never()
    flexmock(module.sys).should_receive('exit').never()
    module.check_and_show_help_on_no_args({'test.yaml': {'default_actions': False}})


def test_check_and_show_help_on_no_args_with_no_default_actions_in_all_configs():
    flexmock(module.sys).should_receive('argv').and_return(['borgmatic'])

    # Both configs have default_actions set to False, so help should be shown
    configs = {
        'config1.yaml': {'default_actions': False},
        'config2.yaml': {'default_actions': False},
    }

    # Expect help to be shown
    flexmock(module).should_receive('parse_arguments').with_args('--help').once()
    flexmock(module.sys).should_receive('exit').with_args(0).once()

    module.check_and_show_help_on_no_args(configs)


def test_check_and_show_help_on_no_args_with_conflicting_configs():
    flexmock(module.sys).should_receive('argv').and_return(['borgmatic'])

    # Simulate two config files with conflicting 'default_actions' values
    configs = {
        'config1.yaml': {'default_actions': True},
        'config2.yaml': {'default_actions': False},
    }

    # Expect help not to be shown because at least one config enables default actions
    flexmock(module).should_receive('parse_arguments').never()
    flexmock(module.sys).should_receive('exit').never()

    module.check_and_show_help_on_no_args(configs)


def test_get_singular_option_value_with_conflicting_values_exits():
    flexmock(module).should_receive('configure_logging')
    flexmock(module).should_receive('exit_with_help_link').once()

    module.get_singular_option_value(
        configs={
            'test1.yaml': {'foo': 1, 'bar': 'baz'},
            'test2.yaml': {'foo': 2, 'bar': 'baz'},
        },
        option_name='foo',
    )


def test_get_singular_option_value_with_same_value_returns_it():
    flexmock(module).should_receive('configure_logging').never()
    flexmock(module).should_receive('exit_with_help_link').never()

    assert (
        module.get_singular_option_value(
            configs={
                'test1.yaml': {'foo': 1, 'bar': 'baz'},
                'test2.yaml': {'foo': 1, 'bar': 'baz'},
            },
            option_name='foo',
        )
        == 1
    )


def test_get_singular_option_value_with_no_values_returns_none():
    flexmock(module).should_receive('configure_logging').never()
    flexmock(module).should_receive('exit_with_help_link').never()

    assert (
        module.get_singular_option_value(
            configs={
                'test1.yaml': {'bar': 'baz'},
                'test2.yaml': {'bar': 'baz'},
            },
            option_name='foo',
        )
        is None
    )


def test_get_singular_option_value_with_no_config_returns_none():
    flexmock(module).should_receive('configure_logging').never()
    flexmock(module).should_receive('exit_with_help_link').never()

    assert (
        module.get_singular_option_value(
            configs={},
            option_name='foo',
        )
        is None
    )
