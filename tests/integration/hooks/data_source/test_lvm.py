from flexmock import flexmock

from borgmatic.borg.pattern import Pattern, Pattern_type
from borgmatic.hooks.data_source import lvm as module


def test_dump_data_sources_snapshots_and_mounts_and_updates_patterns():
    config = {'lvm': {}}
    patterns = [
        Pattern('/mnt/lvolume1/subdir'),
        Pattern('/mnt/lvolume1/subdir/.cache', Pattern_type.EXCLUDE),
        Pattern('/mnt/lvolume2'),
    ]
    logical_volumes = (
        module.Logical_volume(
            name='lvolume1',
            device_path='/dev/lvolume1',
            mount_point='/mnt/lvolume1',
            contained_patterns=(
                Pattern('/mnt/lvolume1/subdir'),
                Pattern('/mnt/lvolume1/subdir/.cache', Pattern_type.EXCLUDE),
            ),
        ),
        module.Logical_volume(
            name='lvolume2',
            device_path='/dev/lvolume2',
            mount_point='/mnt/lvolume2',
            contained_patterns=(Pattern('/mnt/lvolume2'),),
        ),
    )
    flexmock(module).should_receive('get_logical_volumes').and_return(logical_volumes)
    flexmock(module.os).should_receive('getpid').and_return(1234)
    flexmock(module).should_receive('snapshot_logical_volume').with_args(
        'lvcreate',
        'lvolume1_borgmatic-1234',
        '/dev/lvolume1',
        module.DEFAULT_SNAPSHOT_SIZE,
    ).once()
    flexmock(module).should_receive('snapshot_logical_volume').with_args(
        'lvcreate',
        'lvolume2_borgmatic-1234',
        '/dev/lvolume2',
        module.DEFAULT_SNAPSHOT_SIZE,
    ).once()
    flexmock(module).should_receive('get_snapshots').with_args(
        'lvs',
        snapshot_name='lvolume1_borgmatic-1234',
    ).and_return(
        (module.Snapshot(name='lvolume1_borgmatic-1234', device_path='/dev/lvolume1_snap'),),
    )
    flexmock(module).should_receive('get_snapshots').with_args(
        'lvs',
        snapshot_name='lvolume2_borgmatic-1234',
    ).and_return(
        (module.Snapshot(name='lvolume2_borgmatic-1234', device_path='/dev/lvolume2_snap'),),
    )
    flexmock(module.hashlib).should_receive('shake_256').and_return(
        flexmock(hexdigest=lambda length: 'b33f'),
    )
    flexmock(module).should_receive('mount_snapshot').with_args(
        'mount',
        '/dev/lvolume1_snap',
        '/run/borgmatic/lvm_snapshots/b33f/mnt/lvolume1',
    ).once()
    flexmock(module).should_receive('mount_snapshot').with_args(
        'mount',
        '/dev/lvolume2_snap',
        '/run/borgmatic/lvm_snapshots/b33f/mnt/lvolume2',
    ).once()

    assert (
        module.dump_data_sources(
            hook_config=config['lvm'],
            config=config,
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=patterns,
            dry_run=False,
        )
        == []
    )

    assert patterns == [
        Pattern('/run/borgmatic/lvm_snapshots/b33f/./mnt/lvolume1/subdir'),
        Pattern(
            '/run/borgmatic/lvm_snapshots/b33f/./mnt/lvolume1/subdir/.cache', Pattern_type.EXCLUDE
        ),
        Pattern('/run/borgmatic/lvm_snapshots/b33f/./mnt/lvolume2'),
    ]
