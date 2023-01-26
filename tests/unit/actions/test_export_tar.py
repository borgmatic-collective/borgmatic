from flexmock import flexmock

from borgmatic.actions import export_tar as module


def test_run_export_tar_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.export_tar).should_receive('export_tar_archive')
    export_tar_arguments = flexmock(
        repository=flexmock(),
        archive=flexmock(),
        paths=flexmock(),
        destination=flexmock(),
        tar_filter=flexmock(),
        list_files=flexmock(),
        strip_components=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_export_tar(
        repository='repo',
        storage={},
        local_borg_version=None,
        export_tar_arguments=export_tar_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )
