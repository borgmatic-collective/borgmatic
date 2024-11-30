import pytest
from flexmock import flexmock

from borgmatic.hooks.data_source import btrfs as module


def test_get_filesystem_mount_points_parses_findmnt_output():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return(
        '/mnt0   /dev/loop0 btrfs  rw,relatime,ssd,space_cache=v2,subvolid=5,subvol=/\n'
        '/mnt1   /dev/loop1 btrfs  rw,relatime,ssd,space_cache=v2,subvolid=5,subvol=/\n'
    )

    assert module.get_filesystem_mount_points('findmnt') == ('/mnt0', '/mnt1')


def test_get_subvolumes_for_filesystem_parses_subvolume_list_output():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return(
        'ID 270 gen 107 top level 5 path subvol1\n' 'ID 272 gen 74 top level 5 path subvol2\n'
    )

    assert module.get_subvolumes_for_filesystem('btrfs', '/mnt') == ('/mnt/subvol1', '/mnt/subvol2')


def test_get_subvolumes_collects_subvolumes_matching_source_directories_from_all_filesystems():
    flexmock(module).should_receive('get_filesystem_mount_points').and_return(('/mnt1', '/mnt2'))
    flexmock(module).should_receive('get_subvolumes_for_filesystem').with_args(
        'btrfs', '/mnt1'
    ).and_return(('/one', '/two'))
    flexmock(module).should_receive('get_subvolumes_for_filesystem').with_args(
        'btrfs', '/mnt2'
    ).and_return(('/three', '/four'))

    assert module.get_subvolumes(
        'btrfs', 'findmnt', source_directories=['/one', '/four', '/five', '/six', '/mnt2', '/mnt3']
    ) == ('/one', '/mnt2', '/four')


def test_get_subvolumes_without_source_directories_collects_all_subvolumes_from_all_filesystems():
    flexmock(module).should_receive('get_filesystem_mount_points').and_return(('/mnt1', '/mnt2'))
    flexmock(module).should_receive('get_subvolumes_for_filesystem').with_args(
        'btrfs', '/mnt1'
    ).and_return(('/one', '/two'))
    flexmock(module).should_receive('get_subvolumes_for_filesystem').with_args(
        'btrfs', '/mnt2'
    ).and_return(('/three', '/four'))

    assert module.get_subvolumes('btrfs', 'findmnt') == (
        '/mnt1',
        '/one',
        '/two',
        '/mnt2',
        '/three',
        '/four',
    )


