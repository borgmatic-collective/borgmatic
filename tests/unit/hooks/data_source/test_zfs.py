import os

import pytest
from flexmock import flexmock

from borgmatic.hooks.data_source import zfs as module


def test_get_datasets_to_backup_filters_datasets_by_source_directories():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return(
        'dataset\t/dataset\t-\nother\t/other\t-',
    )
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_directories'
    ).with_args('/dataset', object).and_return(('/dataset',))
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_directories'
    ).with_args('/other', object).and_return(())

    assert module.get_datasets_to_backup(
        'zfs', source_directories=('/foo', '/dataset', '/bar')
    ) == (
        module.Dataset(
            name='dataset', mount_point='/dataset', contained_source_directories=('/dataset',)
        ),
    )


def test_get_datasets_to_backup_filters_datasets_by_user_property():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return(
        'dataset\t/dataset\tauto\nother\t/other\t-',
    )
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_directories'
    ).with_args('/dataset', object).never()
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_directories'
    ).with_args('/other', object).and_return(())

    assert module.get_datasets_to_backup('zfs', source_directories=('/foo', '/bar')) == (
        module.Dataset(
            name='dataset',
            mount_point='/dataset',
            auto_backup=True,
            contained_source_directories=('/dataset',),
        ),
    )


def test_get_datasets_to_backup_with_invalid_list_output_raises():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return(
        'dataset',
    )
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_directories'
    ).never()

    with pytest.raises(ValueError, match='zfs'):
        module.get_datasets_to_backup('zfs', source_directories=('/foo', '/bar'))


def test_get_all_dataset_mount_points_does_not_filter_datasets():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return(
        '/dataset\n/other',
    )
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_directories'
    ).and_return(('/dataset',))

    assert module.get_all_dataset_mount_points('zfs') == (
        ('/dataset'),
        ('/other'),
    )


def test_dump_data_sources_snapshots_and_mounts_and_updates_source_directories():
    flexmock(module).should_receive('get_datasets_to_backup').and_return(
        (
            flexmock(
                name='dataset',
                mount_point='/mnt/dataset',
                contained_source_directories=('/mnt/dataset/subdir',),
            )
        )
    )
    flexmock(module.os).should_receive('getpid').and_return(1234)
    full_snapshot_name = 'dataset@borgmatic-1234'
    flexmock(module).should_receive('snapshot_dataset').with_args(
        'zfs',
        full_snapshot_name,
    ).once()
    snapshot_mount_path = '/run/borgmatic/zfs_snapshots/./mnt/dataset'
    flexmock(module).should_receive('mount_snapshot').with_args(
        'mount',
        full_snapshot_name,
        module.os.path.normpath(snapshot_mount_path),
    ).once()
    source_directories = ['/mnt/dataset/subdir']

    assert (
        module.dump_data_sources(
            hook_config={},
            config={'source_directories': '/mnt/dataset', 'zfs': {}},
            log_prefix='test',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            source_directories=source_directories,
            dry_run=False,
        )
        == []
    )

    assert source_directories == [os.path.join(snapshot_mount_path, 'subdir')]


def test_dump_data_sources_snapshots_with_no_datasets_skips_snapshots():
    flexmock(module).should_receive('get_datasets_to_backup').and_return(())
    flexmock(module.os).should_receive('getpid').and_return(1234)
    flexmock(module).should_receive('snapshot_dataset').never()
    flexmock(module).should_receive('mount_snapshot').never()
    source_directories = ['/mnt/dataset']

    assert (
        module.dump_data_sources(
            hook_config={},
            config={'source_directories': '/mnt/dataset', 'zfs': {}},
            log_prefix='test',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            source_directories=source_directories,
            dry_run=False,
        )
        == []
    )

    assert source_directories == ['/mnt/dataset']


