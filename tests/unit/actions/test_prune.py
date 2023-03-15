from flexmock import flexmock

from borgmatic.actions import prune as module


def test_run_prune_calls_hooks():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.prune).should_receive('prune_archives')
    flexmock(module.borgmatic.hooks.command).should_receive('execute_hook').times(2)
    prune_arguments = flexmock(repository=None, stats=flexmock(), list_archives=flexmock())
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_prune(
        config_filename='test.yaml',
        repository='repo',
        storage={},
        retention={},
        hooks={},
        hook_context={},
        local_borg_version=None,
        prune_arguments=prune_arguments,
        global_arguments=global_arguments,
        dry_run_label='',
        local_path=None,
        remote_path=None,
    )


def test_run_prune_runs_with_no_explicit_repository():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.prune).should_receive('prune_archives')
    prune_arguments = flexmock(repository=None, stats=flexmock(), list_archives=flexmock())
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_prune(
        config_filename='test.yaml',
        repository='repo',
        storage={},
        retention={},
        hooks={},
        hook_context={},
        local_borg_version=None,
        prune_arguments=prune_arguments,
        global_arguments=global_arguments,
        dry_run_label='',
        local_path=None,
        remote_path=None,
    )


def test_run_prune_runs_with_select_repository():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.prune).should_receive('prune_archives')
    prune_arguments = flexmock(repository=flexmock(), stats=flexmock(), list_archives=flexmock())
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_prune(
        config_filename='test.yaml',
        repository='repo',
        storage={},
        retention={},
        hooks={},
        hook_context={},
        local_borg_version=None,
        prune_arguments=prune_arguments,
        global_arguments=global_arguments,
        dry_run_label='',
        local_path=None,
        remote_path=None,
    )


def test_run_prune_bails_if_repository_does_not_match():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(
        False
    )
    flexmock(module.borgmatic.borg.prune).should_receive('prune_archives').never()
    prune_arguments = flexmock(repository=flexmock(), stats=flexmock(), list_archives=flexmock())
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_prune(
        config_filename='test.yaml',
        repository='repo',
        storage={},
        retention={},
        hooks={},
        hook_context={},
        local_borg_version=None,
        prune_arguments=prune_arguments,
        global_arguments=global_arguments,
        dry_run_label='',
        local_path=None,
        remote_path=None,
    )
