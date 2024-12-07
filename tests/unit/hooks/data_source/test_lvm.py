from flexmock import flexmock
import pytest

from borgmatic.hooks.data_source import lvm as module


def test_get_logical_volumes_filters_by_source_directories():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return(
        '''
        {
            "blockdevices": [
                {
                   "name": "vgroup-notmounted",
                   "path": "/dev/mapper/vgroup-notmounted",
                   "mountpoint": null,
                   "type": "lvm"
                }, {
                   "name": "vgroup-lvolume",
                   "path": "/dev/mapper/vgroup-lvolume",
                   "mountpoint": "/mnt/lvolume",
                   "type": "lvm"
                }, {
                   "name": "vgroup-other",
                   "path": "/dev/mapper/vgroup-other",
                   "mountpoint": "/mnt/other",
                   "type": "lvm"
                }, {
                   "name": "vgroup-notlvm",
                   "path": "/dev/mapper/vgroup-notlvm",
                   "mountpoint": "/mnt/notlvm",
                   "type": "notlvm"
                }
            ]
        }
        '''
    )
    contained = {'/mnt/lvolume', '/mnt/lvolume/subdir'}
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_directories'
    ).with_args(None, contained).never()
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_directories'
    ).with_args('/mnt/lvolume', contained).and_return(('/mnt/lvolume', '/mnt/lvolume/subdir'))
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_directories'
    ).with_args('/mnt/other', contained).and_return(())
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_directories'
    ).with_args('/mnt/notlvm', contained).never()

    assert module.get_logical_volumes(
        'lsblk', source_directories=('/mnt/lvolume', '/mnt/lvolume/subdir')
    ) == (
        module.Logical_volume(
            'vgroup-lvolume',
            '/dev/mapper/vgroup-lvolume',
            '/mnt/lvolume',
            ('/mnt/lvolume', '/mnt/lvolume/subdir'),
        ),
    )


def test_get_logical_volumes_with_invalid_lsblk_json_errors():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return('{')

    contained = {'/mnt/lvolume', '/mnt/lvolume/subdir'}
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_directories'
    ).never()

    with pytest.raises(ValueError):
        module.get_logical_volumes(
            'lsblk', source_directories=('/mnt/lvolume', '/mnt/lvolume/subdir')
        )


def test_get_logical_volumes_with_lsblk_json_missing_keys_errors():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return('{"block_devices": [{}]}')

    contained = {'/mnt/lvolume', '/mnt/lvolume/subdir'}
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_directories'
    ).never()

    with pytest.raises(ValueError):
        module.get_logical_volumes(
            'lsblk', source_directories=('/mnt/lvolume', '/mnt/lvolume/subdir')
        )


def test_snapshot_logical_volume_with_percentage_snapshot_name_uses_lvcreate_extents_flag():
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        (
            'lvcreate',
            '--snapshot',
            '--extents',
            '10%ORIGIN',
            '--name',
            'snap',
            '/dev/snap',
        ),
        output_log_level=object,
    )

    module.snapshot_logical_volume('lvcreate', 'snap', '/dev/snap', '10%ORIGIN')


def test_snapshot_logical_volume_with_non_percentage_snapshot_name_uses_lvcreate_size_flag():
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        (
            'lvcreate',
            '--snapshot',
            '--size',
            '10TB',
            '--name',
            'snap',
            '/dev/snap',
        ),
        output_log_level=object,
    )

    module.snapshot_logical_volume('lvcreate', 'snap', '/dev/snap', '10TB')


