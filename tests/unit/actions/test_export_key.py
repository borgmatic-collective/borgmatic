from flexmock import flexmock

from borgmatic.actions import export_key as module


def test_run_export_key_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.export_key).should_receive('export_key')
    export_arguments = flexmock(repository=flexmock())

    module.run_export_key(
        repository={'path': 'repo'},
        config={},
        local_borg_version=None,
        export_arguments=export_arguments,
        global_arguments=flexmock(),
        local_path=None,
        remote_path=None,
    )