def test_dump_data_sources_snapshots_each_subvolume_and_updates_source_directories():
    source_directories = ['/foo', '/mnt/subvol1']
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(('/mnt/subvol1', '/mnt/subvol2'))
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1'
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol2').and_return(
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2'
    )
    flexmock(module).should_receive('snapshot_subvolume').with_args(
        'btrfs', '/mnt/subvol1', '/mnt/subvol1/.borgmatic-1234/mnt/subvol1'
    ).once()
    flexmock(module).should_receive('snapshot_subvolume').with_args(
        'btrfs', '/mnt/subvol2', '/mnt/subvol2/.borgmatic-1234/mnt/subvol2'
    ).once()
    flexmock(module).should_receive('make_snapshot_exclude_path').with_args(
        '/mnt/subvol1'
    ).and_return('/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234')
    flexmock(module).should_receive('make_snapshot_exclude_path').with_args(
        '/mnt/subvol2'
    ).and_return('/mnt/subvol2/.borgmatic-1234/mnt/subvol2/.borgmatic-1234')

    assert (
        module.dump_data_sources(
            hook_config=config['btrfs'],
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
        '/foo',
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2',
    ]
    assert config == {
        'btrfs': {},
        'exclude_patterns': [
            '/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234',
            '/mnt/subvol2/.borgmatic-1234/mnt/subvol2/.borgmatic-1234',
        ],
    }


def test_dump_data_sources_uses_custom_btrfs_command_in_commands():
    source_directories = ['/foo', '/mnt/subvol1']
    config = {'btrfs': {'btrfs_command': '/usr/local/bin/btrfs'}}
    flexmock(module).should_receive('get_subvolumes').and_return(('/mnt/subvol1',))
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1'
    )
    flexmock(module).should_receive('snapshot_subvolume').with_args(
        '/usr/local/bin/btrfs', '/mnt/subvol1', '/mnt/subvol1/.borgmatic-1234/mnt/subvol1'
    ).once()
    flexmock(module).should_receive('make_snapshot_exclude_path').with_args(
        '/mnt/subvol1'
    ).and_return('/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234')

    assert (
        module.dump_data_sources(
            hook_config=config['btrfs'],
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
        '/foo',
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
    ]
    assert config == {
        'btrfs': {
            'btrfs_command': '/usr/local/bin/btrfs',
        },
        'exclude_patterns': [
            '/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234',
        ],
    }


def test_dump_data_sources_uses_custom_findmnt_command_in_commands():
    source_directories = ['/foo', '/mnt/subvol1']
    config = {'btrfs': {'findmnt_command': '/usr/local/bin/findmnt'}}
    flexmock(module).should_receive('get_subvolumes').with_args(
        'btrfs', '/usr/local/bin/findmnt', source_directories
    ).and_return(('/mnt/subvol1',)).once()
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1'
    )
    flexmock(module).should_receive('snapshot_subvolume').with_args(
        'btrfs', '/mnt/subvol1', '/mnt/subvol1/.borgmatic-1234/mnt/subvol1'
    ).once()
    flexmock(module).should_receive('make_snapshot_exclude_path').with_args(
        '/mnt/subvol1'
    ).and_return('/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234')

    assert (
        module.dump_data_sources(
            hook_config=config['btrfs'],
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
        '/foo',
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
    ]
    assert config == {
        'btrfs': {
            'findmnt_command': '/usr/local/bin/findmnt',
        },
        'exclude_patterns': [
            '/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234',
        ],
    }


def test_dump_data_sources_with_dry_run_skips_snapshot_and_source_directories_update():
    source_directories = ['/foo', '/mnt/subvol1']
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(('/mnt/subvol1',))
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1'
    )
    flexmock(module).should_receive('snapshot_subvolume').never()
    flexmock(module).should_receive('make_snapshot_exclude_path').never()

    assert (
        module.dump_data_sources(
            hook_config=config['btrfs'],
            config=config,
            log_prefix='test',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            source_directories=source_directories,
            dry_run=True,
        )
        == []
    )

    assert source_directories == ['/foo', '/mnt/subvol1']
    assert config == {'btrfs': {}}


def test_dump_data_sources_without_matching_subvolumes_skips_snapshot_and_source_directories_update():
    source_directories = ['/foo', '/mnt/subvol1']
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(())
    flexmock(module).should_receive('make_snapshot_path').never()
    flexmock(module).should_receive('snapshot_subvolume').never()
    flexmock(module).should_receive('make_snapshot_exclude_path').never()

    assert (
        module.dump_data_sources(
            hook_config=config['btrfs'],
            config=config,
            log_prefix='test',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            source_directories=source_directories,
            dry_run=False,
        )
        == []
    )

    assert source_directories == ['/foo', '/mnt/subvol1']
    assert config == {'btrfs': {}}