def test_dump_data_sources_uses_custom_commands():
    flexmock(module).should_receive('get_datasets_to_backup').and_return(
        (
            flexmock(
                name='dataset',
                mount_point='/mnt/dataset',
                contained_source_directories=('/mnt/dataset/subdir',),
            )
        )
    )
    flexmock(module.os).should_receive('getpid').and_return(1234)
    full_snapshot_name = 'dataset@borgmatic-1234'
    flexmock(module).should_receive('snapshot_dataset').with_args(
        '/usr/local/bin/zfs',
        full_snapshot_name,
    ).once()
    snapshot_mount_path = '/run/borgmatic/zfs_snapshots/./mnt/dataset'
    flexmock(module).should_receive('mount_snapshot').with_args(
        '/usr/local/bin/mount',
        full_snapshot_name,
        module.os.path.normpath(snapshot_mount_path),
    ).once()
    source_directories = ['/mnt/dataset/subdir']
    hook_config = {
        'zfs_command': '/usr/local/bin/zfs',
        'mount_command': '/usr/local/bin/mount',
    }

    assert (
        module.dump_data_sources(
            hook_config=hook_config,
            config={
                'source_directories': source_directories,
                'zfs': hook_config,
            },
            log_prefix='test',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            source_directories=source_directories,
            dry_run=False,
        )
        == []
    )

    assert source_directories == [os.path.join(snapshot_mount_path, 'subdir')]


def test_dump_data_sources_with_dry_run_skips_commands_and_does_not_touch_source_directories():
    flexmock(module).should_receive('get_datasets_to_backup').and_return(
        (flexmock(name='dataset', mount_point='/mnt/dataset'),)
    )
    flexmock(module.os).should_receive('getpid').and_return(1234)
    flexmock(module).should_receive('snapshot_dataset').never()
    flexmock(module).should_receive('mount_snapshot').never()
    source_directories = ['/mnt/dataset']

    assert (
        module.dump_data_sources(
            hook_config={},
            config={'source_directories': '/mnt/dataset', 'zfs': {}},
            log_prefix='test',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            source_directories=source_directories,
            dry_run=True,
        )
        == []
    )

    assert source_directories == ['/mnt/dataset']


def test_dump_data_sources_ignores_mismatch_between_source_directories_and_contained_source_directories():
    flexmock(module).should_receive('get_datasets_to_backup').and_return(
        (
            flexmock(
                name='dataset',
                mount_point='/mnt/dataset',
                contained_source_directories=('/mnt/dataset/subdir',),
            )
        )
    )
    flexmock(module.os).should_receive('getpid').and_return(1234)
    full_snapshot_name = 'dataset@borgmatic-1234'
    flexmock(module).should_receive('snapshot_dataset').with_args(
        'zfs',
        full_snapshot_name,
    ).once()
    snapshot_mount_path = '/run/borgmatic/zfs_snapshots/./mnt/dataset'
    flexmock(module).should_receive('mount_snapshot').with_args(
        'mount',
        full_snapshot_name,
        module.os.path.normpath(snapshot_mount_path),
    ).once()
    source_directories = ['/hmm']

    assert (
        module.dump_data_sources(
            hook_config={},
            config={'source_directories': '/mnt/dataset', 'zfs': {}},
            log_prefix='test',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            source_directories=source_directories,
            dry_run=False,
        )
        == []
    )

    assert source_directories == ['/hmm', os.path.join(snapshot_mount_path, 'subdir')]


def test_get_all_snapshots_parses_list_output():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return(
        'dataset1@borgmatic-1234\ndataset2@borgmatic-4567',
    )

    assert module.get_all_snapshots('zfs') == ('dataset1@borgmatic-1234', 'dataset2@borgmatic-4567')


