import os

from flexmock import flexmock

from borgmatic.borg.pattern import Pattern, Pattern_type
from borgmatic.hooks.data_source import zfs as module


def test_dump_data_sources_snapshots_and_mounts_and_updates_patterns():
    dataset = flexmock(
        name='dataset',
        mount_point='/mnt/dataset',
        contained_patterns=(Pattern('/mnt/dataset/subdir'),),
    )
    flexmock(module).should_receive('get_datasets_to_backup').and_return((dataset,))
    flexmock(module.os).should_receive('getpid').and_return(1234)
    full_snapshot_name = 'dataset@borgmatic-1234'
    flexmock(module).should_receive('snapshot_dataset').with_args(
        'zfs',
        full_snapshot_name,
    ).once()
    flexmock(module.hashlib).should_receive('shake_256').and_return(
        flexmock(hexdigest=lambda length: 'b33f'),
    )
    snapshot_mount_path = '/run/borgmatic/zfs_snapshots/b33f/./mnt/dataset'
    flexmock(module).should_receive('mount_snapshot').with_args(
        'mount',
        full_snapshot_name,
        module.os.path.normpath(snapshot_mount_path),
    ).once()
    patterns = [Pattern('/mnt/dataset/subdir')]

    assert (
        module.dump_data_sources(
            hook_config={},
            config={'source_directories': '/mnt/dataset', 'zfs': {}},
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=patterns,
            dry_run=False,
        )
        == []
    )

    assert patterns == [
        Pattern(os.path.join(snapshot_mount_path, 'subdir')),
        Pattern(os.path.join(snapshot_mount_path, 'subdir'), Pattern_type.INCLUDE),
    ]