def test_dump_data_sources_snapshots_and_mounts_and_updates_source_directories():
    config = {'lvm': {}}
    source_directories = ['/mnt/lvolume1/subdir', '/mnt/lvolume2']
    flexmock(module).should_receive('get_logical_volumes').and_return(
        (
            module.Logical_volume(
                name='lvolume1',
                device_path='/dev/lvolume1',
                mount_point='/mnt/lvolume1',
                contained_source_directories=('/mnt/lvolume1/subdir',),
            ),
            module.Logical_volume(
                name='lvolume2',
                device_path='/dev/lvolume2',
                mount_point='/mnt/lvolume2',
                contained_source_directories=('/mnt/lvolume2',),
            ),
        )
    )
    flexmock(module.os).should_receive('getpid').and_return(1234)
    flexmock(module).should_receive('snapshot_logical_volume').with_args(
        'lvcreate', 'lvolume1_borgmatic-1234', '/dev/lvolume1', module.DEFAULT_SNAPSHOT_SIZE
    ).once()
    flexmock(module).should_receive('snapshot_logical_volume').with_args(
        'lvcreate', 'lvolume2_borgmatic-1234', '/dev/lvolume2', module.DEFAULT_SNAPSHOT_SIZE
    ).once()
    flexmock(module).should_receive('get_snapshots').with_args(
        'lvs', snapshot_name='lvolume1_borgmatic-1234'
    ).and_return(
        (module.Snapshot(name='lvolume1_borgmatic-1234', device_path='/dev/lvolume1_snap'),)
    )
    flexmock(module).should_receive('get_snapshots').with_args(
        'lvs', snapshot_name='lvolume2_borgmatic-1234'
    ).and_return(
        (module.Snapshot(name='lvolume2_borgmatic-1234', device_path='/dev/lvolume2_snap'),)
    )
    flexmock(module).should_receive('mount_snapshot').with_args(
        'mount', '/dev/lvolume1_snap', '/run/borgmatic/lvm_snapshots/mnt/lvolume1'
    ).once()
    flexmock(module).should_receive('mount_snapshot').with_args(
        'mount', '/dev/lvolume2_snap', '/run/borgmatic/lvm_snapshots/mnt/lvolume2'
    ).once()

    assert (
        module.dump_data_sources(
            hook_config=config['lvm'],
            config=config,
            log_prefix='test',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            source_directories=source_directories,
            dry_run=False,
        )
        == []
    )

    assert source_directories == [
        '/run/borgmatic/lvm_snapshots/./mnt/lvolume1/subdir',
        '/run/borgmatic/lvm_snapshots/./mnt/lvolume2',
    ]


def test_dump_data_sources_with_no_logical_volumes_skips_snapshots():
    config = {'lvm': {}}
    source_directories = ['/mnt/lvolume1/subdir', '/mnt/lvolume2']
    flexmock(module).should_receive('get_logical_volumes').and_return(())
    flexmock(module).should_receive('snapshot_logical_volume').never()
    flexmock(module).should_receive('mount_snapshot').never()

    assert (
        module.dump_data_sources(
            hook_config=config['lvm'],
            config=config,
            log_prefix='test',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            source_directories=source_directories,
            dry_run=False,
        )
        == []
    )

    assert source_directories == ['/mnt/lvolume1/subdir', '/mnt/lvolume2']


def test_dump_data_sources_uses_snapshot_size_for_snapshot():
    config = {'lvm': {'snapshot_size': '1000PB'}}
    source_directories = ['/mnt/lvolume1/subdir', '/mnt/lvolume2']
    flexmock(module).should_receive('get_logical_volumes').and_return(
        (
            module.Logical_volume(
                name='lvolume1',
                device_path='/dev/lvolume1',
                mount_point='/mnt/lvolume1',
                contained_source_directories=('/mnt/lvolume1/subdir',),
            ),
            module.Logical_volume(
                name='lvolume2',
                device_path='/dev/lvolume2',
                mount_point='/mnt/lvolume2',
                contained_source_directories=('/mnt/lvolume2',),
            ),
        )
    )
    flexmock(module.os).should_receive('getpid').and_return(1234)
    flexmock(module).should_receive('snapshot_logical_volume').with_args(
        'lvcreate',
        'lvolume1_borgmatic-1234',
        '/dev/lvolume1',
        '1000PB',
    ).once()
    flexmock(module).should_receive('snapshot_logical_volume').with_args(
        'lvcreate',
        'lvolume2_borgmatic-1234',
        '/dev/lvolume2',
        '1000PB',
    ).once()
    flexmock(module).should_receive('get_snapshots').with_args(
        'lvs', snapshot_name='lvolume1_borgmatic-1234'
    ).and_return(
        (module.Snapshot(name='lvolume1_borgmatic-1234', device_path='/dev/lvolume1_snap'),)
    )
    flexmock(module).should_receive('get_snapshots').with_args(
        'lvs', snapshot_name='lvolume2_borgmatic-1234'
    ).and_return(
        (module.Snapshot(name='lvolume2_borgmatic-1234', device_path='/dev/lvolume2_snap'),)
    )
    flexmock(module).should_receive('mount_snapshot').with_args(
        'mount', '/dev/lvolume1_snap', '/run/borgmatic/lvm_snapshots/mnt/lvolume1'
    ).once()
    flexmock(module).should_receive('mount_snapshot').with_args(
        'mount', '/dev/lvolume2_snap', '/run/borgmatic/lvm_snapshots/mnt/lvolume2'
    ).once()

    assert (
        module.dump_data_sources(
            hook_config=config['lvm'],
            config=config,
            log_prefix='test',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            source_directories=source_directories,
            dry_run=False,
        )
        == []
    )

    assert source_directories == [
        '/run/borgmatic/lvm_snapshots/./mnt/lvolume1/subdir',
        '/run/borgmatic/lvm_snapshots/./mnt/lvolume2',
    ]


