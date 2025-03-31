from flexmock import flexmock

from borgmatic.actions import compact as module


def test_compact_actions_calls_hooks_for_configured_repository():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').never()
    flexmock(module.borgmatic.borg.compact).should_receive('compact_segments').once()
    compact_arguments = flexmock(
        repository=None,
        progress=flexmock(),
        cleanup_commits=flexmock(),
        compact_threshold=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_compact(
        config_filename='test.yaml',
        repository={'path': 'repo'},
        config={},
        local_borg_version=None,
        compact_arguments=compact_arguments,
        global_arguments=global_arguments,
        dry_run_label='',
        local_path=None,
        remote_path=None,
    )


def test_compact_runs_with_selected_repository():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive(
        'repositories_match'
    ).once().and_return(True)
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.compact).should_receive('compact_segments').once()
    compact_arguments = flexmock(
        repository=flexmock(),
        progress=flexmock(),
        cleanup_commits=flexmock(),
        compact_threshold=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_compact(
        config_filename='test.yaml',
        repository={'path': 'repo'},
        config={},
        local_borg_version=None,
        compact_arguments=compact_arguments,
        global_arguments=global_arguments,
        dry_run_label='',
        local_path=None,
        remote_path=None,
    )


def test_compact_bails_if_repository_does_not_match():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.config.validate).should_receive(
        'repositories_match'
    ).once().and_return(False)
    flexmock(module.borgmatic.borg.compact).should_receive('compact_segments').never()
    compact_arguments = flexmock(
        repository=flexmock(),
        progress=flexmock(),
        cleanup_commits=flexmock(),
        compact_threshold=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_compact(
        config_filename='test.yaml',
        repository={'path': 'repo'},
        config={},
        local_borg_version=None,
        compact_arguments=compact_arguments,
        global_arguments=global_arguments,
        dry_run_label='',
        local_path=None,
        remote_path=None,
    )
