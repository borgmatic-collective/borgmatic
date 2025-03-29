from flexmock import flexmock

from borgmatic.actions import compact as module


def test_compact_actions_calls_hooks_for_configured_repository():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').never()
    flexmock(module.borgmatic.borg.compact).should_receive('compact_segments').once()
    compact_arguments = flexmock(
        repository=None, progress=flexmock(), cleanup_commits=flexmock(), threshold=flexmock()
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
        repository=flexmock(), progress=flexmock(), cleanup_commits=flexmock(), threshold=flexmock()
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


def test_compact_favors_flags_over_config():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive(
        'repositories_match'
    ).once().and_return(True)
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.compact).should_receive('compact_segments').with_args(
        object,
        object,
        object,
        object,
        object,
        local_path=object,
        remote_path=object,
        progress=False,
        cleanup_commits=object,
        threshold=15,
    ).once()
    compact_arguments = flexmock(
        repository=flexmock(),
        progress=False,
        cleanup_commits=flexmock(),
        threshold=15,
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_compact(
        config_filename='test.yaml',
        repository={'path': 'repo'},
        config={'progress': True, 'compact_threshold': 20},
        local_borg_version=None,
        compact_arguments=compact_arguments,
        global_arguments=global_arguments,
        dry_run_label='',
        local_path=None,
        remote_path=None,
    )


def test_compact_favors_defaults_to_config():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive(
        'repositories_match'
    ).once().and_return(True)
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.compact).should_receive('compact_segments').with_args(
        object,
        object,
        object,
        object,
        object,
        local_path=object,
        remote_path=object,
        progress=True,
        cleanup_commits=object,
        threshold=20,
    ).once()
    compact_arguments = flexmock(
        repository=flexmock(),
        progress=None,
        cleanup_commits=flexmock(),
        threshold=None,
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_compact(
        config_filename='test.yaml',
        repository={'path': 'repo'},
        config={'progress': True, 'compact_threshold': 20},
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
        repository=flexmock(), progress=flexmock(), cleanup_commits=flexmock(), threshold=flexmock()
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