def test_dump_data_sources_uses_custom_commands():
    config = {
        'lvm': {
            'lsblk_command': '/usr/local/bin/lsblk',
            'lvcreate_command': '/usr/local/bin/lvcreate',
            'lvs_command': '/usr/local/bin/lvs',
            'mount_command': '/usr/local/bin/mount',
        },
    }
    source_directories = ['/mnt/lvolume1/subdir', '/mnt/lvolume2']
    flexmock(module).should_receive('get_logical_volumes').and_return(
        (
            module.Logical_volume(
                name='lvolume1',
                device_path='/dev/lvolume1',
                mount_point='/mnt/lvolume1',
                contained_source_directories=('/mnt/lvolume1/subdir',),
            ),
            module.Logical_volume(
                name='lvolume2',
                device_path='/dev/lvolume2',
                mount_point='/mnt/lvolume2',
                contained_source_directories=('/mnt/lvolume2',),
            ),
        )
    )
    flexmock(module.os).should_receive('getpid').and_return(1234)
    flexmock(module).should_receive('snapshot_logical_volume').with_args(
        '/usr/local/bin/lvcreate',
        'lvolume1_borgmatic-1234',
        '/dev/lvolume1',
        module.DEFAULT_SNAPSHOT_SIZE,
    ).once()
    flexmock(module).should_receive('snapshot_logical_volume').with_args(
        '/usr/local/bin/lvcreate',
        'lvolume2_borgmatic-1234',
        '/dev/lvolume2',
        module.DEFAULT_SNAPSHOT_SIZE,
    ).once()
    flexmock(module).should_receive('get_snapshots').with_args(
        '/usr/local/bin/lvs', snapshot_name='lvolume1_borgmatic-1234'
    ).and_return(
        (module.Snapshot(name='lvolume1_borgmatic-1234', device_path='/dev/lvolume1_snap'),)
    )
    flexmock(module).should_receive('get_snapshots').with_args(
        '/usr/local/bin/lvs', snapshot_name='lvolume2_borgmatic-1234'
    ).and_return(
        (module.Snapshot(name='lvolume2_borgmatic-1234', device_path='/dev/lvolume2_snap'),)
    )
    flexmock(module).should_receive('mount_snapshot').with_args(
        '/usr/local/bin/mount', '/dev/lvolume1_snap', '/run/borgmatic/lvm_snapshots/mnt/lvolume1'
    ).once()
    flexmock(module).should_receive('mount_snapshot').with_args(
        '/usr/local/bin/mount', '/dev/lvolume2_snap', '/run/borgmatic/lvm_snapshots/mnt/lvolume2'
    ).once()

    assert (
        module.dump_data_sources(
            hook_config=config['lvm'],
            config=config,
            log_prefix='test',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            source_directories=source_directories,
            dry_run=False,
        )
        == []
    )

    assert source_directories == [
        '/run/borgmatic/lvm_snapshots/./mnt/lvolume1/subdir',
        '/run/borgmatic/lvm_snapshots/./mnt/lvolume2',
    ]


