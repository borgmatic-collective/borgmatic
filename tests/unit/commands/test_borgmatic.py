import logging
import subprocess
import time

from flexmock import flexmock

import borgmatic.hooks.command
from borgmatic.commands import borgmatic as module


def test_run_configuration_runs_actions_for_each_repository():
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
    flexmock(module.borg_version).should_receive('local_borg_version').and_raise(ValueError)
    flexmock(module.command).should_receive('execute_hook').never()
    flexmock(module.dispatch).should_receive('call_hooks').never()
    flexmock(module).should_receive('run_actions').never()
    config = {'location': {'repositories': ['foo']}}
    arguments = {'global': flexmock(monitoring_verbosity=1, dry_run=False), 'prune': flexmock()}

    list(module.run_configuration('test.yaml', config, arguments))


def test_run_configuration_logs_monitor_start_error():
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


def test_run_repos_ordered():
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


def test_run_actions_does_not_raise_for_rcreate_action():
    flexmock(module.borg_rcreate).should_receive('create_repository')
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'rcreate': flexmock(
            encryption_mode=flexmock(),
            source_repository=flexmock(),
            copy_crypt_key=flexmock(),
            append_only=flexmock(),
            storage_quota=flexmock(),
            make_parent_dirs=flexmock(),
        ),
    }

    list(
        module.run_actions(
            arguments=arguments,
            config_filename='test.yaml',
            location={'repositories': ['repo']},
            storage={},
            retention={},
            consistency={},
            hooks={},
            local_path=None,
            remote_path=None,
            local_borg_version=None,
            repository_path='repo',
        )
    )


def test_run_actions_does_not_raise_for_transfer_action():
    flexmock(module.borg_transfer).should_receive('transfer_archives')
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'transfer': flexmock(),
    }

    list(
        module.run_actions(
            arguments=arguments,
            config_filename='test.yaml',
            location={'repositories': ['repo']},
            storage={},
            retention={},
            consistency={},
            hooks={},
            local_path=None,
            remote_path=None,
            local_borg_version=None,
            repository_path='repo',
        )
    )


def test_run_actions_calls_hooks_for_prune_action():
    flexmock(module.borg_prune).should_receive('prune_archives')
    flexmock(module.command).should_receive('execute_hook').times(
        4
    )  # Before/after extract and before/after actions.
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'prune': flexmock(stats=flexmock(), list_archives=flexmock()),
    }

    list(
        module.run_actions(
            arguments=arguments,
            config_filename='test.yaml',
            location={'repositories': ['repo']},
            storage={},
            retention={},
            consistency={},
            hooks={},
            local_path=None,
            remote_path=None,
            local_borg_version=None,
            repository_path='repo',
        )
    )


def test_run_actions_calls_hooks_for_compact_action():
    flexmock(module.borg_feature).should_receive('available').and_return(True)
    flexmock(module.borg_compact).should_receive('compact_segments')
    flexmock(module.command).should_receive('execute_hook').times(
        4
    )  # Before/after extract and before/after actions.
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'compact': flexmock(progress=flexmock(), cleanup_commits=flexmock(), threshold=flexmock()),
    }

    list(
        module.run_actions(
            arguments=arguments,
            config_filename='test.yaml',
            location={'repositories': ['repo']},
            storage={},
            retention={},
            consistency={},
            hooks={},
            local_path=None,
            remote_path=None,
            local_borg_version=None,
            repository_path='repo',
        )
    )


def test_run_actions_executes_and_calls_hooks_for_create_action():
    flexmock(module.borg_create).should_receive('create_archive')
    flexmock(module.command).should_receive('execute_hook').times(
        4
    )  # Before/after extract and before/after actions.
    flexmock(module.dispatch).should_receive('call_hooks').and_return({})
    flexmock(module.dispatch).should_receive('call_hooks_even_if_unconfigured').and_return({})
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'create': flexmock(
            progress=flexmock(), stats=flexmock(), json=flexmock(), list_files=flexmock()
        ),
    }

    list(
        module.run_actions(
            arguments=arguments,
            config_filename='test.yaml',
            location={'repositories': ['repo']},
            storage={},
            retention={},
            consistency={},
            hooks={},
            local_path=None,
            remote_path=None,
            local_borg_version=None,
            repository_path='repo',
        )
    )


def test_run_actions_calls_hooks_for_check_action():
    flexmock(module.checks).should_receive('repository_enabled_for_checks').and_return(True)
    flexmock(module.borg_check).should_receive('check_archives')
    flexmock(module.command).should_receive('execute_hook').times(
        4
    )  # Before/after extract and before/after actions.
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'check': flexmock(
            progress=flexmock(), repair=flexmock(), only=flexmock(), force=flexmock()
        ),
    }

    list(
        module.run_actions(
            arguments=arguments,
            config_filename='test.yaml',
            location={'repositories': ['repo']},
            storage={},
            retention={},
            consistency={},
            hooks={},
            local_path=None,
            remote_path=None,
            local_borg_version=None,
            repository_path='repo',
        )
    )


