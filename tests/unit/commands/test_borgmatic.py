import logging
import subprocess
import time

from flexmock import flexmock

import borgmatic.hooks.command
from borgmatic.commands import borgmatic as module


def test_run_configuration_runs_actions_for_each_repository():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    expected_results = [flexmock(), flexmock()]
    flexmock(module).should_receive('run_actions').and_return(expected_results[:1]).and_return(
        expected_results[1:]
    )
    config = {'location': {'repositories': ['foo', 'bar']}}
    arguments = {'global': flexmock(monitoring_verbosity=1)}

    results = list(module.run_configuration('test.yaml', config, arguments))

    assert results == expected_results


def test_run_configuration_with_invalid_borg_version_errors():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module.borg_version).should_receive('local_borg_version').and_raise(ValueError)
    flexmock(module.command).should_receive('execute_hook').never()
    flexmock(module.dispatch).should_receive('call_hooks').never()
    flexmock(module).should_receive('run_actions').never()
    config = {'location': {'repositories': ['foo']}}
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False), 'prune': flexmock()}

    list(module.run_configuration('test.yaml', config, arguments))


def test_run_configuration_logs_monitor_start_error():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module.dispatch).should_receive('call_hooks').and_raise(OSError).and_return(
        None
    ).and_return(None)
    expected_results = [flexmock()]
    flexmock(module).should_receive('log_error_records').and_return(expected_results)
    flexmock(module).should_receive('run_actions').never()
    config = {'location': {'repositories': ['foo']}}
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False), 'create': flexmock()}

    results = list(module.run_configuration('test.yaml', config, arguments))

    assert results == expected_results


def test_run_configuration_bails_for_monitor_start_soft_failure():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    error = subprocess.CalledProcessError(borgmatic.hooks.command.SOFT_FAIL_EXIT_CODE, 'try again')
    flexmock(module.dispatch).should_receive('call_hooks').and_raise(error)
    flexmock(module).should_receive('log_error_records').never()
    flexmock(module).should_receive('run_actions').never()
    config = {'location': {'repositories': ['foo']}}
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False), 'create': flexmock()}

    results = list(module.run_configuration('test.yaml', config, arguments))

    assert results == []


def test_run_configuration_logs_actions_error():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module.command).should_receive('execute_hook')
    flexmock(module.dispatch).should_receive('call_hooks')
    expected_results = [flexmock()]
    flexmock(module).should_receive('log_error_records').and_return(expected_results)
    flexmock(module).should_receive('run_actions').and_raise(OSError)
    config = {'location': {'repositories': ['foo']}}
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False)}

    results = list(module.run_configuration('test.yaml', config, arguments))

    assert results == expected_results


def test_run_configuration_bails_for_actions_soft_failure():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module.dispatch).should_receive('call_hooks')
    error = subprocess.CalledProcessError(borgmatic.hooks.command.SOFT_FAIL_EXIT_CODE, 'try again')
    flexmock(module).should_receive('run_actions').and_raise(error)
    flexmock(module).should_receive('log_error_records').never()
    flexmock(module.command).should_receive('considered_soft_failure').and_return(True)
    config = {'location': {'repositories': ['foo']}}
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False), 'create': flexmock()}

    results = list(module.run_configuration('test.yaml', config, arguments))

    assert results == []


def test_run_configuration_logs_monitor_finish_error():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module.dispatch).should_receive('call_hooks').and_return(None).and_return(
        None
    ).and_raise(OSError)
    expected_results = [flexmock()]
    flexmock(module).should_receive('log_error_records').and_return(expected_results)
    flexmock(module).should_receive('run_actions').and_return([])
    config = {'location': {'repositories': ['foo']}}
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False), 'create': flexmock()}

    results = list(module.run_configuration('test.yaml', config, arguments))

    assert results == expected_results


