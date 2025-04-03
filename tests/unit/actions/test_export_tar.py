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
        list_details=flexmock(),
        strip_components=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_export_tar(
        repository={'path': 'repo'},
        config={},
        local_borg_version=None,
        export_tar_arguments=export_tar_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )


def test_run_export_tar_favors_flags_over_config():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.export_tar).should_receive('export_tar_archive').with_args(
        object,
        object,
        object,
        object,
        object,
        object,
        object,
        object,
        local_path=object,
        remote_path=object,
        tar_filter=object,
        strip_components=object,
    ).once()
    export_tar_arguments = flexmock(
        repository=flexmock(),
        archive=flexmock(),
        paths=flexmock(),
        destination=flexmock(),
        tar_filter=flexmock(),
        list_details=False,
        strip_components=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_export_tar(
        repository={'path': 'repo'},
        config={'list_details': True},
        local_borg_version=None,
        export_tar_arguments=export_tar_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )


def test_run_export_tar_defaults_to_config():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.export_tar).should_receive('export_tar_archive').with_args(
        object,
        object,
        object,
        object,
        object,
        object,
        object,
        object,
        local_path=object,
        remote_path=object,
        tar_filter=object,
        strip_components=object,
    ).once()
    export_tar_arguments = flexmock(
        repository=flexmock(),
        archive=flexmock(),
        paths=flexmock(),
        destination=flexmock(),
        tar_filter=flexmock(),
        list_details=None,
        strip_components=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_export_tar(
        repository={'path': 'repo'},
        config={'list_details': True},
        local_borg_version=None,
        export_tar_arguments=export_tar_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )
