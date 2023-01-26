from flexmock import flexmock

from borgmatic.actions import compact as module


def test_compact_actions_calls_hooks():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.compact).should_receive('compact_segments')
    flexmock(module.borgmatic.hooks.command).should_receive('execute_hook').times(2)
    compact_arguments = flexmock(
        progress=flexmock(), cleanup_commits=flexmock(), threshold=flexmock()
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_compact(
        config_filename='test.yaml',
        repository='repo',
        storage={},
        retention={},
        hooks={},
        hook_context={},
        local_borg_version=None,
        compact_arguments=compact_arguments,
        global_arguments=global_arguments,
        dry_run_label='',
        local_path=None,
        remote_path=None,
    )