def test_dump_data_sources_with_dry_run_skips_snapshots_and_does_not_touch_source_directories():
    config = {'lvm': {}}
    source_directories = ['/mnt/lvolume1/subdir', '/mnt/lvolume2']
    flexmock(module).should_receive('get_logical_volumes').and_return(
        (
            module.Logical_volume(
                name='lvolume1',
                device_path='/dev/lvolume1',
                mount_point='/mnt/lvolume1',
                contained_source_directories=('/mnt/lvolume1/subdir',),
            ),
            module.Logical_volume(
                name='lvolume2',
                device_path='/dev/lvolume2',
                mount_point='/mnt/lvolume2',
                contained_source_directories=('/mnt/lvolume2',),
            ),
        )
    )
    flexmock(module.os).should_receive('getpid').and_return(1234)
    flexmock(module).should_receive('snapshot_logical_volume').never()
    flexmock(module).should_receive('get_snapshots').with_args(
        'lvs', snapshot_name='lvolume1_borgmatic-1234'
    ).and_return(
        (module.Snapshot(name='lvolume1_borgmatic-1234', device_path='/dev/lvolume1_snap'),)
    )
    flexmock(module).should_receive('get_snapshots').with_args(
        'lvs', snapshot_name='lvolume2_borgmatic-1234'
    ).and_return(
        (module.Snapshot(name='lvolume2_borgmatic-1234', device_path='/dev/lvolume2_snap'),)
    )
    flexmock(module).should_receive('mount_snapshot').never()

    assert (
        module.dump_data_sources(
            hook_config=config['lvm'],
            config=config,
            log_prefix='test',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            source_directories=source_directories,
            dry_run=True,
        )
        == []
    )

    assert source_directories == [
        '/mnt/lvolume1/subdir',
        '/mnt/lvolume2',
    ]


def test_dump_data_sources_ignores_mismatch_between_source_directories_and_contained_source_directories():
    config = {'lvm': {}}
    source_directories = ['/hmm']
    flexmock(module).should_receive('get_logical_volumes').and_return(
        (
            module.Logical_volume(
                name='lvolume1',
                device_path='/dev/lvolume1',
                mount_point='/mnt/lvolume1',
                contained_source_directories=('/mnt/lvolume1/subdir',),
            ),
            module.Logical_volume(
                name='lvolume2',
                device_path='/dev/lvolume2',
                mount_point='/mnt/lvolume2',
                contained_source_directories=('/mnt/lvolume2',),
            ),
        )
    )
    flexmock(module.os).should_receive('getpid').and_return(1234)
    flexmock(module).should_receive('snapshot_logical_volume').with_args(
        'lvcreate', 'lvolume1_borgmatic-1234', '/dev/lvolume1', module.DEFAULT_SNAPSHOT_SIZE
    ).once()
    flexmock(module).should_receive('snapshot_logical_volume').with_args(
        'lvcreate', 'lvolume2_borgmatic-1234', '/dev/lvolume2', module.DEFAULT_SNAPSHOT_SIZE
    ).once()
    flexmock(module).should_receive('get_snapshots').with_args(
        'lvs', snapshot_name='lvolume1_borgmatic-1234'
    ).and_return(
        (module.Snapshot(name='lvolume1_borgmatic-1234', device_path='/dev/lvolume1_snap'),)
    )
    flexmock(module).should_receive('get_snapshots').with_args(
        'lvs', snapshot_name='lvolume2_borgmatic-1234'
    ).and_return(
        (module.Snapshot(name='lvolume2_borgmatic-1234', device_path='/dev/lvolume2_snap'),)
    )
    flexmock(module).should_receive('mount_snapshot').with_args(
        'mount', '/dev/lvolume1_snap', '/run/borgmatic/lvm_snapshots/mnt/lvolume1'
    ).once()
    flexmock(module).should_receive('mount_snapshot').with_args(
        'mount', '/dev/lvolume2_snap', '/run/borgmatic/lvm_snapshots/mnt/lvolume2'
    ).once()

    assert (
        module.dump_data_sources(
            hook_config=config['lvm'],
            config=config,
            log_prefix='test',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            source_directories=source_directories,
            dry_run=False,
        )
        == []
    )

    assert source_directories == [
        '/hmm',
        '/run/borgmatic/lvm_snapshots/./mnt/lvolume1/subdir',
        '/run/borgmatic/lvm_snapshots/./mnt/lvolume2',
    ]