def test_run_configuration_bails_for_monitor_finish_soft_failure():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    error = subprocess.CalledProcessError(borgmatic.hooks.command.SOFT_FAIL_EXIT_CODE, 'try again')
    flexmock(module.dispatch).should_receive('call_hooks').and_return(None).and_return(
        None
    ).and_raise(error)
    flexmock(module).should_receive('log_error_records').never()
    flexmock(module).should_receive('run_actions').and_return([])
    flexmock(module.command).should_receive('considered_soft_failure').and_return(True)
    config = {'location': {'repositories': ['foo']}}
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False), 'create': flexmock()}

    results = list(module.run_configuration('test.yaml', config, arguments))

    assert results == []


def test_run_configuration_logs_on_error_hook_error():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module.command).should_receive('execute_hook').and_raise(OSError)
    expected_results = [flexmock(), flexmock()]
    flexmock(module).should_receive('log_error_records').and_return(
        expected_results[:1]
    ).and_return(expected_results[1:])
    flexmock(module).should_receive('run_actions').and_raise(OSError)
    config = {'location': {'repositories': ['foo']}}
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False), 'create': flexmock()}

    results = list(module.run_configuration('test.yaml', config, arguments))

    assert results == expected_results


def test_run_configuration_bails_for_on_error_hook_soft_failure():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    error = subprocess.CalledProcessError(borgmatic.hooks.command.SOFT_FAIL_EXIT_CODE, 'try again')
    flexmock(module.command).should_receive('execute_hook').and_raise(error)
    expected_results = [flexmock()]
    flexmock(module).should_receive('log_error_records').and_return(expected_results)
    flexmock(module).should_receive('run_actions').and_raise(OSError)
    config = {'location': {'repositories': ['foo']}}
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False), 'create': flexmock()}

    results = list(module.run_configuration('test.yaml', config, arguments))

    assert results == expected_results


def test_run_configuration_retries_soft_error():
    # Run action first fails, second passes
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module.command).should_receive('execute_hook')
    flexmock(module).should_receive('run_actions').and_raise(OSError).and_return([])
    flexmock(module).should_receive('log_error_records').and_return([flexmock()]).once()
    config = {'location': {'repositories': ['foo']}, 'storage': {'retries': 1}}
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False), 'create': flexmock()}
    results = list(module.run_configuration('test.yaml', config, arguments))
    assert results == []


def test_run_configuration_retries_hard_error():
    # Run action fails twice
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module.command).should_receive('execute_hook')
    flexmock(module).should_receive('run_actions').and_raise(OSError).times(2)
    flexmock(module).should_receive('log_error_records').with_args(
        'foo: Error running actions for repository',
        OSError,
        levelno=logging.WARNING,
        log_command_error_output=True,
    ).and_return([flexmock()])
    error_logs = [flexmock()]
    flexmock(module).should_receive('log_error_records').with_args(
        'foo: Error running actions for repository', OSError,
    ).and_return(error_logs)
    config = {'location': {'repositories': ['foo']}, 'storage': {'retries': 1}}
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False), 'create': flexmock()}
    results = list(module.run_configuration('test.yaml', config, arguments))
    assert results == error_logs


def test_run_configuration_repos_ordered():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module.command).should_receive('execute_hook')
    flexmock(module).should_receive('run_actions').and_raise(OSError).times(2)
    expected_results = [flexmock(), flexmock()]
    flexmock(module).should_receive('log_error_records').with_args(
        'foo: Error running actions for repository', OSError
    ).and_return(expected_results[:1]).ordered()
    flexmock(module).should_receive('log_error_records').with_args(
        'bar: Error running actions for repository', OSError
    ).and_return(expected_results[1:]).ordered()
    config = {'location': {'repositories': ['foo', 'bar']}}
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False), 'create': flexmock()}
    results = list(module.run_configuration('test.yaml', config, arguments))
    assert results == expected_results


