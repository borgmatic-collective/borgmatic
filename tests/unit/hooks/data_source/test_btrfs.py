import pytest
from flexmock import flexmock

from borgmatic.borg.pattern import Pattern, Pattern_style, Pattern_type
from borgmatic.hooks.data_source import btrfs as module


def test_get_filesystem_mount_points_parses_findmnt_output():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return(
        '''{
           "filesystems": [
              {
                 "target": "/mnt0",
                 "source": "/dev/loop0",
                 "fstype": "btrfs",
                 "options": "rw,relatime,ssd,space_cache=v2,subvolid=5,subvol=/"
              },
              {
                 "target": "/mnt1",
                 "source": "/dev/loop0",
                 "fstype": "btrfs",
                 "options": "rw,relatime,ssd,space_cache=v2,subvolid=5,subvol=/"
              }
           ]
        }
        '''
    )

    assert module.get_filesystem_mount_points('findmnt') == ('/mnt0', '/mnt1')


def test_get_filesystem_mount_points_with_invalid_findmnt_json_errors():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return('{')

    with pytest.raises(ValueError):
        module.get_filesystem_mount_points('findmnt')


def test_get_filesystem_mount_points_with_findmnt_json_missing_filesystems_errors():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return('{"wtf": "something is wrong here"}')

    with pytest.raises(ValueError):
        module.get_filesystem_mount_points('findmnt')


def test_get_subvolumes_for_filesystem_parses_subvolume_list_output():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return(
        'ID 270 gen 107 top level 5 path subvol1\nID 272 gen 74 top level 5 path subvol2\n'
    )

    assert module.get_subvolumes_for_filesystem('btrfs', '/mnt') == (
        '/mnt',
        '/mnt/subvol1',
        '/mnt/subvol2',
    )


def test_get_subvolumes_for_filesystem_skips_empty_subvolume_paths():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return('\n \nID 272 gen 74 top level 5 path subvol2\n')

    assert module.get_subvolumes_for_filesystem('btrfs', '/mnt') == ('/mnt', '/mnt/subvol2')


def test_get_subvolumes_for_filesystem_skips_empty_filesystem_mount_points():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return(
        'ID 270 gen 107 top level 5 path subvol1\nID 272 gen 74 top level 5 path subvol2\n'
    )

    assert module.get_subvolumes_for_filesystem('btrfs', ' ') == ()


def test_get_subvolumes_collects_subvolumes_matching_patterns_from_all_filesystems():
    flexmock(module).should_receive('get_filesystem_mount_points').and_return(('/mnt1', '/mnt2'))
    flexmock(module).should_receive('get_subvolumes_for_filesystem').with_args(
        'btrfs', '/mnt1'
    ).and_return(('/one', '/two'))
    flexmock(module).should_receive('get_subvolumes_for_filesystem').with_args(
        'btrfs', '/mnt2'
    ).and_return(('/three', '/four'))

    for path in ('/one', '/four'):
        flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
            'get_contained_patterns'
        ).with_args(path, object).and_return((Pattern(path),))
    for path in ('/two', '/three'):
        flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
            'get_contained_patterns'
        ).with_args(path, object).and_return(())

    assert module.get_subvolumes(
        'btrfs',
        'findmnt',
        patterns=[
            Pattern('/one'),
            Pattern('/four'),
            Pattern('/five'),
            Pattern('/six'),
            Pattern('/mnt2'),
            Pattern('/mnt3'),
        ],
    ) == (
        module.Subvolume('/four', contained_patterns=(Pattern('/four'),)),
        module.Subvolume('/one', contained_patterns=(Pattern('/one'),)),
    )


def test_get_subvolumes_without_patterns_collects_all_subvolumes_from_all_filesystems():
    flexmock(module).should_receive('get_filesystem_mount_points').and_return(('/mnt1', '/mnt2'))
    flexmock(module).should_receive('get_subvolumes_for_filesystem').with_args(
        'btrfs', '/mnt1'
    ).and_return(('/one', '/two'))
    flexmock(module).should_receive('get_subvolumes_for_filesystem').with_args(
        'btrfs', '/mnt2'
    ).and_return(('/three', '/four'))

    for path in ('/one', '/two', '/three', '/four'):
        flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
            'get_contained_patterns'
        ).with_args(path, object).and_return((Pattern(path),))

    assert module.get_subvolumes('btrfs', 'findmnt') == (
        module.Subvolume('/four', contained_patterns=(Pattern('/four'),)),
        module.Subvolume('/one', contained_patterns=(Pattern('/one'),)),
        module.Subvolume('/three', contained_patterns=(Pattern('/three'),)),
        module.Subvolume('/two', contained_patterns=(Pattern('/two'),)),
    )