def test_dump_data_sources_with_missing_snapshot_errors():
    config = {'lvm': {}}
    source_directories = ['/mnt/lvolume1/subdir', '/mnt/lvolume2']
    flexmock(module).should_receive('get_logical_volumes').and_return(
        (
            module.Logical_volume(
                name='lvolume1',
                device_path='/dev/lvolume1',
                mount_point='/mnt/lvolume1',
                contained_source_directories=('/mnt/lvolume1/subdir',),
            ),
            module.Logical_volume(
                name='lvolume2',
                device_path='/dev/lvolume2',
                mount_point='/mnt/lvolume2',
                contained_source_directories=('/mnt/lvolume2',),
            ),
        )
    )
    flexmock(module.os).should_receive('getpid').and_return(1234)
    flexmock(module).should_receive('snapshot_logical_volume').with_args(
        'lvcreate', 'lvolume1_borgmatic-1234', '/dev/lvolume1', module.DEFAULT_SNAPSHOT_SIZE
    ).once()
    flexmock(module).should_receive('snapshot_logical_volume').with_args(
        'lvcreate', 'lvolume2_borgmatic-1234', '/dev/lvolume2', module.DEFAULT_SNAPSHOT_SIZE
    ).never()
    flexmock(module).should_receive('get_snapshots').with_args(
        'lvs', snapshot_name='lvolume1_borgmatic-1234'
    ).and_return(())
    flexmock(module).should_receive('get_snapshots').with_args(
        'lvs', snapshot_name='lvolume2_borgmatic-1234'
    ).never()
    flexmock(module).should_receive('mount_snapshot').never()

    with pytest.raises(ValueError):
        module.dump_data_sources(
            hook_config=config['lvm'],
            config=config,
            log_prefix='test',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            source_directories=source_directories,
            dry_run=False,
        )


def test_get_snapshots_lists_all_snapshots():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return(
        '''
          {
              "report": [
                  {
                      "lv": [
                          {"lv_name": "snap1", "lv_path": "/dev/snap1"},
                          {"lv_name": "snap2", "lv_path": "/dev/snap2"}
                      ]
                  }
              ],
              "log": [
              ]
          }
        '''
    )

    assert module.get_snapshots('lvs') == (
        module.Snapshot('snap1', '/dev/snap1'),
        module.Snapshot('snap2', '/dev/snap2'),
    )


def test_get_snapshots_with_snapshot_name_lists_just_that_snapshot():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return(
        '''
          {
              "report": [
                  {
                      "lv": [
                          {"lv_name": "snap1", "lv_path": "/dev/snap1"},
                          {"lv_name": "snap2", "lv_path": "/dev/snap2"}
                      ]
                  }
              ],
              "log": [
              ]
          }
        '''
    )

    assert module.get_snapshots('lvs', snapshot_name='snap2') == (
        module.Snapshot('snap2', '/dev/snap2'),
    )


def test_get_snapshots_with_invalid_lvs_json_errors():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return('{')

    with pytest.raises(ValueError):
        assert module.get_snapshots('lvs')


def test_get_snapshots_with_lvs_json_missing_report_errors():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return(
        '''
          {
              "report": [],
              "log": [
              ]
          }
        '''
    )

    with pytest.raises(ValueError):
        assert module.get_snapshots('lvs')


def test_get_snapshots_with_lvs_json_missing_keys_errors():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return(
        '''
          {
              "report": [
                  {
                      "lv": [
                          {}
                      ]
                  }
              ],
              "log": [
              ]
          }
        '''
    )

    with pytest.raises(ValueError):
        assert module.get_snapshots('lvs')