def test_run_configuration_retries_round_robbin():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module.command).should_receive('execute_hook')
    flexmock(module).should_receive('run_actions').and_raise(OSError).times(4)
    flexmock(module).should_receive('log_error_records').with_args(
        'foo: Error running actions for repository',
        OSError,
        levelno=logging.WARNING,
        log_command_error_output=True,
    ).and_return([flexmock()]).ordered()
    flexmock(module).should_receive('log_error_records').with_args(
        'bar: Error running actions for repository',
        OSError,
        levelno=logging.WARNING,
        log_command_error_output=True,
    ).and_return([flexmock()]).ordered()
    foo_error_logs = [flexmock()]
    flexmock(module).should_receive('log_error_records').with_args(
        'foo: Error running actions for repository', OSError
    ).and_return(foo_error_logs).ordered()
    bar_error_logs = [flexmock()]
    flexmock(module).should_receive('log_error_records').with_args(
        'bar: Error running actions for repository', OSError
    ).and_return(bar_error_logs).ordered()
    config = {'location': {'repositories': ['foo', 'bar']}, 'storage': {'retries': 1}}
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False), 'create': flexmock()}
    results = list(module.run_configuration('test.yaml', config, arguments))
    assert results == foo_error_logs + bar_error_logs


def test_run_configuration_retries_one_passes():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module.command).should_receive('execute_hook')
    flexmock(module).should_receive('run_actions').and_raise(OSError).and_raise(OSError).and_return(
        []
    ).and_raise(OSError).times(4)
    flexmock(module).should_receive('log_error_records').with_args(
        'foo: Error running actions for repository',
        OSError,
        levelno=logging.WARNING,
        log_command_error_output=True,
    ).and_return([flexmock()]).ordered()
    flexmock(module).should_receive('log_error_records').with_args(
        'bar: Error running actions for repository',
        OSError,
        levelno=logging.WARNING,
        log_command_error_output=True,
    ).and_return(flexmock()).ordered()
    error_logs = [flexmock()]
    flexmock(module).should_receive('log_error_records').with_args(
        'bar: Error running actions for repository', OSError
    ).and_return(error_logs).ordered()
    config = {'location': {'repositories': ['foo', 'bar']}, 'storage': {'retries': 1}}
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False), 'create': flexmock()}
    results = list(module.run_configuration('test.yaml', config, arguments))
    assert results == error_logs


def test_run_configuration_retry_wait():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module.command).should_receive('execute_hook')
    flexmock(module).should_receive('run_actions').and_raise(OSError).times(4)
    flexmock(module).should_receive('log_error_records').with_args(
        'foo: Error running actions for repository',
        OSError,
        levelno=logging.WARNING,
        log_command_error_output=True,
    ).and_return([flexmock()]).ordered()

    flexmock(time).should_receive('sleep').with_args(10).and_return().ordered()
    flexmock(module).should_receive('log_error_records').with_args(
        'foo: Error running actions for repository',
        OSError,
        levelno=logging.WARNING,
        log_command_error_output=True,
    ).and_return([flexmock()]).ordered()

    flexmock(time).should_receive('sleep').with_args(20).and_return().ordered()
    flexmock(module).should_receive('log_error_records').with_args(
        'foo: Error running actions for repository',
        OSError,
        levelno=logging.WARNING,
        log_command_error_output=True,
    ).and_return([flexmock()]).ordered()

    flexmock(time).should_receive('sleep').with_args(30).and_return().ordered()
    error_logs = [flexmock()]
    flexmock(module).should_receive('log_error_records').with_args(
        'foo: Error running actions for repository', OSError
    ).and_return(error_logs).ordered()
    config = {'location': {'repositories': ['foo']}, 'storage': {'retries': 3, 'retry_wait': 10}}
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False), 'create': flexmock()}
    results = list(module.run_configuration('test.yaml', config, arguments))
    assert results == error_logs