def test_remove_data_source_dumps_deletes_snapshots():
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(('/mnt/subvol1', '/mnt/subvol2'))
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/./mnt/subvol1'
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol2').and_return(
        '/mnt/subvol2/.borgmatic-1234/./mnt/subvol2'
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).with_args(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
        temporary_directory_prefix=module.BORGMATIC_SNAPSHOT_PREFIX,
    ).and_return(
        '/mnt/subvol1/.borgmatic-*/mnt/subvol1'
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).with_args(
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2',
        temporary_directory_prefix=module.BORGMATIC_SNAPSHOT_PREFIX,
    ).and_return(
        '/mnt/subvol2/.borgmatic-*/mnt/subvol2'
    )
    flexmock(module.glob).should_receive('glob').with_args(
        '/mnt/subvol1/.borgmatic-*/mnt/subvol1'
    ).and_return(
        ('/mnt/subvol1/.borgmatic-1234/mnt/subvol1', '/mnt/subvol1/.borgmatic-5678/mnt/subvol1')
    )
    flexmock(module.glob).should_receive('glob').with_args(
        '/mnt/subvol2/.borgmatic-*/mnt/subvol2'
    ).and_return(
        ('/mnt/subvol2/.borgmatic-1234/mnt/subvol2', '/mnt/subvol2/.borgmatic-5678/mnt/subvol2')
    )
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1'
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol1/.borgmatic-5678/mnt/subvol1'
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2'
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol2/.borgmatic-5678/mnt/subvol2'
    ).and_return(False)
    flexmock(module).should_receive('delete_snapshot').with_args(
        'btrfs', '/mnt/subvol1/.borgmatic-1234/mnt/subvol1'
    ).once()
    flexmock(module).should_receive('delete_snapshot').with_args(
        'btrfs', '/mnt/subvol1/.borgmatic-5678/mnt/subvol1'
    ).once()
    flexmock(module).should_receive('delete_snapshot').with_args(
        'btrfs', '/mnt/subvol2/.borgmatic-1234/mnt/subvol2'
    ).once()
    flexmock(module).should_receive('delete_snapshot').with_args(
        'btrfs', '/mnt/subvol2/.borgmatic-5678/mnt/subvol2'
    ).never()
    flexmock(module.shutil).should_receive('rmtree').with_args(
        '/mnt/subvol1/.borgmatic-1234'
    ).once()
    flexmock(module.shutil).should_receive('rmtree').with_args(
        '/mnt/subvol1/.borgmatic-5678'
    ).once()
    flexmock(module.shutil).should_receive('rmtree').with_args(
        '/mnt/subvol2/.borgmatic-1234'
    ).once()
    flexmock(module.shutil).should_receive('rmtree').with_args(
        '/mnt/subvol2/.borgmatic-5678'
    ).never()

    module.remove_data_source_dumps(
        hook_config=config['btrfs'],
        config=config,
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_with_get_subvolumes_file_not_found_error_bails():
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_raise(FileNotFoundError)
    flexmock(module).should_receive('make_snapshot_path').never()
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).never()
    flexmock(module).should_receive('delete_snapshot').never()
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps(
        hook_config=config['btrfs'],
        config=config,
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_with_get_subvolumes_called_process_error_bails():
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_raise(
        module.subprocess.CalledProcessError(1, 'command', 'error')
    )
    flexmock(module).should_receive('make_snapshot_path').never()
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).never()
    flexmock(module).should_receive('delete_snapshot').never()
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps(
        hook_config=config['btrfs'],
        config=config,
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_with_dry_run_skips_deletes():
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(('/mnt/subvol1', '/mnt/subvol2'))
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/./mnt/subvol1'
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol2').and_return(
        '/mnt/subvol2/.borgmatic-1234/./mnt/subvol2'
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).with_args(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
        temporary_directory_prefix=module.BORGMATIC_SNAPSHOT_PREFIX,
    ).and_return(
        '/mnt/subvol1/.borgmatic-*/mnt/subvol1'
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).with_args(
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2',
        temporary_directory_prefix=module.BORGMATIC_SNAPSHOT_PREFIX,
    ).and_return(
        '/mnt/subvol2/.borgmatic-*/mnt/subvol2'
    )
    flexmock(module.glob).should_receive('glob').with_args(
        '/mnt/subvol1/.borgmatic-*/mnt/subvol1'
    ).and_return(
        ('/mnt/subvol1/.borgmatic-1234/mnt/subvol1', '/mnt/subvol1/.borgmatic-5678/mnt/subvol1')
    )
    flexmock(module.glob).should_receive('glob').with_args(
        '/mnt/subvol2/.borgmatic-*/mnt/subvol2'
    ).and_return(
        ('/mnt/subvol2/.borgmatic-1234/mnt/subvol2', '/mnt/subvol2/.borgmatic-5678/mnt/subvol2')
    )
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1'
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol1/.borgmatic-5678/mnt/subvol1'
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2'
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol2/.borgmatic-5678/mnt/subvol2'
    ).and_return(False)
    flexmock(module).should_receive('delete_snapshot').never()
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps(
        hook_config=config['btrfs'],
        config=config,
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=True,
    )


