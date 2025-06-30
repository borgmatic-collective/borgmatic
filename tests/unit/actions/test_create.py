import json
import os

import pytest
from flexmock import flexmock

from borgmatic.actions import create as module


def test_run_create_executes_and_calls_hooks_for_configured_repository():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').never()
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.create).should_receive('create_archive').once()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return({})
    flexmock(module.borgmatic.hooks.dispatch).should_receive(
        'call_hooks_even_if_unconfigured'
    ).and_return({})
    flexmock(module.borgmatic.actions.pattern).should_receive('collect_patterns').and_return(())
    flexmock(module.borgmatic.actions.pattern).should_receive('process_patterns').and_return([])
    flexmock(os.path).should_receive('join').and_return('/run/borgmatic/bootstrap')
    create_arguments = flexmock(
        repository=None,
        progress=flexmock(),
        statistics=flexmock(),
        json=False,
        comment=None,
        list_details=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    list(
        module.run_create(
            config_filename='test.yaml',
            repository={'path': 'repo'},
            config={},
            config_paths=['/tmp/test.yaml'],
            local_borg_version=None,
            create_arguments=create_arguments,
            global_arguments=global_arguments,
            dry_run_label='',
            local_path=None,
            remote_path=None,
        )
    )


def test_run_create_runs_with_selected_repository():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive(
        'repositories_match'
    ).once().and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.create).should_receive('create_archive').once()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return({})
    flexmock(module.borgmatic.hooks.dispatch).should_receive(
        'call_hooks_even_if_unconfigured'
    ).and_return({})
    flexmock(module.borgmatic.actions.pattern).should_receive('collect_patterns').and_return(())
    flexmock(module.borgmatic.actions.pattern).should_receive('process_patterns').and_return([])
    flexmock(os.path).should_receive('join').and_return('/run/borgmatic/bootstrap')
    create_arguments = flexmock(
        repository=flexmock(),
        progress=flexmock(),
        statistics=flexmock(),
        json=False,
        comment=None,
        list_details=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    list(
        module.run_create(
            config_filename='test.yaml',
            repository={'path': 'repo'},
            config={},
            config_paths=['/tmp/test.yaml'],
            local_borg_version=None,
            create_arguments=create_arguments,
            global_arguments=global_arguments,
            dry_run_label='',
            local_path=None,
            remote_path=None,
        )
    )


def test_run_create_bails_if_repository_does_not_match():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive(
        'repositories_match'
    ).once().and_return(False)
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').never()
    flexmock(module.borgmatic.borg.create).should_receive('create_archive').never()
    create_arguments = flexmock(
        repository=flexmock(),
        progress=flexmock(),
        statistics=flexmock(),
        json=False,
        comment=None,
        list_details=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    list(
        module.run_create(
            config_filename='test.yaml',
            repository='repo',
            config={},
            config_paths=['/tmp/test.yaml'],
            local_borg_version=None,
            create_arguments=create_arguments,
            global_arguments=global_arguments,
            dry_run_label='',
            local_path=None,
            remote_path=None,
        )
    )


def test_run_create_with_both_list_and_json_errors():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive(
        'repositories_match'
    ).once().and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').never()
    flexmock(module.borgmatic.borg.create).should_receive('create_archive').never()
    create_arguments = flexmock(
        repository=flexmock(),
        progress=flexmock(),
        statistics=flexmock(),
        json=True,
        comment=None,
        list_details=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    with pytest.raises(ValueError):
        list(
            module.run_create(
                config_filename='test.yaml',
                repository={'path': 'repo'},
                config={'list_details': True},
                config_paths=['/tmp/test.yaml'],
                local_borg_version=None,
                create_arguments=create_arguments,
                global_arguments=global_arguments,
                dry_run_label='',
                local_path=None,
                remote_path=None,
            )
        )


def test_run_create_with_both_list_and_progress_errors():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive(
        'repositories_match'
    ).once().and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').never()
    flexmock(module.borgmatic.borg.create).should_receive('create_archive').never()
    create_arguments = flexmock(
        repository=flexmock(),
        progress=flexmock(),
        statistics=flexmock(),
        json=False,
        comment=None,
        list_details=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    with pytest.raises(ValueError):
        list(
            module.run_create(
                config_filename='test.yaml',
                repository={'path': 'repo'},
                config={'list_details': True, 'progress': True},
                config_paths=['/tmp/test.yaml'],
                local_borg_version=None,
                create_arguments=create_arguments,
                global_arguments=global_arguments,
                dry_run_label='',
                local_path=None,
                remote_path=None,
            )
        )


def test_run_create_produces_json():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive(
        'repositories_match'
    ).once().and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.create).should_receive('create_archive').once().and_return(
        flexmock()
    )
    parsed_json = flexmock()
    flexmock(module.borgmatic.actions.json).should_receive('parse_json').and_return(parsed_json)
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return({})
    flexmock(module.borgmatic.hooks.dispatch).should_receive(
        'call_hooks_even_if_unconfigured'
    ).and_return({})
    flexmock(module.borgmatic.actions.pattern).should_receive('collect_patterns').and_return(())
    flexmock(module.borgmatic.actions.pattern).should_receive('process_patterns').and_return([])
    flexmock(os.path).should_receive('join').and_return('/run/borgmatic/bootstrap')
    create_arguments = flexmock(
        repository=flexmock(),
        progress=flexmock(),
        statistics=flexmock(),
        json=True,
        comment=None,
        list_details=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    assert list(
        module.run_create(
            config_filename='test.yaml',
            repository={'path': 'repo'},
            config={},
            config_paths=['/tmp/test.yaml'],
            local_borg_version=None,
            create_arguments=create_arguments,
            global_arguments=global_arguments,
            dry_run_label='',
            local_path=None,
            remote_path=None,
        )
    ) == [parsed_json]


def test_run_create_with_active_dumps_roundtrips_via_checkpoint_archive():
    mock_dump_process = flexmock()
    mock_dump_process.should_receive('poll').and_return(None).and_return(0)

    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').never()
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.create).should_receive('create_archive').once()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return(
        {'dump': mock_dump_process}
    )
    flexmock(module.borgmatic.hooks.dispatch).should_receive(
        'call_hooks_even_if_unconfigured'
    ).and_return({})
    flexmock(module.borgmatic.actions.pattern).should_receive('collect_patterns').and_return(())
    flexmock(module.borgmatic.actions.pattern).should_receive('process_patterns').and_return([])
    flexmock(os.path).should_receive('join').and_return('/run/borgmatic/bootstrap')
    flexmock(module.borgmatic.borg.repo_list).should_receive('get_latest_archive').and_return(
        {'id': 'id1', 'name': 'archive.checkpoint'}
    )

    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    flexmock(module).should_receive('rename_checkpoint_archive').with_args(
        repository_path='repo',
        global_arguments=global_arguments,
        config={},
        local_borg_version=None,
        local_path=None,
        remote_path=None,
    ).once()
    create_arguments = flexmock(
        repository=None,
        progress=flexmock(),
        statistics=flexmock(),
        json=False,
        comment=None,
        list_details=flexmock(),
    )

    list(
        module.run_create(
            config_filename='test.yaml',
            repository={'path': 'repo'},
            config={},
            config_paths=['/tmp/test.yaml'],
            local_borg_version=None,
            create_arguments=create_arguments,
            global_arguments=global_arguments,
            dry_run_label='',
            local_path=None,
            remote_path=None,
        )
    )


def test_run_create_with_active_dumps_json_updates_archive_info():
    mock_dump_process = flexmock()
    mock_dump_process.should_receive('poll').and_return(None).and_return(0)

    borg_create_result = {
        'archive': {
            'command_line': ['foo'],
            'name': 'archive.checkpoint',
            'id': 'id1',
        },
        'cache': {},
        'repository': {
            'id': 'repo-id',
        },
    }

    expected_create_result = {
        'archive': {
            'command_line': ['foo'],
            'name': 'archive',
            'id': 'id2',
        },
        'cache': {},
        'repository': {'id': 'repo-id', 'label': ''},
    }

    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').never()
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        flexmock()
    )

    flexmock(module.borgmatic.borg.create).should_receive('create_archive').and_return(
        json.dumps(borg_create_result)
    ).once()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return(
        {'dump': mock_dump_process}
    )
    flexmock(module.borgmatic.hooks.dispatch).should_receive(
        'call_hooks_even_if_unconfigured'
    ).and_return({})
    flexmock(module.borgmatic.actions.pattern).should_receive('collect_patterns').and_return(())
    flexmock(module.borgmatic.actions.pattern).should_receive('process_patterns').and_return([])
    flexmock(os.path).should_receive('join').and_return('/run/borgmatic/bootstrap')

    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    flexmock(module).should_receive('rename_checkpoint_archive').with_args(
        repository_path='repo',
        global_arguments=global_arguments,
        config={},
        local_borg_version=None,
        local_path=None,
        remote_path=None,
    ).once()

    flexmock(module.borgmatic.borg.repo_list).should_receive('get_latest_archive').and_return(
        {'id': 'id2', 'name': 'archive'},
    )

    create_arguments = flexmock(
        repository=None,
        progress=flexmock(),
        statistics=flexmock(),
        json=True,
        comment=None,
        list_details=flexmock(),
    )

    assert list(
        module.run_create(
            config_filename='test.yaml',
            repository={'path': 'repo'},
            config={},
            config_paths=['/tmp/test.yaml'],
            local_borg_version=None,
            create_arguments=create_arguments,
            global_arguments=global_arguments,
            dry_run_label='',
            local_path=None,
            remote_path=None,
        )
    ) == [expected_create_result]


def test_rename_checkpoint_archive_renames_archive():
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)
    flexmock(module.borgmatic.borg.repo_list).should_receive('get_latest_archive').and_return(
        {'id': 'id1', 'name': 'archive.checkpoint'}
    )

    flexmock(module.borgmatic.borg.rename).should_receive('rename_archive').with_args(
        repository_name='path',
        old_archive_name='archive.checkpoint',
        new_archive_name='archive',
        dry_run=False,
        config={},
        local_borg_version=None,
        local_path=None,
        remote_path=None,
    )

    module.rename_checkpoint_archive(
        repository_path='path',
        global_arguments=global_arguments,
        config={},
        local_borg_version=None,
        local_path=None,
        remote_path=None,
    )


def test_rename_checkpoint_archive_checks_suffix():
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)
    flexmock(module.borgmatic.borg.repo_list).should_receive('get_latest_archive').and_return(
        {'id': 'id1', 'name': 'unexpected-archive'}
    )

    with pytest.raises(
        ValueError,
        match='Latest archive did not have a .checkpoint suffix. Got: unexpected-archive',
    ):
        module.rename_checkpoint_archive(
            repository_path='path',
            global_arguments=global_arguments,
            config={},
            local_borg_version=None,
            local_path=None,
            remote_path=None,
        )
