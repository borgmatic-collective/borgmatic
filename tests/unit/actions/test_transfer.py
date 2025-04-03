import pytest
from flexmock import flexmock

from borgmatic.actions import transfer as module


def test_run_transfer_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.transfer).should_receive('transfer_archives')
    transfer_arguments = flexmock(archive=None)
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_transfer(
        repository={'path': 'repo'},
        config={},
        local_borg_version=None,
        transfer_arguments=transfer_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )


def test_run_transfer_with_archive_and_match_archives_raises():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.transfer).should_receive('transfer_archives')
    transfer_arguments = flexmock(archive='foo')
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    with pytest.raises(ValueError):
        module.run_transfer(
            repository={'path': 'repo'},
            config={'match_archives': 'foo*'},
            local_borg_version=None,
            transfer_arguments=transfer_arguments,
            global_arguments=global_arguments,
            local_path=None,
            remote_path=None,
        )