def test_remove_data_source_dumps_without_subvolumes_skips_deletes():
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(())
    flexmock(module).should_receive('make_snapshot_path').never()
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).never()
    flexmock(module).should_receive('delete_snapshot').never()
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps(
        hook_config=config['btrfs'],
        config=config,
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_without_snapshots_skips_deletes():
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(('/mnt/subvol1', '/mnt/subvol2'))
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/./mnt/subvol1'
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol2').and_return(
        '/mnt/subvol2/.borgmatic-1234/./mnt/subvol2'
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).with_args(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
        temporary_directory_prefix=module.BORGMATIC_SNAPSHOT_PREFIX,
    ).and_return(
        '/mnt/subvol1/.borgmatic-*/mnt/subvol1'
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).with_args(
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2',
        temporary_directory_prefix=module.BORGMATIC_SNAPSHOT_PREFIX,
    ).and_return(
        '/mnt/subvol2/.borgmatic-*/mnt/subvol2'
    )
    flexmock(module.glob).should_receive('glob').and_return(())
    flexmock(module.os.path).should_receive('isdir').never()
    flexmock(module).should_receive('delete_snapshot').never()
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps(
        hook_config=config['btrfs'],
        config=config,
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_with_delete_snapshot_file_not_found_error_bails():
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(('/mnt/subvol1', '/mnt/subvol2'))
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/./mnt/subvol1'
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol2').and_return(
        '/mnt/subvol2/.borgmatic-1234/./mnt/subvol2'
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).with_args(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
        temporary_directory_prefix=module.BORGMATIC_SNAPSHOT_PREFIX,
    ).and_return(
        '/mnt/subvol1/.borgmatic-*/mnt/subvol1'
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).with_args(
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2',
        temporary_directory_prefix=module.BORGMATIC_SNAPSHOT_PREFIX,
    ).and_return(
        '/mnt/subvol2/.borgmatic-*/mnt/subvol2'
    )
    flexmock(module.glob).should_receive('glob').with_args(
        '/mnt/subvol1/.borgmatic-*/mnt/subvol1'
    ).and_return(
        ('/mnt/subvol1/.borgmatic-1234/mnt/subvol1', '/mnt/subvol1/.borgmatic-5678/mnt/subvol1')
    )
    flexmock(module.glob).should_receive('glob').with_args(
        '/mnt/subvol2/.borgmatic-*/mnt/subvol2'
    ).and_return(
        ('/mnt/subvol2/.borgmatic-1234/mnt/subvol2', '/mnt/subvol2/.borgmatic-5678/mnt/subvol2')
    )
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1'
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol1/.borgmatic-5678/mnt/subvol1'
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2'
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol2/.borgmatic-5678/mnt/subvol2'
    ).and_return(False)
    flexmock(module).should_receive('delete_snapshot').and_raise(FileNotFoundError)
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps(
        hook_config=config['btrfs'],
        config=config,
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )


def test_remove_data_source_dumps_with_delete_snapshot_called_process_error_bails():
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(('/mnt/subvol1', '/mnt/subvol2'))
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/./mnt/subvol1'
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol2').and_return(
        '/mnt/subvol2/.borgmatic-1234/./mnt/subvol2'
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).with_args(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
        temporary_directory_prefix=module.BORGMATIC_SNAPSHOT_PREFIX,
    ).and_return(
        '/mnt/subvol1/.borgmatic-*/mnt/subvol1'
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).with_args(
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2',
        temporary_directory_prefix=module.BORGMATIC_SNAPSHOT_PREFIX,
    ).and_return(
        '/mnt/subvol2/.borgmatic-*/mnt/subvol2'
    )
    flexmock(module.glob).should_receive('glob').with_args(
        '/mnt/subvol1/.borgmatic-*/mnt/subvol1'
    ).and_return(
        ('/mnt/subvol1/.borgmatic-1234/mnt/subvol1', '/mnt/subvol1/.borgmatic-5678/mnt/subvol1')
    )
    flexmock(module.glob).should_receive('glob').with_args(
        '/mnt/subvol2/.borgmatic-*/mnt/subvol2'
    ).and_return(
        ('/mnt/subvol2/.borgmatic-1234/mnt/subvol2', '/mnt/subvol2/.borgmatic-5678/mnt/subvol2')
    )
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1'
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol1/.borgmatic-5678/mnt/subvol1'
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2'
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol2/.borgmatic-5678/mnt/subvol2'
    ).and_return(False)
    flexmock(module).should_receive('delete_snapshot').and_raise(
        module.subprocess.CalledProcessError(1, 'command', 'error')
    )
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps(
        hook_config=config['btrfs'],
        config=config,
        log_prefix='test',
        borgmatic_runtime_directory='/run/borgmatic',
        dry_run=False,
    )