def test_remove_data_source_dumps_unmounts_and_destroys_snapshots():
    flexmock(module).should_receive('get_all_dataset_mount_points').and_return(('/mnt/dataset',))
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(lambda path: [path])
    flexmock(module.os.path).should_receive('isdir').and_return(True)
    flexmock(module.shutil).should_receive('rmtree')
    flexmock(module).should_receive('unmount_snapshot').with_args(
        'umount', '/run/borgmatic/zfs_snapshots/mnt/dataset'
    ).once()
    flexmock(module).should_receive('get_all_snapshots').and_return(
        ('dataset@borgmatic-1234', 'dataset@other', 'other@other', 'invalid')
    )
    flexmock(module).should_receive('destroy_snapshot').with_args(
        'zfs', 'dataset@borgmatic-1234'
    ).once()

    module.remove_data_source_dumps(
        hook_config={},
        config={'source_directories': '/mnt/dataset', 'zfs': {}},
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_use_custom_commands():
    flexmock(module).should_receive('get_all_dataset_mount_points').and_return(('/mnt/dataset',))
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(lambda path: [path])
    flexmock(module.os.path).should_receive('isdir').and_return(True)
    flexmock(module.shutil).should_receive('rmtree')
    flexmock(module).should_receive('unmount_snapshot').with_args(
        '/usr/local/bin/umount', '/run/borgmatic/zfs_snapshots/mnt/dataset'
    ).once()
    flexmock(module).should_receive('get_all_snapshots').and_return(
        ('dataset@borgmatic-1234', 'dataset@other', 'other@other', 'invalid')
    )
    flexmock(module).should_receive('destroy_snapshot').with_args(
        '/usr/local/bin/zfs', 'dataset@borgmatic-1234'
    ).once()
    hook_config = {'zfs_command': '/usr/local/bin/zfs', 'umount_command': '/usr/local/bin/umount'}

    module.remove_data_source_dumps(
        hook_config=hook_config,
        config={'source_directories': '/mnt/dataset', 'zfs': hook_config},
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_bails_for_missing_zfs_command():
    flexmock(module).should_receive('get_all_dataset_mount_points').and_raise(FileNotFoundError)
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).never()
    hook_config = {'zfs_command': 'wtf'}

    module.remove_data_source_dumps(
        hook_config=hook_config,
        config={'source_directories': '/mnt/dataset', 'zfs': hook_config},
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_bails_for_zfs_command_error():
    flexmock(module).should_receive('get_all_dataset_mount_points').and_raise(
        module.subprocess.CalledProcessError(1, 'wtf')
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).never()
    hook_config = {'zfs_command': 'wtf'}

    module.remove_data_source_dumps(
        hook_config=hook_config,
        config={'source_directories': '/mnt/dataset', 'zfs': hook_config},
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_bails_for_missing_umount_command():
    flexmock(module).should_receive('get_all_dataset_mount_points').and_return(('/mnt/dataset',))
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(lambda path: [path])
    flexmock(module.os.path).should_receive('isdir').and_return(True)
    flexmock(module.shutil).should_receive('rmtree')
    flexmock(module).should_receive('unmount_snapshot').with_args(
        '/usr/local/bin/umount', '/run/borgmatic/zfs_snapshots/mnt/dataset'
    ).and_raise(FileNotFoundError)
    flexmock(module).should_receive('get_all_snapshots').never()
    flexmock(module).should_receive('destroy_snapshot').never()
    hook_config = {'zfs_command': '/usr/local/bin/zfs', 'umount_command': '/usr/local/bin/umount'}

    module.remove_data_source_dumps(
        hook_config=hook_config,
        config={'source_directories': '/mnt/dataset', 'zfs': hook_config},
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_bails_for_umount_command_error():
    flexmock(module).should_receive('get_all_dataset_mount_points').and_return(('/mnt/dataset',))
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(lambda path: [path])
    flexmock(module.os.path).should_receive('isdir').and_return(True)
    flexmock(module.shutil).should_receive('rmtree')
    flexmock(module).should_receive('unmount_snapshot').with_args(
        '/usr/local/bin/umount', '/run/borgmatic/zfs_snapshots/mnt/dataset'
    ).and_raise(module.subprocess.CalledProcessError(1, 'wtf'))
    flexmock(module).should_receive('get_all_snapshots').never()
    flexmock(module).should_receive('destroy_snapshot').never()
    hook_config = {'zfs_command': '/usr/local/bin/zfs', 'umount_command': '/usr/local/bin/umount'}

    module.remove_data_source_dumps(
        hook_config=hook_config,
        config={'source_directories': '/mnt/dataset', 'zfs': hook_config},
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_skips_unmount_snapshot_directories_that_are_not_actually_directories():
    flexmock(module).should_receive('get_all_dataset_mount_points').and_return(('/mnt/dataset',))
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(lambda path: [path])
    flexmock(module.os.path).should_receive('isdir').and_return(False)
    flexmock(module.shutil).should_receive('rmtree').never()
    flexmock(module).should_receive('unmount_snapshot').never()
    flexmock(module).should_receive('get_all_snapshots').and_return(
        ('dataset@borgmatic-1234', 'dataset@other', 'other@other', 'invalid')
    )
    flexmock(module).should_receive('destroy_snapshot').with_args(
        'zfs', 'dataset@borgmatic-1234'
    ).once()

    module.remove_data_source_dumps(
        hook_config={},
        config={'source_directories': '/mnt/dataset', 'zfs': {}},
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_skips_unmount_snapshot_mount_paths_that_are_not_actually_directories():
    flexmock(module).should_receive('get_all_dataset_mount_points').and_return(('/mnt/dataset',))
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(lambda path: [path])
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/run/borgmatic/zfs_snapshots'
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/run/borgmatic/zfs_snapshots/mnt/dataset'
    ).and_return(False)
    flexmock(module.shutil).should_receive('rmtree')
    flexmock(module).should_receive('unmount_snapshot').never()
    flexmock(module).should_receive('get_all_snapshots').and_return(
        ('dataset@borgmatic-1234', 'dataset@other', 'other@other', 'invalid')
    )
    flexmock(module).should_receive('destroy_snapshot').with_args(
        'zfs', 'dataset@borgmatic-1234'
    ).once()

    module.remove_data_source_dumps(
        hook_config={},
        config={'source_directories': '/mnt/dataset', 'zfs': {}},
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_skips_unmount_snapshot_mount_paths_after_rmtree_succeeds():
    flexmock(module).should_receive('get_all_dataset_mount_points').and_return(('/mnt/dataset',))
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(lambda path: [path])
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/run/borgmatic/zfs_snapshots'
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/run/borgmatic/zfs_snapshots/mnt/dataset'
    ).and_return(True).and_return(False)
    flexmock(module.shutil).should_receive('rmtree')
    flexmock(module).should_receive('unmount_snapshot').never()
    flexmock(module).should_receive('get_all_snapshots').and_return(
        ('dataset@borgmatic-1234', 'dataset@other', 'other@other', 'invalid')
    )
    flexmock(module).should_receive('destroy_snapshot').with_args(
        'zfs', 'dataset@borgmatic-1234'
    ).once()

    module.remove_data_source_dumps(
        hook_config={},
        config={'source_directories': '/mnt/dataset', 'zfs': {}},
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_with_dry_run_skips_unmount_and_destroy():
    flexmock(module).should_receive('get_all_dataset_mount_points').and_return(('/mnt/dataset',))
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(lambda path: [path])
    flexmock(module.os.path).should_receive('isdir').and_return(True)
    flexmock(module.shutil).should_receive('rmtree').never()
    flexmock(module).should_receive('unmount_snapshot').never()
    flexmock(module).should_receive('get_all_snapshots').and_return(
        ('dataset@borgmatic-1234', 'dataset@other', 'other@other', 'invalid')
    )
    flexmock(module).should_receive('destroy_snapshot').never()

    module.remove_data_source_dumps(
        hook_config={},
        config={'source_directories': '/mnt/dataset', 'zfs': {}},
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=True,
    )