@pytest.mark.parametrize(
    'subvolume_path,expected_snapshot_path',
    (
        ('/foo/bar', '/foo/bar/.borgmatic-snapshot-1234/foo/bar'),
        ('/', '/.borgmatic-snapshot-1234'),
    ),
)
def test_make_snapshot_path_includes_stripped_subvolume_path(
    subvolume_path, expected_snapshot_path
):
    flexmock(module.os).should_receive('getpid').and_return(1234)

    assert module.make_snapshot_path(subvolume_path) == expected_snapshot_path


@pytest.mark.parametrize(
    'subvolume_path,pattern_path,expected_path',
    (
        ('/foo/bar', '/foo/bar/baz', '/foo/bar/.borgmatic-snapshot-1234/./foo/bar/baz'),
        ('/foo/bar', '/foo/bar', '/foo/bar/.borgmatic-snapshot-1234/./foo/bar'),
        ('/', '/foo', '/.borgmatic-snapshot-1234/./foo'),
        ('/', '/', '/.borgmatic-snapshot-1234/./'),
    ),
)
def test_make_borg_snapshot_pattern_includes_slashdot_hack_and_stripped_pattern_path(
    subvolume_path, pattern_path, expected_path
):
    flexmock(module.os).should_receive('getpid').and_return(1234)

    assert module.make_borg_snapshot_pattern(subvolume_path, Pattern(pattern_path)) == Pattern(
        expected_path
    )


def test_dump_data_sources_snapshots_each_subvolume_and_updates_patterns():
    patterns = [Pattern('/foo'), Pattern('/mnt/subvol1')]
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(
        (
            module.Subvolume('/mnt/subvol1', contained_patterns=(Pattern('/mnt/subvol1'),)),
            module.Subvolume('/mnt/subvol2', contained_patterns=(Pattern('/mnt/subvol2'),)),
        )
    )
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
    flexmock(module).should_receive('make_snapshot_exclude_pattern').with_args(
        '/mnt/subvol1'
    ).and_return(
        Pattern(
            '/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234',
            Pattern_type.EXCLUDE,
            Pattern_style.FNMATCH,
        )
    )
    flexmock(module).should_receive('make_snapshot_exclude_pattern').with_args(
        '/mnt/subvol2'
    ).and_return(
        Pattern(
            '/mnt/subvol2/.borgmatic-1234/mnt/subvol2/.borgmatic-1234',
            Pattern_type.EXCLUDE,
            Pattern_style.FNMATCH,
        )
    )
    flexmock(module).should_receive('make_borg_snapshot_pattern').with_args(
        '/mnt/subvol1', object
    ).and_return(Pattern('/mnt/subvol1/.borgmatic-1234/mnt/subvol1'))
    flexmock(module).should_receive('make_borg_snapshot_pattern').with_args(
        '/mnt/subvol2', object
    ).and_return(Pattern('/mnt/subvol2/.borgmatic-1234/mnt/subvol2'))

    assert (
        module.dump_data_sources(
            hook_config=config['btrfs'],
            config=config,
            log_prefix='test',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=patterns,
            dry_run=False,
        )
        == []
    )

    assert patterns == [
        Pattern('/foo'),
        Pattern('/mnt/subvol1/.borgmatic-1234/mnt/subvol1'),
        Pattern(
            '/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234',
            Pattern_type.EXCLUDE,
            Pattern_style.FNMATCH,
        ),
        Pattern('/mnt/subvol2/.borgmatic-1234/mnt/subvol2'),
        Pattern(
            '/mnt/subvol2/.borgmatic-1234/mnt/subvol2/.borgmatic-1234',
            Pattern_type.EXCLUDE,
            Pattern_style.FNMATCH,
        ),
    ]
    assert config == {
        'btrfs': {},
    }