def test_run_configuration_retries_timeout_multiple_repos():
    flexmock(module).should_receive('verbosity_to_log_level').and_return(logging.INFO)
    flexmock(module.borg_version).should_receive('local_borg_version').and_return(flexmock())
    flexmock(module.command).should_receive('execute_hook')
    flexmock(module).should_receive('run_actions').and_raise(OSError).and_raise(OSError).and_return(
        []
    ).and_raise(OSError).times(4)
    flexmock(module).should_receive('log_error_records').with_args(
        'foo: Error running actions for repository',
        OSError,
        levelno=logging.WARNING,
        log_command_error_output=True,
    ).and_return([flexmock()]).ordered()
    flexmock(module).should_receive('log_error_records').with_args(
        'bar: Error running actions for repository',
        OSError,
        levelno=logging.WARNING,
        log_command_error_output=True,
    ).and_return([flexmock()]).ordered()

    # Sleep before retrying foo (and passing)
    flexmock(time).should_receive('sleep').with_args(10).and_return().ordered()

    # Sleep before retrying bar (and failing)
    flexmock(time).should_receive('sleep').with_args(10).and_return().ordered()
    error_logs = [flexmock()]
    flexmock(module).should_receive('log_error_records').with_args(
        'bar: Error running actions for repository', OSError
    ).and_return(error_logs).ordered()
    config = {
        'location': {'repositories': ['foo', 'bar']},
        'storage': {'retries': 1, 'retry_wait': 10},
    }
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False), 'create': flexmock()}
    results = list(module.run_configuration('test.yaml', config, arguments))
    assert results == error_logs


def test_run_actions_runs_rcreate():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.command).should_receive('execute_hook')
    flexmock(borgmatic.actions.rcreate).should_receive('run_rcreate').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'rcreate': flexmock()},
            config_filename=flexmock(),
            location={'repositories': []},
            storage=flexmock(),
            retention=flexmock(),
            consistency=flexmock(),
            hooks={},
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository_path='repo',
        )
    )


def test_run_actions_runs_transfer():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.command).should_receive('execute_hook')
    flexmock(borgmatic.actions.transfer).should_receive('run_transfer').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'transfer': flexmock()},
            config_filename=flexmock(),
            location={'repositories': []},
            storage=flexmock(),
            retention=flexmock(),
            consistency=flexmock(),
            hooks={},
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository_path='repo',
        )
    )


def test_run_actions_runs_prune():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.command).should_receive('execute_hook')
    flexmock(borgmatic.actions.prune).should_receive('run_prune').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'prune': flexmock()},
            config_filename=flexmock(),
            location={'repositories': []},
            storage=flexmock(),
            retention=flexmock(),
            consistency=flexmock(),
            hooks={},
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository_path='repo',
        )
    )


def test_run_actions_runs_compact():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.command).should_receive('execute_hook')
    flexmock(borgmatic.actions.compact).should_receive('run_compact').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'compact': flexmock()},
            config_filename=flexmock(),
            location={'repositories': []},
            storage=flexmock(),
            retention=flexmock(),
            consistency=flexmock(),
            hooks={},
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository_path='repo',
        )
    )


def test_run_actions_runs_create():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.command).should_receive('execute_hook')
    expected = flexmock()
    flexmock(borgmatic.actions.create).should_receive('run_create').and_yield(expected).once()

    result = tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'create': flexmock()},
            config_filename=flexmock(),
            location={'repositories': []},
            storage=flexmock(),
            retention=flexmock(),
            consistency=flexmock(),
            hooks={},
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository_path='repo',
        )
    )
    assert result == (expected,)


def test_run_actions_runs_check_when_repository_enabled_for_checks():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.command).should_receive('execute_hook')
    flexmock(module.checks).should_receive('repository_enabled_for_checks').and_return(True)
    flexmock(borgmatic.actions.check).should_receive('run_check').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'check': flexmock()},
            config_filename=flexmock(),
            location={'repositories': []},
            storage=flexmock(),
            retention=flexmock(),
            consistency=flexmock(),
            hooks={},
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository_path='repo',
        )
    )


def test_run_actions_skips_check_when_repository_not_enabled_for_checks():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.command).should_receive('execute_hook')
    flexmock(module.checks).should_receive('repository_enabled_for_checks').and_return(False)
    flexmock(borgmatic.actions.check).should_receive('run_check').never()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'check': flexmock()},
            config_filename=flexmock(),
            location={'repositories': []},
            storage=flexmock(),
            retention=flexmock(),
            consistency=flexmock(),
            hooks={},
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository_path='repo',
        )
    )


def test_run_actions_runs_extract():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.command).should_receive('execute_hook')
    flexmock(borgmatic.actions.extract).should_receive('run_extract').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'extract': flexmock()},
            config_filename=flexmock(),
            location={'repositories': []},
            storage=flexmock(),
            retention=flexmock(),
            consistency=flexmock(),
            hooks={},
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository_path='repo',
        )
    )


