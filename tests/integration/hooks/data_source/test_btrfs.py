from flexmock import flexmock

from borgmatic.borg.pattern import Pattern, Pattern_style, Pattern_type
from borgmatic.hooks.data_source import btrfs as module


def test_dump_data_sources_snapshots_each_subvolume_and_updates_patterns():
    patterns = [
        Pattern('/foo'),
        Pattern('/mnt/subvol1'),
        Pattern('/mnt/subvol1/.cache', Pattern_type.EXCLUDE),
        Pattern('/mnt/subvol2'),
    ]
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(
        (
            module.Subvolume(
                '/mnt/subvol1',
                contained_patterns=(
                    Pattern('/mnt/subvol1'),
                    Pattern('/mnt/subvol1/.cache', Pattern_type.EXCLUDE),
                ),
            ),
            module.Subvolume('/mnt/subvol2', contained_patterns=(Pattern('/mnt/subvol2'),)),
        ),
    )
    flexmock(module.os).should_receive('getpid').and_return(1234)
    flexmock(module).should_receive('snapshot_subvolume').with_args(
        'btrfs',
        '/mnt/subvol1',
        '/mnt/subvol1/.borgmatic-snapshot-1234/mnt/subvol1',
    ).once()
    flexmock(module).should_receive('snapshot_subvolume').with_args(
        'btrfs',
        '/mnt/subvol2',
        '/mnt/subvol2/.borgmatic-snapshot-1234/mnt/subvol2',
    ).once()

    assert (
        module.dump_data_sources(
            hook_config=config['btrfs'],
            config=config,
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=patterns,
            dry_run=False,
        )
        == []
    )

    assert patterns == [
        Pattern(
            '/mnt/subvol2/.borgmatic-snapshot-1234/mnt/subvol2/.borgmatic-snapshot-1234',
            Pattern_type.NO_RECURSE,
            Pattern_style.FNMATCH,
        ),
        Pattern(
            '/mnt/subvol1/.borgmatic-snapshot-1234/mnt/subvol1/.borgmatic-snapshot-1234',
            Pattern_type.NO_RECURSE,
            Pattern_style.FNMATCH,
        ),
        Pattern('/foo'),
        Pattern('/mnt/subvol1/.borgmatic-snapshot-1234/./mnt/subvol1'),
        Pattern('/mnt/subvol1/.borgmatic-snapshot-1234/./mnt/subvol1/.cache', Pattern_type.EXCLUDE),
        Pattern('/mnt/subvol2/.borgmatic-snapshot-1234/./mnt/subvol2'),
    ]
    assert config == {
        'btrfs': {},
    }