def test_dump_data_sources_uses_custom_btrfs_command_in_commands():
    patterns = [Pattern('/foo'), Pattern('/mnt/subvol1')]
    config = {'btrfs': {'btrfs_command': '/usr/local/bin/btrfs'}}
    flexmock(module).should_receive('get_subvolumes').and_return(
        (module.Subvolume('/mnt/subvol1', contained_patterns=(Pattern('/mnt/subvol1'),)),)
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1'
    )
    flexmock(module).should_receive('snapshot_subvolume').with_args(
        '/usr/local/bin/btrfs', '/mnt/subvol1', '/mnt/subvol1/.borgmatic-1234/mnt/subvol1'
    ).once()
    flexmock(module).should_receive('make_snapshot_exclude_pattern').with_args(
        '/mnt/subvol1'
    ).and_return(
        Pattern(
            '/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234',
            Pattern_type.EXCLUDE,
            Pattern_style.FNMATCH,
        )
    )
    flexmock(module).should_receive('make_borg_snapshot_pattern').with_args(
        '/mnt/subvol1', object
    ).and_return(Pattern('/mnt/subvol1/.borgmatic-1234/mnt/subvol1'))

    assert (
        module.dump_data_sources(
            hook_config=config['btrfs'],
            config=config,
            log_prefix='test',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=patterns,
            dry_run=False,
        )
        == []
    )

    assert patterns == [
        Pattern('/foo'),
        Pattern('/mnt/subvol1/.borgmatic-1234/mnt/subvol1'),
        Pattern(
            '/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234',
            Pattern_type.EXCLUDE,
            Pattern_style.FNMATCH,
        ),
    ]
    assert config == {
        'btrfs': {
            'btrfs_command': '/usr/local/bin/btrfs',
        },
    }


def test_dump_data_sources_uses_custom_findmnt_command_in_commands():
    patterns = [Pattern('/foo'), Pattern('/mnt/subvol1')]
    config = {'btrfs': {'findmnt_command': '/usr/local/bin/findmnt'}}
    flexmock(module).should_receive('get_subvolumes').with_args(
        'btrfs', '/usr/local/bin/findmnt', patterns
    ).and_return(
        (module.Subvolume('/mnt/subvol1', contained_patterns=(Pattern('/mnt/subvol1'),)),)
    ).once()
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1'
    )
    flexmock(module).should_receive('snapshot_subvolume').with_args(
        'btrfs', '/mnt/subvol1', '/mnt/subvol1/.borgmatic-1234/mnt/subvol1'
    ).once()
    flexmock(module).should_receive('make_snapshot_exclude_pattern').with_args(
        '/mnt/subvol1'
    ).and_return(
        Pattern(
            '/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234',
            Pattern_type.EXCLUDE,
            Pattern_style.FNMATCH,
        )
    )
    flexmock(module).should_receive('make_borg_snapshot_pattern').with_args(
        '/mnt/subvol1', object
    ).and_return(Pattern('/mnt/subvol1/.borgmatic-1234/mnt/subvol1'))

    assert (
        module.dump_data_sources(
            hook_config=config['btrfs'],
            config=config,
            log_prefix='test',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=patterns,
            dry_run=False,
        )
        == []
    )

    assert patterns == [
        Pattern('/foo'),
        Pattern('/mnt/subvol1/.borgmatic-1234/mnt/subvol1'),
        Pattern(
            '/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234',
            Pattern_type.EXCLUDE,
            Pattern_style.FNMATCH,
        ),
    ]
    assert config == {
        'btrfs': {
            'findmnt_command': '/usr/local/bin/findmnt',
        },
    }


def test_dump_data_sources_with_dry_run_skips_snapshot_and_patterns_update():
    patterns = [Pattern('/foo'), Pattern('/mnt/subvol1')]
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(
        (module.Subvolume('/mnt/subvol1', contained_patterns=(Pattern('/mnt/subvol1'),)),)
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1'
    )
    flexmock(module).should_receive('snapshot_subvolume').never()
    flexmock(module).should_receive('make_snapshot_exclude_pattern').never()

    assert (
        module.dump_data_sources(
            hook_config=config['btrfs'],
            config=config,
            log_prefix='test',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=patterns,
            dry_run=True,
        )
        == []
    )

    assert patterns == [Pattern('/foo'), Pattern('/mnt/subvol1')]
    assert config == {'btrfs': {}}


def test_dump_data_sources_without_matching_subvolumes_skips_snapshot_and_patterns_update():
    patterns = [Pattern('/foo'), Pattern('/mnt/subvol1')]
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(())
    flexmock(module).should_receive('make_snapshot_path').never()
    flexmock(module).should_receive('snapshot_subvolume').never()
    flexmock(module).should_receive('make_snapshot_exclude_pattern').never()

    assert (
        module.dump_data_sources(
            hook_config=config['btrfs'],
            config=config,
            log_prefix='test',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=patterns,
            dry_run=False,
        )
        == []
    )

    assert patterns == [Pattern('/foo'), Pattern('/mnt/subvol1')]
    assert config == {'btrfs': {}}