def test_run_actions_runs_export_tar():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.command).should_receive('execute_hook')
    flexmock(borgmatic.actions.export_tar).should_receive('run_export_tar').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'export-tar': flexmock()},
            config_filename=flexmock(),
            location={'repositories': []},
            storage=flexmock(),
            retention=flexmock(),
            consistency=flexmock(),
            hooks={},
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository_path='repo',
        )
    )


def test_run_actions_runs_mount():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.command).should_receive('execute_hook')
    flexmock(borgmatic.actions.mount).should_receive('run_mount').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'mount': flexmock()},
            config_filename=flexmock(),
            location={'repositories': []},
            storage=flexmock(),
            retention=flexmock(),
            consistency=flexmock(),
            hooks={},
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository_path='repo',
        )
    )


def test_run_actions_runs_restore():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.command).should_receive('execute_hook')
    flexmock(borgmatic.actions.restore).should_receive('run_restore').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'restore': flexmock()},
            config_filename=flexmock(),
            location={'repositories': []},
            storage=flexmock(),
            retention=flexmock(),
            consistency=flexmock(),
            hooks={},
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository_path='repo',
        )
    )


def test_run_actions_runs_rlist():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.command).should_receive('execute_hook')
    expected = flexmock()
    flexmock(borgmatic.actions.rlist).should_receive('run_rlist').and_yield(expected).once()

    result = tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'rlist': flexmock()},
            config_filename=flexmock(),
            location={'repositories': []},
            storage=flexmock(),
            retention=flexmock(),
            consistency=flexmock(),
            hooks={},
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository_path='repo',
        )
    )
    assert result == (expected,)


def test_run_actions_runs_list():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.command).should_receive('execute_hook')
    expected = flexmock()
    flexmock(borgmatic.actions.list).should_receive('run_list').and_yield(expected).once()

    result = tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'list': flexmock()},
            config_filename=flexmock(),
            location={'repositories': []},
            storage=flexmock(),
            retention=flexmock(),
            consistency=flexmock(),
            hooks={},
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository_path='repo',
        )
    )
    assert result == (expected,)


def test_run_actions_runs_rinfo():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.command).should_receive('execute_hook')
    expected = flexmock()
    flexmock(borgmatic.actions.rinfo).should_receive('run_rinfo').and_yield(expected).once()

    result = tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'rinfo': flexmock()},
            config_filename=flexmock(),
            location={'repositories': []},
            storage=flexmock(),
            retention=flexmock(),
            consistency=flexmock(),
            hooks={},
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository_path='repo',
        )
    )
    assert result == (expected,)


def test_run_actions_runs_info():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.command).should_receive('execute_hook')
    expected = flexmock()
    flexmock(borgmatic.actions.info).should_receive('run_info').and_yield(expected).once()

    result = tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'info': flexmock()},
            config_filename=flexmock(),
            location={'repositories': []},
            storage=flexmock(),
            retention=flexmock(),
            consistency=flexmock(),
            hooks={},
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository_path='repo',
        )
    )
    assert result == (expected,)


def test_run_actions_runs_break_lock():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.command).should_receive('execute_hook')
    flexmock(borgmatic.actions.break_lock).should_receive('run_break_lock').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'break-lock': flexmock()},
            config_filename=flexmock(),
            location={'repositories': []},
            storage=flexmock(),
            retention=flexmock(),
            consistency=flexmock(),
            hooks={},
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository_path='repo',
        )
    )


def test_run_actions_runs_borg():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.command).should_receive('execute_hook')
    flexmock(borgmatic.actions.borg).should_receive('run_borg').once()

    tuple(
        module.run_actions(
            arguments={'global': flexmock(dry_run=False), 'borg': flexmock()},
            config_filename=flexmock(),
            location={'repositories': []},
            storage=flexmock(),
            retention=flexmock(),
            consistency=flexmock(),
            hooks={},
            local_path=flexmock(),
            remote_path=flexmock(),
            local_borg_version=flexmock(),
            repository_path='repo',
        )
    )


