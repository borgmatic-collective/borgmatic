from flexmock import flexmock

from borgmatic.actions.config import bootstrap as module


def test_get_config_paths_returns_list_of_config_paths():
    bootstrap_arguments = flexmock(
        borgmatic_source_directory=None,
        repository='repo',
        archive='archive',
    )
    global_arguments = flexmock(
        dry_run=False,
    )
    local_borg_version = flexmock()
    extract_process = flexmock(
        stdout=flexmock(
            read=lambda: '{"config_paths": ["/borgmatic/config.yaml"]}',
        ),
    )
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        extract_process
    )
    flexmock(module.borgmatic.borg.rlist).should_receive('resolve_archive_name').and_return(
        'archive'
    )
    assert module.get_config_paths(
        bootstrap_arguments, global_arguments, local_borg_version
    ) == ['/borgmatic/config.yaml']


def test_run_bootstrap_does_not_raise():
    bootstrap_arguments = flexmock(
        repository='repo',
        archive='archive',
        destination='dest',
        strip_components=1,
        progress=False,
        borgmatic_source_directory='/borgmatic',
    )
    global_arguments = flexmock(
        dry_run=False,
    )
    local_borg_version = flexmock()
    extract_process = flexmock(
        stdout=flexmock(
            read=lambda: '{"config_paths": ["/borgmatic/config.yaml"]}',
        ),
    )
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        extract_process
    ).twice()
    flexmock(module.borgmatic.borg.rlist).should_receive('resolve_archive_name').and_return(
        'archive'
    )
    module.run_bootstrap(bootstrap_arguments, global_arguments, local_borg_version)