def test_dump_data_sources_snapshots_adds_to_existing_exclude_patterns():
    patterns = [Pattern('/foo'), Pattern('/mnt/subvol1')]
    config = {'btrfs': {}, 'exclude_patterns': ['/bar']}
    flexmock(module).should_receive('get_subvolumes').and_return(
        (
            module.Subvolume('/mnt/subvol1', contained_patterns=(Pattern('/mnt/subvol1'),)),
            module.Subvolume('/mnt/subvol2', contained_patterns=(Pattern('/mnt/subvol2'),)),
        )
    )
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
    flexmock(module).should_receive('make_snapshot_exclude_pattern').with_args(
        '/mnt/subvol1'
    ).and_return(
        Pattern(
            '/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234',
            Pattern_type.EXCLUDE,
            Pattern_style.FNMATCH,
        )
    )
    flexmock(module).should_receive('make_snapshot_exclude_pattern').with_args(
        '/mnt/subvol2'
    ).and_return(
        Pattern(
            '/mnt/subvol2/.borgmatic-1234/mnt/subvol2/.borgmatic-1234',
            Pattern_type.EXCLUDE,
            Pattern_style.FNMATCH,
        )
    )
    flexmock(module).should_receive('make_borg_snapshot_pattern').with_args(
        '/mnt/subvol1', object
    ).and_return(Pattern('/mnt/subvol1/.borgmatic-1234/mnt/subvol1'))
    flexmock(module).should_receive('make_borg_snapshot_pattern').with_args(
        '/mnt/subvol2', object
    ).and_return(Pattern('/mnt/subvol2/.borgmatic-1234/mnt/subvol2'))

    assert (
        module.dump_data_sources(
            hook_config=config['btrfs'],
            config=config,
            log_prefix='test',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=patterns,
            dry_run=False,
        )
        == []
    )

    assert patterns == [
        Pattern('/foo'),
        Pattern('/mnt/subvol1/.borgmatic-1234/mnt/subvol1'),
        Pattern(
            '/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234',
            Pattern_type.EXCLUDE,
            Pattern_style.FNMATCH,
        ),
        Pattern('/mnt/subvol2/.borgmatic-1234/mnt/subvol2'),
        Pattern(
            '/mnt/subvol2/.borgmatic-1234/mnt/subvol2/.borgmatic-1234',
            Pattern_type.EXCLUDE,
            Pattern_style.FNMATCH,
        ),
    ]
    assert config == {
        'btrfs': {},
        'exclude_patterns': ['/bar'],
    }


def test_remove_data_source_dumps_deletes_snapshots():
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(
        (
            module.Subvolume('/mnt/subvol1', contained_patterns=(Pattern('/mnt/subvol1'),)),
            module.Subvolume('/mnt/subvol2', contained_patterns=(Pattern('/mnt/subvol2'),)),
        )
    )
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


def test_remove_data_source_dumps_without_hook_configuration_bails():
    flexmock(module).should_receive('get_subvolumes').never()
    flexmock(module).should_receive('make_snapshot_path').never()
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).never()
    flexmock(module).should_receive('delete_snapshot').never()
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps(
        hook_config=None,
        config={'source_directories': '/mnt/subvolume'},
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
    flexmock(module).should_receive('get_subvolumes').and_return(
        (
            module.Subvolume('/mnt/subvol1', contained_patterns=(Pattern('/mnt/subvol1'),)),
            module.Subvolume('/mnt/subvol2', contained_patterns=(Pattern('/mnt/subvol2'),)),
        )
    )
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
    flexmock(module).should_receive('get_subvolumes').and_return(
        (
            module.Subvolume('/mnt/subvol1', contained_patterns=(Pattern('/mnt/subvol1'),)),
            module.Subvolume('/mnt/subvol2', contained_patterns=(Pattern('/mnt/subvol2'),)),
        )
    )
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
    flexmock(module).should_receive('get_subvolumes').and_return(
        (
            module.Subvolume('/mnt/subvol1', contained_patterns=(Pattern('/mnt/subvol1'),)),
            module.Subvolume('/mnt/subvol2', contained_patterns=(Pattern('/mnt/subvol2'),)),
        )
    )
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
    flexmock(module).should_receive('get_subvolumes').and_return(
        (
            module.Subvolume('/mnt/subvol1', contained_patterns=(Pattern('/mnt/subvol1'),)),
            module.Subvolume('/mnt/subvol2', contained_patterns=(Pattern('/mnt/subvol2'),)),
        )
    )
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