def test_load_configurations_collects_parsed_configurations_and_logs():
    configuration = flexmock()
    other_configuration = flexmock()
    test_expected_logs = [flexmock(), flexmock()]
    other_expected_logs = [flexmock(), flexmock()]
    flexmock(module.validate).should_receive('parse_configuration').and_return(
        configuration, test_expected_logs
    ).and_return(other_configuration, other_expected_logs)

    configs, logs = tuple(module.load_configurations(('test.yaml', 'other.yaml')))

    assert configs == {'test.yaml': configuration, 'other.yaml': other_configuration}
    assert logs == test_expected_logs + other_expected_logs


def test_load_configurations_logs_warning_for_permission_error():
    flexmock(module.validate).should_receive('parse_configuration').and_raise(PermissionError)

    configs, logs = tuple(module.load_configurations(('test.yaml',)))

    assert configs == {}
    assert {log.levelno for log in logs} == {logging.WARNING}


def test_load_configurations_logs_critical_for_parse_error():
    flexmock(module.validate).should_receive('parse_configuration').and_raise(ValueError)

    configs, logs = tuple(module.load_configurations(('test.yaml',)))

    assert configs == {}
    assert {log.levelno for log in logs} == {logging.CRITICAL}


def test_log_record_does_not_raise():
    module.log_record(levelno=1, foo='bar', baz='quux')


def test_log_record_with_suppress_does_not_raise():
    module.log_record(levelno=1, foo='bar', baz='quux', suppress_log=True)


def test_log_error_records_generates_output_logs_for_message_only():
    flexmock(module).should_receive('log_record').replace_with(dict)

    logs = tuple(module.log_error_records('Error'))

    assert {log['levelno'] for log in logs} == {logging.CRITICAL}


def test_log_error_records_generates_output_logs_for_called_process_error():
    flexmock(module).should_receive('log_record').replace_with(dict)
    flexmock(module.logger).should_receive('getEffectiveLevel').and_return(logging.WARNING)

    logs = tuple(
        module.log_error_records('Error', subprocess.CalledProcessError(1, 'ls', 'error output'))
    )

    assert {log['levelno'] for log in logs} == {logging.CRITICAL}
    assert any(log for log in logs if 'error output' in str(log))


def test_log_error_records_generates_logs_for_value_error():
    flexmock(module).should_receive('log_record').replace_with(dict)

    logs = tuple(module.log_error_records('Error', ValueError()))

    assert {log['levelno'] for log in logs} == {logging.CRITICAL}


def test_log_error_records_generates_logs_for_os_error():
    flexmock(module).should_receive('log_record').replace_with(dict)

    logs = tuple(module.log_error_records('Error', OSError()))

    assert {log['levelno'] for log in logs} == {logging.CRITICAL}


def test_log_error_records_generates_nothing_for_other_error():
    flexmock(module).should_receive('log_record').replace_with(dict)

    logs = tuple(module.log_error_records('Error', KeyError()))

    assert logs == ()


def test_get_local_path_uses_configuration_value():
    assert module.get_local_path({'test.yaml': {'location': {'local_path': 'borg1'}}}) == 'borg1'


def test_get_local_path_without_location_defaults_to_borg():
    assert module.get_local_path({'test.yaml': {}}) == 'borg'


def test_get_local_path_without_local_path_defaults_to_borg():
    assert module.get_local_path({'test.yaml': {'location': {}}}) == 'borg'


def test_collect_configuration_run_summary_logs_info_for_success():
    flexmock(module.command).should_receive('execute_hook').never()
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module).should_receive('run_configuration').and_return([])
    arguments = {}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert {log.levelno for log in logs} == {logging.INFO}


def test_collect_configuration_run_summary_executes_hooks_for_create():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module).should_receive('run_configuration').and_return([])
    arguments = {'create': flexmock(), 'global': flexmock(monitoring_verbosity=1, dry_run=False)}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert {log.levelno for log in logs} == {logging.INFO}


