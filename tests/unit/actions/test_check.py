from flexmock import flexmock

from borgmatic.actions import check as module


def test_run_check_calls_hooks_for_configured_repository():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.checks).should_receive(
        'repository_enabled_for_checks'
    ).and_return(True)
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').never()
    flexmock(module.borgmatic.borg.check).should_receive('check_archives').once()
    flexmock(module.borgmatic.hooks.command).should_receive('execute_hook').times(2)
    check_arguments = flexmock(
        repository=None,
        progress=flexmock(),
        repair=flexmock(),
        only=flexmock(),
        force=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_check(
        config_filename='test.yaml',
        repository={'path': 'repo'},
        location={'repositories': ['repo']},
        storage={},
        consistency={},
        hooks={},
        hook_context={},
        local_borg_version=None,
        check_arguments=check_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )


def test_run_check_runs_with_selected_repository():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive(
        'repositories_match'
    ).once().and_return(True)
    flexmock(module.borgmatic.borg.check).should_receive('check_archives').once()
    check_arguments = flexmock(
        repository=flexmock(),
        progress=flexmock(),
        repair=flexmock(),
        only=flexmock(),
        force=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_check(
        config_filename='test.yaml',
        repository={'path': 'repo'},
        location={'repositories': ['repo']},
        storage={},
        consistency={},
        hooks={},
        hook_context={},
        local_borg_version=None,
        check_arguments=check_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )


def test_run_check_bails_if_repository_does_not_match():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive(
        'repositories_match'
    ).once().and_return(False)
    flexmock(module.borgmatic.borg.check).should_receive('check_archives').never()
    check_arguments = flexmock(
        repository=flexmock(),
        progress=flexmock(),
        repair=flexmock(),
        only=flexmock(),
        force=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_check(
        config_filename='test.yaml',
        repository={'path': 'repo'},
        location={'repositories': ['repo']},
        storage={},
        consistency={},
        hooks={},
        hook_context={},
        local_borg_version=None,
        check_arguments=check_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )
