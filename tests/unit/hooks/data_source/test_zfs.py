import os

import pytest
from flexmock import flexmock

from borgmatic.borg.pattern import Pattern, Pattern_source, Pattern_style, Pattern_type
from borgmatic.hooks.data_source import zfs as module


def test_get_datasets_to_backup_filters_datasets_by_patterns():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_return(
        'dataset\t/dataset\ton\t-\nother\t/other\ton\t-',
    )
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_patterns',
    ).with_args('/dataset', object).and_return(
        (
            Pattern(
                '/dataset',
                Pattern_type.ROOT,
                source=Pattern_source.CONFIG,
            ),
        ),
    )
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_patterns',
    ).with_args('/other', object).and_return(())

    assert module.get_datasets_to_backup(
        'zfs',
        patterns=(
            Pattern(
                '/foo',
                Pattern_type.ROOT,
                source=Pattern_source.CONFIG,
            ),
            Pattern(
                '/dataset',
                Pattern_type.ROOT,
                source=Pattern_source.CONFIG,
            ),
            Pattern(
                '/bar',
                Pattern_type.ROOT,
                source=Pattern_source.CONFIG,
            ),
        ),
    ) == (
        module.Dataset(
            name='dataset',
            mount_point='/dataset',
            contained_patterns=(
                Pattern(
                    '/dataset',
                    Pattern_type.ROOT,
                    source=Pattern_source.CONFIG,
                ),
            ),
        ),
    )


def test_get_datasets_to_backup_skips_non_root_patterns():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_return(
        'dataset\t/dataset\ton\t-\nother\t/other\ton\t-',
    )
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_patterns',
    ).with_args('/dataset', object).and_return(
        (
            Pattern(
                '/dataset',
                Pattern_type.EXCLUDE,
                source=Pattern_source.CONFIG,
            ),
        ),
    )
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_patterns',
    ).with_args('/other', object).and_return(())

    assert (
        module.get_datasets_to_backup(
            'zfs',
            patterns=(
                Pattern(
                    '/foo',
                    Pattern_type.ROOT,
                    source=Pattern_source.CONFIG,
                ),
                Pattern(
                    '/dataset',
                    Pattern_type.EXCLUDE,
                    source=Pattern_source.CONFIG,
                ),
                Pattern(
                    '/bar',
                    Pattern_type.ROOT,
                    source=Pattern_source.CONFIG,
                ),
            ),
        )
        == ()
    )


def test_get_datasets_to_backup_skips_non_config_patterns():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_return(
        'dataset\t/dataset\ton\t-\nother\t/other\ton\t-',
    )
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_patterns',
    ).with_args('/dataset', object).and_return(
        (
            Pattern(
                '/dataset',
                Pattern_type.ROOT,
                source=Pattern_source.HOOK,
            ),
        ),
    )
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_patterns',
    ).with_args('/other', object).and_return(())

    assert (
        module.get_datasets_to_backup(
            'zfs',
            patterns=(
                Pattern(
                    '/foo',
                    Pattern_type.ROOT,
                    source=Pattern_source.CONFIG,
                ),
                Pattern(
                    '/dataset',
                    Pattern_type.ROOT,
                    source=Pattern_source.HOOK,
                ),
                Pattern(
                    '/bar',
                    Pattern_type.ROOT,
                    source=Pattern_source.CONFIG,
                ),
            ),
        )
        == ()
    )


def test_get_datasets_to_backup_filters_datasets_by_user_property():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_return(
        'dataset\t/dataset\ton\tauto\nother\t/other\ton\t-',
    )
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_patterns',
    ).with_args('/dataset', object).and_return(())
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_patterns',
    ).with_args('/other', object).and_return(())

    assert module.get_datasets_to_backup(
        'zfs',
        patterns=(Pattern('/foo'), Pattern('/bar')),
    ) == (
        module.Dataset(
            name='dataset',
            mount_point='/dataset',
            auto_backup=True,
            contained_patterns=(Pattern('/dataset', source=Pattern_source.HOOK),),
        ),
    )


def test_get_datasets_to_backup_filters_datasets_by_canmount_property():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_return(
        'dataset\t/dataset\toff\t-\nother\t/other\ton\t-',
    )
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_patterns',
    ).with_args('/dataset', object).and_return((Pattern('/dataset'),))
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_patterns',
    ).with_args('/other', object).and_return(())

    assert (
        module.get_datasets_to_backup(
            'zfs',
            patterns=(
                Pattern('/foo'),
                Pattern('/dataset'),
                Pattern('/bar'),
            ),
        )
        == ()
    )


def test_get_datasets_to_backup_with_invalid_list_output_raises():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_return(
        'dataset',
    )
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_patterns',
    ).never()

    with pytest.raises(ValueError, match='zfs'):
        module.get_datasets_to_backup('zfs', patterns=(Pattern('/foo'), Pattern('/bar')))


def test_get_all_dataset_mount_points_omits_none():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_return(
        '/dataset\nnone\n/other',
    )
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_patterns',
    ).and_return((Pattern('/dataset'),))

    assert module.get_all_dataset_mount_points('zfs') == (
        ('/dataset'),
        ('/other'),
    )


def test_get_all_dataset_mount_points_omits_duplicates():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_return(
        '/dataset\n/other\n/dataset\n/other',
    )
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_patterns',
    ).and_return((Pattern('/dataset'),))

    assert module.get_all_dataset_mount_points('zfs') == (
        ('/dataset'),
        ('/other'),
    )


@pytest.mark.parametrize(
    'pattern,expected_pattern',
    (
        (
            Pattern('/foo/bar/baz'),
            Pattern('/run/borgmatic/zfs_snapshots/b33f/./foo/bar/baz'),
        ),
        (Pattern('/foo/bar'), Pattern('/run/borgmatic/zfs_snapshots/b33f/./foo/bar')),
        (
            Pattern('^/foo/bar', Pattern_type.INCLUDE, Pattern_style.REGULAR_EXPRESSION),
            Pattern(
                '^/run/borgmatic/zfs_snapshots/b33f/./foo/bar',
                Pattern_type.INCLUDE,
                Pattern_style.REGULAR_EXPRESSION,
            ),
        ),
        (
            Pattern('/foo/bar', Pattern_type.INCLUDE, Pattern_style.REGULAR_EXPRESSION),
            Pattern(
                '/run/borgmatic/zfs_snapshots/b33f/./foo/bar',
                Pattern_type.INCLUDE,
                Pattern_style.REGULAR_EXPRESSION,
            ),
        ),
        (Pattern('/foo'), Pattern('/run/borgmatic/zfs_snapshots/b33f/./foo')),
        (Pattern('/'), Pattern('/run/borgmatic/zfs_snapshots/b33f/./')),
        (
            Pattern('/foo/./bar/baz'),
            Pattern('/run/borgmatic/zfs_snapshots/b33f/foo/./bar/baz'),
        ),
    ),
)
def test_make_borg_snapshot_pattern_includes_slashdot_hack_and_stripped_pattern_path(
    pattern,
    expected_pattern,
):
    flexmock(module.hashlib).should_receive('shake_256').and_return(
        flexmock(hexdigest=lambda length: 'b33f'),
    )

    assert (
        module.make_borg_snapshot_pattern(
            pattern,
            flexmock(mount_point='/something'),
            '/run/borgmatic',
        )
        == expected_pattern
    )


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
    flexmock(module).should_receive('make_borg_snapshot_pattern').with_args(
        Pattern('/mnt/dataset/subdir'),
        dataset,
        '/run/borgmatic',
    ).and_return(Pattern('/run/borgmatic/zfs_snapshots/b33f/./mnt/dataset/subdir'))
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

    assert patterns == [Pattern(os.path.join(snapshot_mount_path, 'subdir'))]


def test_dump_data_sources_with_no_datasets_skips_snapshots():
    flexmock(module).should_receive('get_datasets_to_backup').and_return(())
    flexmock(module.os).should_receive('getpid').and_return(1234)
    flexmock(module).should_receive('snapshot_dataset').never()
    flexmock(module).should_receive('mount_snapshot').never()
    patterns = [Pattern('/mnt/dataset')]

    assert (
        module.dump_data_sources(
            hook_config={},
            config={'patterns': flexmock(), 'zfs': {}},
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=patterns,
            dry_run=False,
        )
        == []
    )

    assert patterns == [Pattern('/mnt/dataset')]


def test_dump_data_sources_uses_custom_commands():
    dataset = flexmock(
        name='dataset',
        mount_point='/mnt/dataset',
        contained_patterns=(Pattern('/mnt/dataset/subdir'),),
    )
    flexmock(module).should_receive('get_datasets_to_backup').and_return((dataset,))
    flexmock(module.os).should_receive('getpid').and_return(1234)
    full_snapshot_name = 'dataset@borgmatic-1234'
    flexmock(module).should_receive('snapshot_dataset').with_args(
        '/usr/local/bin/zfs',
        full_snapshot_name,
    ).once()
    flexmock(module.hashlib).should_receive('shake_256').and_return(
        flexmock(hexdigest=lambda length: 'b33f'),
    )
    snapshot_mount_path = '/run/borgmatic/zfs_snapshots/b33f/./mnt/dataset'
    flexmock(module).should_receive('mount_snapshot').with_args(
        '/usr/local/bin/mount',
        full_snapshot_name,
        module.os.path.normpath(snapshot_mount_path),
    ).once()
    flexmock(module).should_receive('make_borg_snapshot_pattern').with_args(
        Pattern('/mnt/dataset/subdir'),
        dataset,
        '/run/borgmatic',
    ).and_return(Pattern('/run/borgmatic/zfs_snapshots/b33f/./mnt/dataset/subdir'))
    patterns = [Pattern('/mnt/dataset/subdir')]
    hook_config = {
        'zfs_command': '/usr/local/bin/zfs',
        'mount_command': '/usr/local/bin/mount',
    }

    assert (
        module.dump_data_sources(
            hook_config=hook_config,
            config={
                'patterns': flexmock(),
                'zfs': hook_config,
            },
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=patterns,
            dry_run=False,
        )
        == []
    )

    assert patterns == [Pattern(os.path.join(snapshot_mount_path, 'subdir'))]


def test_dump_data_sources_with_dry_run_skips_commands_and_does_not_touch_patterns():
    flexmock(module).should_receive('get_datasets_to_backup').and_return(
        (flexmock(name='dataset', mount_point='/mnt/dataset'),),
    )
    flexmock(module.os).should_receive('getpid').and_return(1234)
    flexmock(module).should_receive('snapshot_dataset').never()
    flexmock(module).should_receive('mount_snapshot').never()
    patterns = [Pattern('/mnt/dataset')]

    assert (
        module.dump_data_sources(
            hook_config={},
            config={'patterns': ('R /mnt/dataset',), 'zfs': {}},
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=patterns,
            dry_run=True,
        )
        == []
    )

    assert patterns == [Pattern('/mnt/dataset')]


def test_dump_data_sources_ignores_mismatch_between_given_patterns_and_contained_patterns():
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
    flexmock(module).should_receive('make_borg_snapshot_pattern').with_args(
        Pattern('/mnt/dataset/subdir'),
        dataset,
        '/run/borgmatic',
    ).and_return(Pattern('/run/borgmatic/zfs_snapshots/b33f/./mnt/dataset/subdir'))
    patterns = [Pattern('/hmm')]

    assert (
        module.dump_data_sources(
            hook_config={},
            config={'patterns': ('R /mnt/dataset',), 'zfs': {}},
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=patterns,
            dry_run=False,
        )
        == []
    )

    assert patterns == [Pattern('/hmm'), Pattern(os.path.join(snapshot_mount_path, 'subdir'))]


def test_get_all_snapshots_parses_list_output():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_return(
        'dataset1@borgmatic-1234\ndataset2@borgmatic-4567',
    )

    assert module.get_all_snapshots('zfs') == ('dataset1@borgmatic-1234', 'dataset2@borgmatic-4567')


def test_remove_data_source_dumps_unmounts_and_destroys_snapshots():
    flexmock(module).should_receive('get_all_dataset_mount_points').and_return(('/mnt/dataset',))
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(
        lambda path: [path.replace('*', 'b33f')],
    )
    flexmock(module.os.path).should_receive('isdir').and_return(True)
    flexmock(module.os).should_receive('listdir').and_return(['file.txt'])
    flexmock(module.shutil).should_receive('rmtree')
    flexmock(module).should_receive('unmount_snapshot').with_args(
        'umount',
        '/run/borgmatic/zfs_snapshots/b33f/mnt/dataset',
    ).once()
    flexmock(module).should_receive('get_all_snapshots').and_return(
        ('dataset@borgmatic-1234', 'dataset@other', 'other@other', 'invalid'),
    )
    flexmock(module).should_receive('destroy_snapshot').with_args(
        'zfs',
        'dataset@borgmatic-1234',
    ).once()

    module.remove_data_source_dumps(
        hook_config={},
        config={'source_directories': '/mnt/dataset', 'zfs': {}},
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_use_custom_commands():
    flexmock(module).should_receive('get_all_dataset_mount_points').and_return(('/mnt/dataset',))
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(
        lambda path: [path.replace('*', 'b33f')],
    )
    flexmock(module.os.path).should_receive('isdir').and_return(True)
    flexmock(module.os).should_receive('listdir').and_return(['file.txt'])
    flexmock(module.shutil).should_receive('rmtree')
    flexmock(module).should_receive('unmount_snapshot').with_args(
        '/usr/local/bin/umount',
        '/run/borgmatic/zfs_snapshots/b33f/mnt/dataset',
    ).once()
    flexmock(module).should_receive('get_all_snapshots').and_return(
        ('dataset@borgmatic-1234', 'dataset@other', 'other@other', 'invalid'),
    )
    flexmock(module).should_receive('destroy_snapshot').with_args(
        '/usr/local/bin/zfs',
        'dataset@borgmatic-1234',
    ).once()
    hook_config = {'zfs_command': '/usr/local/bin/zfs', 'umount_command': '/usr/local/bin/umount'}

    module.remove_data_source_dumps(
        hook_config=hook_config,
        config={'source_directories': '/mnt/dataset', 'zfs': hook_config},
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_bails_for_missing_hook_configuration():
    flexmock(module).should_receive('get_all_dataset_mount_points').never()
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).never()

    module.remove_data_source_dumps(
        hook_config=None,
        config={'source_directories': '/mnt/dataset'},
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_bails_for_missing_zfs_command():
    flexmock(module).should_receive('get_all_dataset_mount_points').and_raise(FileNotFoundError)
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).never()
    hook_config = {'zfs_command': 'wtf'}

    module.remove_data_source_dumps(
        hook_config=hook_config,
        config={'source_directories': '/mnt/dataset', 'zfs': hook_config},
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_bails_for_zfs_command_error():
    flexmock(module).should_receive('get_all_dataset_mount_points').and_raise(
        module.subprocess.CalledProcessError(1, 'wtf'),
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).never()
    hook_config = {'zfs_command': 'wtf'}

    module.remove_data_source_dumps(
        hook_config=hook_config,
        config={'source_directories': '/mnt/dataset', 'zfs': hook_config},
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_bails_for_missing_umount_command():
    flexmock(module).should_receive('get_all_dataset_mount_points').and_return(('/mnt/dataset',))
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(
        lambda path: [path.replace('*', 'b33f')],
    )
    flexmock(module.os.path).should_receive('isdir').and_return(True)
    flexmock(module.os).should_receive('listdir').and_return(['file.txt'])
    flexmock(module.shutil).should_receive('rmtree')
    flexmock(module).should_receive('unmount_snapshot').with_args(
        '/usr/local/bin/umount',
        '/run/borgmatic/zfs_snapshots/b33f/mnt/dataset',
    ).and_raise(FileNotFoundError)
    flexmock(module).should_receive('get_all_snapshots').never()
    flexmock(module).should_receive('destroy_snapshot').never()
    hook_config = {'zfs_command': '/usr/local/bin/zfs', 'umount_command': '/usr/local/bin/umount'}

    module.remove_data_source_dumps(
        hook_config=hook_config,
        config={'source_directories': '/mnt/dataset', 'zfs': hook_config},
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_swallows_umount_command_error():
    flexmock(module).should_receive('get_all_dataset_mount_points').and_return(('/mnt/dataset',))
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(
        lambda path: [path.replace('*', 'b33f')],
    )
    flexmock(module.os.path).should_receive('isdir').and_return(True)
    flexmock(module.os).should_receive('listdir').and_return(['file.txt'])
    flexmock(module.shutil).should_receive('rmtree')
    flexmock(module).should_receive('unmount_snapshot').with_args(
        '/usr/local/bin/umount',
        '/run/borgmatic/zfs_snapshots/b33f/mnt/dataset',
    ).and_raise(module.subprocess.CalledProcessError(1, 'wtf'))
    flexmock(module).should_receive('get_all_snapshots').and_return(
        ('dataset@borgmatic-1234', 'dataset@other', 'other@other', 'invalid'),
    )
    flexmock(module).should_receive('destroy_snapshot').with_args(
        '/usr/local/bin/zfs',
        'dataset@borgmatic-1234',
    ).once()
    hook_config = {'zfs_command': '/usr/local/bin/zfs', 'umount_command': '/usr/local/bin/umount'}

    module.remove_data_source_dumps(
        hook_config=hook_config,
        config={'source_directories': '/mnt/dataset', 'zfs': hook_config},
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_skips_unmount_snapshot_directories_that_are_not_actually_directories():
    flexmock(module).should_receive('get_all_dataset_mount_points').and_return(('/mnt/dataset',))
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(
        lambda path: [path.replace('*', 'b33f')],
    )
    flexmock(module.os.path).should_receive('isdir').and_return(False)
    flexmock(module.shutil).should_receive('rmtree').never()
    flexmock(module).should_receive('unmount_snapshot').never()
    flexmock(module).should_receive('get_all_snapshots').and_return(
        ('dataset@borgmatic-1234', 'dataset@other', 'other@other', 'invalid'),
    )
    flexmock(module).should_receive('destroy_snapshot').with_args(
        'zfs',
        'dataset@borgmatic-1234',
    ).once()

    module.remove_data_source_dumps(
        hook_config={},
        config={'source_directories': '/mnt/dataset', 'zfs': {}},
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_skips_unmount_snapshot_mount_paths_that_are_not_actually_directories():
    flexmock(module).should_receive('get_all_dataset_mount_points').and_return(('/mnt/dataset',))
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(
        lambda path: [path.replace('*', 'b33f')],
    )
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/run/borgmatic/zfs_snapshots/b33f',
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/run/borgmatic/zfs_snapshots/b33f/mnt/dataset',
    ).and_return(False)
    flexmock(module.os).should_receive('listdir').and_return(['file.txt'])
    flexmock(module.shutil).should_receive('rmtree')
    flexmock(module).should_receive('unmount_snapshot').never()
    flexmock(module).should_receive('get_all_snapshots').and_return(
        ('dataset@borgmatic-1234', 'dataset@other', 'other@other', 'invalid'),
    )
    flexmock(module).should_receive('destroy_snapshot').with_args(
        'zfs',
        'dataset@borgmatic-1234',
    ).once()

    module.remove_data_source_dumps(
        hook_config={},
        config={'source_directories': '/mnt/dataset', 'zfs': {}},
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_skips_unmount_snapshot_mount_paths_that_are_empty():
    flexmock(module).should_receive('get_all_dataset_mount_points').and_return(('/mnt/dataset',))
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(
        lambda path: [path.replace('*', 'b33f')],
    )
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/run/borgmatic/zfs_snapshots/b33f',
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/run/borgmatic/zfs_snapshots/b33f/mnt/dataset',
    ).and_return(True)
    flexmock(module.os).should_receive('listdir').with_args(
        '/run/borgmatic/zfs_snapshots/b33f/mnt/dataset',
    ).and_return([])
    flexmock(module.shutil).should_receive('rmtree')
    flexmock(module).should_receive('unmount_snapshot').never()
    flexmock(module).should_receive('get_all_snapshots').and_return(
        ('dataset@borgmatic-1234', 'dataset@other', 'other@other', 'invalid'),
    )
    flexmock(module).should_receive('destroy_snapshot').with_args(
        'zfs',
        'dataset@borgmatic-1234',
    ).once()

    module.remove_data_source_dumps(
        hook_config={},
        config={'source_directories': '/mnt/dataset', 'zfs': {}},
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_skips_unmount_snapshot_mount_paths_after_rmtree_succeeds():
    flexmock(module).should_receive('get_all_dataset_mount_points').and_return(('/mnt/dataset',))
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(
        lambda path: [path.replace('*', 'b33f')],
    )
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/run/borgmatic/zfs_snapshots/b33f',
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/run/borgmatic/zfs_snapshots/b33f/mnt/dataset',
    ).and_return(True).and_return(False)
    flexmock(module.os).should_receive('listdir').and_return(['file.txt'])
    flexmock(module.shutil).should_receive('rmtree')
    flexmock(module).should_receive('unmount_snapshot').never()
    flexmock(module).should_receive('get_all_snapshots').and_return(
        ('dataset@borgmatic-1234', 'dataset@other', 'other@other', 'invalid'),
    )
    flexmock(module).should_receive('destroy_snapshot').with_args(
        'zfs',
        'dataset@borgmatic-1234',
    ).once()

    module.remove_data_source_dumps(
        hook_config={},
        config={'source_directories': '/mnt/dataset', 'zfs': {}},
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_with_dry_run_skips_unmount_and_destroy():
    flexmock(module).should_receive('get_all_dataset_mount_points').and_return(('/mnt/dataset',))
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(
        lambda path: [path.replace('*', 'b33f')],
    )
    flexmock(module.os.path).should_receive('isdir').and_return(True)
    flexmock(module.os).should_receive('listdir').and_return(['file.txt'])
    flexmock(module.shutil).should_receive('rmtree').never()
    flexmock(module).should_receive('unmount_snapshot').never()
    flexmock(module).should_receive('get_all_snapshots').and_return(
        ('dataset@borgmatic-1234', 'dataset@other', 'other@other', 'invalid'),
    )
    flexmock(module).should_receive('destroy_snapshot').never()

    module.remove_data_source_dumps(
        hook_config={},
        config={'source_directories': '/mnt/dataset', 'zfs': {}},
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=True,
    )