def test_collect_configuration_run_summary_logs_info_for_success_with_extract():
    flexmock(module.validate).should_receive('guard_single_repository_selected')
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module).should_receive('run_configuration').and_return([])
    arguments = {'extract': flexmock(repository='repo')}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
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
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert logs == expected_logs


def test_collect_configuration_run_summary_logs_info_for_success_with_mount():
    flexmock(module.validate).should_receive('guard_single_repository_selected')
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module).should_receive('run_configuration').and_return([])
    arguments = {'mount': flexmock(repository='repo')}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert {log.levelno for log in logs} == {logging.INFO}


def test_collect_configuration_run_summary_logs_mount_with_repository_error():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository').and_raise(
        ValueError
    )
    expected_logs = (flexmock(),)
    flexmock(module).should_receive('log_error_records').and_return(expected_logs)
    arguments = {'mount': flexmock(repository='repo')}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert logs == expected_logs


def test_collect_configuration_run_summary_logs_missing_configs_error():
    arguments = {'global': flexmock(config_paths=[])}
    expected_logs = (flexmock(),)
    flexmock(module).should_receive('log_error_records').and_return(expected_logs)

    logs = tuple(module.collect_configuration_run_summary_logs({}, arguments=arguments))

    assert logs == expected_logs


def test_collect_configuration_run_summary_logs_pre_hook_error():
    flexmock(module.command).should_receive('execute_hook').and_raise(ValueError)
    expected_logs = (flexmock(),)
    flexmock(module).should_receive('log_error_records').and_return(expected_logs)
    arguments = {'create': flexmock(), 'global': flexmock(monitoring_verbosity=1, dry_run=False)}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert logs == expected_logs


def test_collect_configuration_run_summary_logs_post_hook_error():
    flexmock(module.command).should_receive('execute_hook').and_return(None).and_raise(ValueError)
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module).should_receive('run_configuration').and_return([])
    expected_logs = (flexmock(),)
    flexmock(module).should_receive('log_error_records').and_return(expected_logs)
    arguments = {'create': flexmock(), 'global': flexmock(monitoring_verbosity=1, dry_run=False)}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert expected_logs[0] in logs


def test_collect_configuration_run_summary_logs_for_list_with_archive_and_repository_error():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository').and_raise(
        ValueError
    )
    expected_logs = (flexmock(),)
    flexmock(module).should_receive('log_error_records').and_return(expected_logs)
    arguments = {'list': flexmock(repository='repo', archive='test')}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert logs == expected_logs


def test_collect_configuration_run_summary_logs_info_for_success_with_list():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module).should_receive('run_configuration').and_return([])
    arguments = {'list': flexmock(repository='repo', archive=None)}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert {log.levelno for log in logs} == {logging.INFO}


def test_collect_configuration_run_summary_logs_run_configuration_error():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module).should_receive('run_configuration').and_return(
        [logging.makeLogRecord(dict(levelno=logging.CRITICAL, levelname='CRITICAL', msg='Error'))]
    )
    flexmock(module).should_receive('log_error_records').and_return([])
    arguments = {}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert {log.levelno for log in logs} == {logging.CRITICAL}


def test_collect_configuration_run_summary_logs_run_umount_error():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module).should_receive('run_configuration').and_return([])
    flexmock(module.borg_umount).should_receive('unmount_archive').and_raise(OSError)
    flexmock(module).should_receive('log_error_records').and_return(
        [logging.makeLogRecord(dict(levelno=logging.CRITICAL, levelname='CRITICAL', msg='Error'))]
    )
    arguments = {'umount': flexmock(mount_point='/mnt')}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert {log.levelno for log in logs} == {logging.INFO, logging.CRITICAL}


def test_collect_configuration_run_summary_logs_outputs_merged_json_results():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module).should_receive('run_configuration').and_return(['foo', 'bar']).and_return(
        ['baz']
    )
    stdout = flexmock()
    stdout.should_receive('write').with_args('["foo", "bar", "baz"]').once()
    flexmock(module.sys).stdout = stdout
    arguments = {}

    tuple(
        module.collect_configuration_run_summary_logs(
            {'test.yaml': {}, 'test2.yaml': {}}, arguments=arguments
        )
    )
