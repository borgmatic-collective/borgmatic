from flexmock import flexmock

from borgmatic.actions import mount as module


def test_run_mount_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.mount).should_receive('mount_archive')
    mount_arguments = flexmock(
        repository=flexmock(),
        archive=flexmock(),
        mount_point=flexmock(),
        paths=flexmock(),
        foreground=flexmock(),
        options=flexmock(),
    )

    module.run_mount(
        repository='repo',
        storage={},
        local_borg_version=None,
        mount_arguments=mount_arguments,
        local_path=None,
        remote_path=None,
    )
