from flexmock import flexmock

from borgmatic.actions import check as module


def test_run_check_calls_hooks():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.checks).should_receive(
        'repository_enabled_for_checks'
    ).and_return(True)
    flexmock(module.borgmatic.borg.check).should_receive('check_archives')
    flexmock(module.borgmatic.hooks.command).should_receive('execute_hook').times(2)
    check_arguments = flexmock(
        progress=flexmock(), repair=flexmock(), only=flexmock(), force=flexmock()
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_check(
        config_filename='test.yaml',
        repository='repo',
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