def test_run_actions_calls_hooks_for_extract_action():
    flexmock(module.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borg_extract).should_receive('extract_archive')
    flexmock(module.command).should_receive('execute_hook').times(
        4
    )  # Before/after extract and before/after actions.
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'extract': flexmock(
            paths=flexmock(),
            progress=flexmock(),
            destination=flexmock(),
            strip_components=flexmock(),
            archive=flexmock(),
            repository='repo',
        ),
    }

    list(
        module.run_actions(
            arguments=arguments,
            config_filename='test.yaml',
            location={'repositories': ['repo']},
            storage={},
            retention={},
            consistency={},
            hooks={},
            local_path=None,
            remote_path=None,
            local_borg_version=None,
            repository_path='repo',
        )
    )


def test_run_actions_does_not_raise_for_export_tar_action():
    flexmock(module.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borg_export_tar).should_receive('export_tar_archive')
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'export-tar': flexmock(
            repository=flexmock(),
            archive=flexmock(),
            paths=flexmock(),
            destination=flexmock(),
            tar_filter=flexmock(),
            list_files=flexmock(),
            strip_components=flexmock(),
        ),
    }

    list(
        module.run_actions(
            arguments=arguments,
            config_filename='test.yaml',
            location={'repositories': ['repo']},
            storage={},
            retention={},
            consistency={},
            hooks={},
            local_path=None,
            remote_path=None,
            local_borg_version=None,
            repository_path='repo',
        )
    )


def test_run_actions_does_not_raise_for_mount_action():
    flexmock(module.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borg_mount).should_receive('mount_archive')
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'mount': flexmock(
            repository=flexmock(),
            archive=flexmock(),
            mount_point=flexmock(),
            paths=flexmock(),
            foreground=flexmock(),
            options=flexmock(),
        ),
    }

    list(
        module.run_actions(
            arguments=arguments,
            config_filename='test.yaml',
            location={'repositories': ['repo']},
            storage={},
            retention={},
            consistency={},
            hooks={},
            local_path=None,
            remote_path=None,
            local_borg_version=None,
            repository_path='repo',
        )
    )


def test_run_actions_does_not_raise_for_rlist_action():
    flexmock(module.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borg_rlist).should_receive('list_repository')
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'rlist': flexmock(repository=flexmock(), json=flexmock()),
    }

    list(
        module.run_actions(
            arguments=arguments,
            config_filename='test.yaml',
            location={'repositories': ['repo']},
            storage={},
            retention={},
            consistency={},
            hooks={},
            local_path=None,
            remote_path=None,
            local_borg_version=None,
            repository_path='repo',
        )
    )


def test_run_actions_does_not_raise_for_list_action():
    flexmock(module.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borg_rlist).should_receive('resolve_archive_name').and_return(flexmock())
    flexmock(module.borg_list).should_receive('list_archive')
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'list': flexmock(repository=flexmock(), archive=flexmock(), json=flexmock()),
    }

    list(
        module.run_actions(
            arguments=arguments,
            config_filename='test.yaml',
            location={'repositories': ['repo']},
            storage={},
            retention={},
            consistency={},
            hooks={},
            local_path=None,
            remote_path=None,
            local_borg_version=None,
            repository_path='repo',
        )
    )


def test_run_actions_does_not_raise_for_rinfo_action():
    flexmock(module.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borg_rinfo).should_receive('display_repository_info')
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'rinfo': flexmock(repository=flexmock(), json=flexmock()),
    }

    list(
        module.run_actions(
            arguments=arguments,
            config_filename='test.yaml',
            location={'repositories': ['repo']},
            storage={},
            retention={},
            consistency={},
            hooks={},
            local_path=None,
            remote_path=None,
            local_borg_version=None,
            repository_path='repo',
        )
    )


def test_run_actions_does_not_raise_for_info_action():
    flexmock(module.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borg_rlist).should_receive('resolve_archive_name').and_return(flexmock())
    flexmock(module.borg_info).should_receive('display_archives_info')
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'info': flexmock(repository=flexmock(), archive=flexmock(), json=flexmock()),
    }

    list(
        module.run_actions(
            arguments=arguments,
            config_filename='test.yaml',
            location={'repositories': ['repo']},
            storage={},
            retention={},
            consistency={},
            hooks={},
            local_path=None,
            remote_path=None,
            local_borg_version=None,
            repository_path='repo',
        )
    )


def test_run_actions_does_not_raise_for_break_lock_action():
    flexmock(module.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borg_break_lock).should_receive('break_lock')
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'break-lock': flexmock(repository=flexmock()),
    }

    list(
        module.run_actions(
            arguments=arguments,
            config_filename='test.yaml',
            location={'repositories': ['repo']},
            storage={},
            retention={},
            consistency={},
            hooks={},
            local_path=None,
            remote_path=None,
            local_borg_version=None,
            repository_path='repo',
        )
    )


def test_run_actions_does_not_raise_for_borg_action():
    flexmock(module.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borg_rlist).should_receive('resolve_archive_name').and_return(flexmock())
    flexmock(module.borg_borg).should_receive('run_arbitrary_borg')
    arguments = {
        'global': flexmock(monitoring_verbosity=1, dry_run=False),
        'borg': flexmock(repository=flexmock(), archive=flexmock(), options=flexmock()),
    }

    list(
        module.run_actions(
            arguments=arguments,
            config_filename='test.yaml',
            location={'repositories': ['repo']},
            storage={},
            retention={},
            consistency={},
            hooks={},
            local_path=None,
            remote_path=None,
            local_borg_version=None,
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