def test_remove_data_source_dumps_unmounts_and_remove_snapshots():
    config = {'lvm': {}}
    flexmock(module).should_receive('get_logical_volumes').and_return(
        (
            module.Logical_volume(
                name='lvolume1',
                device_path='/dev/lvolume1',
                mount_point='/mnt/lvolume1',
                contained_source_directories=('/mnt/lvolume1/subdir',),
            ),
            module.Logical_volume(
                name='lvolume2',
                device_path='/dev/lvolume2',
                mount_point='/mnt/lvolume2',
                contained_source_directories=('/mnt/lvolume2',),
            ),
        )
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(lambda path: [path])
    flexmock(module.os.path).should_receive('isdir').and_return(True)
    flexmock(module.shutil).should_receive('rmtree')
    flexmock(module).should_receive('unmount_snapshot').with_args(
        'umount',
        '/run/borgmatic/lvm_snapshots/mnt/lvolume1',
    ).once()
    flexmock(module).should_receive('unmount_snapshot').with_args(
        'umount',
        '/run/borgmatic/lvm_snapshots/mnt/lvolume2',
    ).once()
    flexmock(module).should_receive('get_snapshots').and_return(
        (
            module.Snapshot('lvolume1_borgmatic-1234', '/dev/lvolume1'),
            module.Snapshot('lvolume2_borgmatic-1234', '/dev/lvolume2'),
            module.Snapshot('nonborgmatic', '/dev/nonborgmatic'),
        ),
    )
    flexmock(module).should_receive('remove_snapshot').with_args('lvremove', '/dev/lvolume1').once()
    flexmock(module).should_receive('remove_snapshot').with_args('lvremove', '/dev/lvolume2').once()
    flexmock(module).should_receive('remove_snapshot').with_args(
        'nonborgmatic', '/dev/nonborgmatic'
    ).never()

    module.remove_data_source_dumps(
        hook_config=config['lvm'],
        config=config,
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_bails_for_missing_lsblk_command():
    config = {'lvm': {}}
    flexmock(module).should_receive('get_logical_volumes').and_raise(FileNotFoundError)
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).never()
    flexmock(module).should_receive('unmount_snapshot').never()
    flexmock(module).should_receive('remove_snapshot').never()

    module.remove_data_source_dumps(
        hook_config=config['lvm'],
        config=config,
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_bails_for_lsblk_command_error():
    config = {'lvm': {}}
    flexmock(module).should_receive('get_logical_volumes').and_raise(
        module.subprocess.CalledProcessError(1, 'wtf')
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).never()
    flexmock(module).should_receive('unmount_snapshot').never()
    flexmock(module).should_receive('remove_snapshot').never()

    module.remove_data_source_dumps(
        hook_config=config['lvm'],
        config=config,
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_with_missing_snapshot_directory_skips_unmount():
    config = {'lvm': {}}
    flexmock(module).should_receive('get_logical_volumes').and_return(
        (
            module.Logical_volume(
                name='lvolume1',
                device_path='/dev/lvolume1',
                mount_point='/mnt/lvolume1',
                contained_source_directories=('/mnt/lvolume1/subdir',),
            ),
            module.Logical_volume(
                name='lvolume2',
                device_path='/dev/lvolume2',
                mount_point='/mnt/lvolume2',
                contained_source_directories=('/mnt/lvolume2',),
            ),
        )
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(lambda path: [path])
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/run/borgmatic/lvm_snapshots'
    ).and_return(False)
    flexmock(module.shutil).should_receive('rmtree').never()
    flexmock(module).should_receive('unmount_snapshot').never()
    flexmock(module).should_receive('get_snapshots').and_return(
        (
            module.Snapshot('lvolume1_borgmatic-1234', '/dev/lvolume1'),
            module.Snapshot('lvolume2_borgmatic-1234', '/dev/lvolume2'),
        ),
    )
    flexmock(module).should_receive('remove_snapshot').with_args('lvremove', '/dev/lvolume1').once()
    flexmock(module).should_receive('remove_snapshot').with_args('lvremove', '/dev/lvolume2').once()

    module.remove_data_source_dumps(
        hook_config=config['lvm'],
        config=config,
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_with_missing_snapshot_mount_path_skips_unmount():
    config = {'lvm': {}}
    flexmock(module).should_receive('get_logical_volumes').and_return(
        (
            module.Logical_volume(
                name='lvolume1',
                device_path='/dev/lvolume1',
                mount_point='/mnt/lvolume1',
                contained_source_directories=('/mnt/lvolume1/subdir',),
            ),
            module.Logical_volume(
                name='lvolume2',
                device_path='/dev/lvolume2',
                mount_point='/mnt/lvolume2',
                contained_source_directories=('/mnt/lvolume2',),
            ),
        )
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(lambda path: [path])
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/run/borgmatic/lvm_snapshots'
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/run/borgmatic/lvm_snapshots/mnt/lvolume1'
    ).and_return(False)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/run/borgmatic/lvm_snapshots/mnt/lvolume2'
    ).and_return(True)
    flexmock(module.shutil).should_receive('rmtree')
    flexmock(module).should_receive('unmount_snapshot').with_args(
        'umount',
        '/run/borgmatic/lvm_snapshots/mnt/lvolume1',
    ).never()
    flexmock(module).should_receive('unmount_snapshot').with_args(
        'umount',
        '/run/borgmatic/lvm_snapshots/mnt/lvolume2',
    ).once()
    flexmock(module).should_receive('get_snapshots').and_return(
        (
            module.Snapshot('lvolume1_borgmatic-1234', '/dev/lvolume1'),
            module.Snapshot('lvolume2_borgmatic-1234', '/dev/lvolume2'),
        ),
    )
    flexmock(module).should_receive('remove_snapshot').with_args('lvremove', '/dev/lvolume1').once()
    flexmock(module).should_receive('remove_snapshot').with_args('lvremove', '/dev/lvolume2').once()

    module.remove_data_source_dumps(
        hook_config=config['lvm'],
        config=config,
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_with_successful_mount_point_removal_skips_unmount():
    config = {'lvm': {}}
    flexmock(module).should_receive('get_logical_volumes').and_return(
        (
            module.Logical_volume(
                name='lvolume1',
                device_path='/dev/lvolume1',
                mount_point='/mnt/lvolume1',
                contained_source_directories=('/mnt/lvolume1/subdir',),
            ),
            module.Logical_volume(
                name='lvolume2',
                device_path='/dev/lvolume2',
                mount_point='/mnt/lvolume2',
                contained_source_directories=('/mnt/lvolume2',),
            ),
        )
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(lambda path: [path])
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/run/borgmatic/lvm_snapshots'
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/run/borgmatic/lvm_snapshots/mnt/lvolume1'
    ).and_return(True).and_return(False)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/run/borgmatic/lvm_snapshots/mnt/lvolume2'
    ).and_return(True).and_return(True)
    flexmock(module.shutil).should_receive('rmtree')
    flexmock(module).should_receive('unmount_snapshot').with_args(
        'umount',
        '/run/borgmatic/lvm_snapshots/mnt/lvolume1',
    ).never()
    flexmock(module).should_receive('unmount_snapshot').with_args(
        'umount',
        '/run/borgmatic/lvm_snapshots/mnt/lvolume2',
    ).once()
    flexmock(module).should_receive('get_snapshots').and_return(
        (
            module.Snapshot('lvolume1_borgmatic-1234', '/dev/lvolume1'),
            module.Snapshot('lvolume2_borgmatic-1234', '/dev/lvolume2'),
        ),
    )
    flexmock(module).should_receive('remove_snapshot').with_args('lvremove', '/dev/lvolume1').once()
    flexmock(module).should_receive('remove_snapshot').with_args('lvremove', '/dev/lvolume2').once()

    module.remove_data_source_dumps(
        hook_config=config['lvm'],
        config=config,
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_bails_for_missing_umount_command():
    config = {'lvm': {}}
    flexmock(module).should_receive('get_logical_volumes').and_return(
        (
            module.Logical_volume(
                name='lvolume1',
                device_path='/dev/lvolume1',
                mount_point='/mnt/lvolume1',
                contained_source_directories=('/mnt/lvolume1/subdir',),
            ),
            module.Logical_volume(
                name='lvolume2',
                device_path='/dev/lvolume2',
                mount_point='/mnt/lvolume2',
                contained_source_directories=('/mnt/lvolume2',),
            ),
        )
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(lambda path: [path])
    flexmock(module.os.path).should_receive('isdir').and_return(True)
    flexmock(module.shutil).should_receive('rmtree')
    flexmock(module).should_receive('unmount_snapshot').with_args(
        'umount',
        '/run/borgmatic/lvm_snapshots/mnt/lvolume1',
    ).and_raise(FileNotFoundError)
    flexmock(module).should_receive('unmount_snapshot').with_args(
        'umount',
        '/run/borgmatic/lvm_snapshots/mnt/lvolume2',
    ).never()
    flexmock(module).should_receive('get_snapshots').never()
    flexmock(module).should_receive('remove_snapshot').never()

    module.remove_data_source_dumps(
        hook_config=config['lvm'],
        config=config,
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_bails_for_umount_command_error():
    config = {'lvm': {}}
    flexmock(module).should_receive('get_logical_volumes').and_return(
        (
            module.Logical_volume(
                name='lvolume1',
                device_path='/dev/lvolume1',
                mount_point='/mnt/lvolume1',
                contained_source_directories=('/mnt/lvolume1/subdir',),
            ),
            module.Logical_volume(
                name='lvolume2',
                device_path='/dev/lvolume2',
                mount_point='/mnt/lvolume2',
                contained_source_directories=('/mnt/lvolume2',),
            ),
        )
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(lambda path: [path])
    flexmock(module.os.path).should_receive('isdir').and_return(True)
    flexmock(module.shutil).should_receive('rmtree')
    flexmock(module).should_receive('unmount_snapshot').with_args(
        'umount',
        '/run/borgmatic/lvm_snapshots/mnt/lvolume1',
    ).and_raise(module.subprocess.CalledProcessError(1, 'wtf'))
    flexmock(module).should_receive('unmount_snapshot').with_args(
        'umount',
        '/run/borgmatic/lvm_snapshots/mnt/lvolume2',
    ).never()
    flexmock(module).should_receive('get_snapshots').never()
    flexmock(module).should_receive('remove_snapshot').never()

    module.remove_data_source_dumps(
        hook_config=config['lvm'],
        config=config,
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_bails_for_missing_lvs_command():
    config = {'lvm': {}}
    flexmock(module).should_receive('get_logical_volumes').and_return(
        (
            module.Logical_volume(
                name='lvolume1',
                device_path='/dev/lvolume1',
                mount_point='/mnt/lvolume1',
                contained_source_directories=('/mnt/lvolume1/subdir',),
            ),
            module.Logical_volume(
                name='lvolume2',
                device_path='/dev/lvolume2',
                mount_point='/mnt/lvolume2',
                contained_source_directories=('/mnt/lvolume2',),
            ),
        )
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(lambda path: [path])
    flexmock(module.os.path).should_receive('isdir').and_return(True)
    flexmock(module.shutil).should_receive('rmtree')
    flexmock(module).should_receive('unmount_snapshot').with_args(
        'umount',
        '/run/borgmatic/lvm_snapshots/mnt/lvolume1',
    ).once()
    flexmock(module).should_receive('unmount_snapshot').with_args(
        'umount',
        '/run/borgmatic/lvm_snapshots/mnt/lvolume2',
    ).once()
    flexmock(module).should_receive('get_snapshots').and_raise(FileNotFoundError)
    flexmock(module).should_receive('remove_snapshot').never()

    module.remove_data_source_dumps(
        hook_config=config['lvm'],
        config=config,
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_bails_for_lvs_command_error():
    config = {'lvm': {}}
    flexmock(module).should_receive('get_logical_volumes').and_return(
        (
            module.Logical_volume(
                name='lvolume1',
                device_path='/dev/lvolume1',
                mount_point='/mnt/lvolume1',
                contained_source_directories=('/mnt/lvolume1/subdir',),
            ),
            module.Logical_volume(
                name='lvolume2',
                device_path='/dev/lvolume2',
                mount_point='/mnt/lvolume2',
                contained_source_directories=('/mnt/lvolume2',),
            ),
        )
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(lambda path: [path])
    flexmock(module.os.path).should_receive('isdir').and_return(True)
    flexmock(module.shutil).should_receive('rmtree')
    flexmock(module).should_receive('unmount_snapshot').with_args(
        'umount',
        '/run/borgmatic/lvm_snapshots/mnt/lvolume1',
    ).once()
    flexmock(module).should_receive('unmount_snapshot').with_args(
        'umount',
        '/run/borgmatic/lvm_snapshots/mnt/lvolume2',
    ).once()
    flexmock(module).should_receive('get_snapshots').and_raise(
        module.subprocess.CalledProcessError(1, 'wtf')
    )
    flexmock(module).should_receive('remove_snapshot').never()

    module.remove_data_source_dumps(
        hook_config=config['lvm'],
        config=config,
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_with_dry_run_skips_snapshot_unmount_and_delete():
    config = {'lvm': {}}
    flexmock(module).should_receive('get_logical_volumes').and_return(
        (
            module.Logical_volume(
                name='lvolume1',
                device_path='/dev/lvolume1',
                mount_point='/mnt/lvolume1',
                contained_source_directories=('/mnt/lvolume1/subdir',),
            ),
            module.Logical_volume(
                name='lvolume2',
                device_path='/dev/lvolume2',
                mount_point='/mnt/lvolume2',
                contained_source_directories=('/mnt/lvolume2',),
            ),
        )
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(lambda path: [path])
    flexmock(module.os.path).should_receive('isdir').and_return(True)
    flexmock(module.shutil).should_receive('rmtree').never()
    flexmock(module).should_receive('unmount_snapshot').never()
    flexmock(module).should_receive('get_snapshots').and_return(
        (
            module.Snapshot('lvolume1_borgmatic-1234', '/dev/lvolume1'),
            module.Snapshot('lvolume2_borgmatic-1234', '/dev/lvolume2'),
            module.Snapshot('nonborgmatic', '/dev/nonborgmatic'),
        ),
    ).once()
    flexmock(module).should_receive('remove_snapshot').never()

    module.remove_data_source_dumps(
        hook_config=config['lvm'],
        config=config,
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=True,
    )
