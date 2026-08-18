from flexmock import flexmock

from borgmatic.actions import import_key as module


def test_run_import_key_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.import_key).should_receive('import_key')
    import_arguments = flexmock(repository=flexmock())

    module.run_import_key(
        repository={'path': 'repo'},
        config={},
        local_borg_version=None,
        import_arguments=import_arguments,
        global_arguments=flexmock(),
        local_path=None,
        remote_path=None,
    )
