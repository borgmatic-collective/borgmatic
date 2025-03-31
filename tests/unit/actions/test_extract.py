from flexmock import flexmock

from borgmatic.actions import extract as module


def test_run_extract_calls_hooks():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive')
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
        repository={'path': 'repo'},
        config={'repositories': ['repo']},
        local_borg_version=None,
        extract_arguments=extract_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )


def test_run_extract_favors_flags_over_config():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').with_args(
        object,
        object,
        object,
        object,
        object,
        object,
        object,
        local_path=object,
        remote_path=object,
        destination_path=object,
        strip_components=object,
    ).once()
    extract_arguments = flexmock(
        paths=flexmock(),
        progress=False,
        destination=flexmock(),
        strip_components=flexmock(),
        archive=flexmock(),
        repository='repo',
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_extract(
        config_filename='test.yaml',
        repository={'path': 'repo'},
        config={'repositories': ['repo'], 'progress': True},
        local_borg_version=None,
        extract_arguments=extract_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )


def test_run_extract_defaults_to_config():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').with_args(
        object,
        object,
        object,
        object,
        object,
        object,
        object,
        local_path=object,
        remote_path=object,
        destination_path=object,
        strip_components=object,
    ).once()
    extract_arguments = flexmock(
        paths=flexmock(),
        progress=None,
        destination=flexmock(),
        strip_components=flexmock(),
        archive=flexmock(),
        repository='repo',
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_extract(
        config_filename='test.yaml',
        repository={'path': 'repo'},
        config={'repositories': ['repo'], 'progress': True},
        local_borg_version=None,
        extract_arguments=extract_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )
