from flexmock import flexmock

from borgmatic.actions import extract as module


def test_run_extract_calls_hooks():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive')
    flexmock(module.borgmatic.hooks.command).should_receive('execute_hook').times(2)
    extract_arguments = flexmock(
        paths=flexmock(),
        progress=flexmock(),
        destination=flexmock(),
        strip_components=flexmock(),
        archive=flexmock(),
        repository='repo',
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_extract(
        config_filename='test.yaml',
        repository='repo',
        location={'repositories': ['repo']},
        storage={},
        hooks={},
        hook_context={},
        local_borg_version=None,
        extract_arguments=extract_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )
