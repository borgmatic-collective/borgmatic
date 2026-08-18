from flexmock import flexmock

from borgmatic.actions import prune as module


def test_run_prune_calls_hooks_for_configured_repository():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.prune).should_receive('prune_archives').once()
    prune_arguments = flexmock(repository=None, statistics=flexmock(), list_details=flexmock())
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_prune(
        config_filename='test.yaml',
        repository={'path': 'repo'},
        config={},
        local_borg_version=None,
        prune_arguments=prune_arguments,
        global_arguments=global_arguments,
        dry_run_label='',
        local_path=None,
        remote_path=None,
    )
