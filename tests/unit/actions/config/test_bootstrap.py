from flexmock import flexmock

from borgmatic.actions.config import bootstrap as module


def test_run_bootstrap():
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
    )
    flexmock(module.borgmatic.borg.rlist).should_receive('resolve_archive_name').and_return(
        'archive'
    )
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        extract_process
    )
    module.run_bootstrap(bootstrap_arguments, global_arguments, local_borg_version)
