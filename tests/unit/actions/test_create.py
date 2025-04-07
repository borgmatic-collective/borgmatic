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
