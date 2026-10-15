import io
import sys

import pytest
from flexmock import flexmock

from borgmatic.hooks.data_source import tarballs as module


def test_dump_data_sources_creates_member_pipes_and_manifest_and_stream_process():
    flexmock(module.dump).should_receive('raise_number_of_files_resource_limit')
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module).should_receive('make_dump_path').and_return(flexmock())
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        '/run/borgmatic/tarballs/localhost/foo'
    ).and_return('/run/borgmatic/tarballs/localhost/bar')
    flexmock(module.os).should_receive('makedirs')
    flexmock(module.tarfile).should_receive('is_tarfile').and_return(True)
    member_metadata = {'type': '5'}
    foo_members = [
        flexmock(name='dir', get_info=lambda: member_metadata, isdir=lambda: True),
        flexmock(name='dir/foo.txt', get_info=lambda: member_metadata, isdir=lambda: False),
    ]
    bar_members = [flexmock(name='bar.txt', get_info=lambda: member_metadata, isdir=lambda: False)]
    flexmock(module.tarfile).should_receive('open').and_return(foo_members).and_return(bar_members)
    flexmock(module.os).should_receive('makedirs').with_args(
        '/run/borgmatic/tarballs/localhost/foo/dir', mode=object, exist_ok=True
    )
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').with_args(
        '/run/borgmatic/tarballs/localhost/foo/dir'
    ).never()
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').with_args(
        '/run/borgmatic/tarballs/localhost/foo/dir/foo.txt'
    ).once()
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').with_args(
        '/run/borgmatic/tarballs/localhost/bar/bar.txt'
    ).once()
    foo_manifest_file = flexmock()
    foo_manifest_file.should_receive('write').with_args(
        '{"dir": {"type": 53}, "dir/foo.txt": {"type": 53}}'
    ).once()
    flexmock(sys.modules['builtins']).should_receive('open').with_args(
        '/run/borgmatic/tarballs/localhost/foo_manifest.json',
        'w',
    ).and_return(foo_manifest_file)
    bar_manifest_file = flexmock()
    bar_manifest_file.should_receive('write').with_args('{"bar.txt": {"type": 53}}').once()
    flexmock(sys.modules['builtins']).should_receive('open').with_args(
        '/run/borgmatic/tarballs/localhost/bar_manifest.json',
        'w',
    ).and_return(bar_manifest_file)
    flexmock(module.borgmatic.execute).should_receive('execute_command').and_return(
        stream_process := flexmock()
    ).once()
    flexmock(module.dump).should_receive('write_data_source_dumps_metadata')
    flexmock(module.borgmatic.hooks.data_source.config).should_receive('inject_pattern')
    tarballs = [{'name': 'foo', 'path': 'foo.tar.gz'}, {'name': 'bar', 'path': 'bar.tar'}]

    assert module.dump_data_sources(
        tarballs=tarballs,
        config=flexmock(),
        config_paths=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=flexmock(),
        dry_run=False,
    ) == (stream_process,)


def test_dump_data_sources_with_missing_tarball_raises():
    flexmock(module.dump).should_receive('raise_number_of_files_resource_limit')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module).should_receive('make_dump_path').never()
    flexmock(module.borgmatic.execute).should_receive('execute_command').never()
    tarballs = [{'name': 'foo', 'path': 'foo.tar.gz'}, {'name': 'bar', 'path': 'bar.tar'}]

    with pytest.raises(ValueError):
        module.dump_data_sources(
            tarballs=tarballs,
            config=flexmock(),
            config_paths=flexmock(),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=flexmock(),
            dry_run=False,
        )


def test_dump_data_sources_with_invalid_tarball_raises():
    flexmock(module.dump).should_receive('raise_number_of_files_resource_limit')
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module).should_receive('make_dump_path').and_return(flexmock())
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        '/run/borgmatic/tarballs/localhost/foo'
    ).and_return('/run/borgmatic/tarballs/localhost/bar')
    flexmock(module.os).should_receive('makedirs')
    flexmock(module.tarfile).should_receive('is_tarfile').and_return(False)
    flexmock(module.borgmatic.execute).should_receive('execute_command').never()
    tarballs = [{'name': 'foo', 'path': 'foo.tar.gz'}, {'name': 'bar', 'path': 'bar.tar'}]

    with pytest.raises(ValueError):
        module.dump_data_sources(
            tarballs=tarballs,
            config=flexmock(),
            config_paths=flexmock(),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=flexmock(),
            dry_run=False,
        )


def test_dump_data_sources_with_dry_run_skips_member_pipes_and_manifest_and_stream_process():
    flexmock(module.dump).should_receive('raise_number_of_files_resource_limit')
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module).should_receive('make_dump_path').and_return(flexmock())
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        '/run/borgmatic/tarballs/localhost/foo'
    ).and_return('/run/borgmatic/tarballs/localhost/bar')
    flexmock(module.os).should_receive('makedirs')
    flexmock(module.tarfile).should_receive('is_tarfile').and_return(True)
    member_metadata = {'type': '5'}
    foo_members = [
        flexmock(name='dir', get_info=lambda: member_metadata, isdir=lambda: True),
        flexmock(name='dir/foo.txt', get_info=lambda: member_metadata, isdir=lambda: False),
    ]
    bar_members = [flexmock(name='bar.txt', get_info=lambda: member_metadata, isdir=lambda: False)]
    flexmock(module.tarfile).should_receive('open').and_return(foo_members).and_return(bar_members)
    flexmock(module.os).should_receive('makedirs').never()
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').never()
    foo_manifest_file = flexmock()
    foo_manifest_file.should_receive('write').with_args(
        '{"dir": {"type": 53}, "dir/foo.txt": {"type": 53}}'
    ).once()
    flexmock(sys.modules['builtins']).should_receive('open').with_args(
        '/run/borgmatic/tarballs/localhost/foo_manifest.json',
        'w',
    ).and_return(foo_manifest_file)
    bar_manifest_file = flexmock()
    bar_manifest_file.should_receive('write').with_args('{"bar.txt": {"type": 53}}').once()
    flexmock(sys.modules['builtins']).should_receive('open').with_args(
        '/run/borgmatic/tarballs/localhost/bar_manifest.json',
        'w',
    ).and_return(bar_manifest_file)
    flexmock(module.borgmatic.execute).should_receive('execute_command').never()
    flexmock(module.dump).should_receive('write_data_source_dumps_metadata').never()
    flexmock(module.borgmatic.hooks.data_source.config).should_receive('inject_pattern').never()
    tarballs = [{'name': 'foo', 'path': 'foo.tar.gz'}, {'name': 'bar', 'path': 'bar.tar'}]

    assert (
        module.dump_data_sources(
            tarballs=tarballs,
            config=flexmock(),
            config_paths=flexmock(),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=flexmock(),
            dry_run=True,
        )
        == ()
    )


def test_stream_member_writes_member_data_to_pipe():
    member_pipe = flexmock()
    member_pipe.should_receive('write').with_args(b'data').once()
    flexmock(sys.modules['builtins']).should_receive('open').with_args(
        '/run/foo.txt',
        'wb',
    ).and_return(member_pipe)
    member = flexmock(name='foo.txt', isfile=lambda: True)
    tar_file = flexmock()
    tar_file.should_receive('extractfile').with_args(member).and_return(
        io.BufferedReader(io.BytesIO(b'data'))
    )

    module.stream_member(
        tar_file=tar_file, dump_directory='/run', member=member, read_lock=flexmock()
    )


def test_stream_member_writes_big_member_data_to_pipe_in_chunks():
    member_pipe = flexmock()
    member_pipe.should_receive('write').twice()
    flexmock(sys.modules['builtins']).should_receive('open').with_args(
        '/run/foo.txt',
        'wb',
    ).and_return(member_pipe)
    member = flexmock(name='foo.txt', isfile=lambda: True)
    tar_file = flexmock()
    tar_file.should_receive('extractfile').with_args(member).and_return(
        io.BufferedReader(io.BytesIO(b'x' * (module.STREAM_BLOCK_SIZE + 1)))
    )

    module.stream_member(
        tar_file=tar_file, dump_directory='/run', member=member, read_lock=flexmock()
    )


def test_stream_member_with_non_regular_file_bails():
    member_pipe = flexmock()
    member_pipe.should_receive('write').never()
    flexmock(sys.modules['builtins']).should_receive('open').with_args(
        '/run/dev/foo',
        'wb',
    ).and_return(member_pipe)
    member = flexmock(name='dev/foo', isfile=lambda: False)
    tar_file = flexmock()
    tar_file.should_receive('extractfile').with_args(member).never()

    module.stream_member(
        tar_file=tar_file, dump_directory='/run', member=member, read_lock=flexmock()
    )


def test_stream_tarballs_streams_each_tarball_member():
    foo_members = [
        flexmock(name='dir', isdir=lambda: True),
        flexmock(name='dir/foo.txt', isdir=lambda: False),
    ]
    bar_members = [flexmock(name='bar.txt', isdir=lambda: False)]
    flexmock(module.tarfile).should_receive('open').with_args(
        'foo.tar.gz',
    ).and_return(foo_members)
    flexmock(module.tarfile).should_receive('open').with_args(
        'bar.tar',
    ).and_return(bar_members)
    flexmock(module).should_receive('make_dump_path').and_return(flexmock())
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        '/run/borgmatic/tarballs/localhost/foo'
    ).and_return('/run/borgmatic/tarballs/localhost/bar')
    flexmock(module.threading).should_receive('Lock').and_return(foo_lock := flexmock()).and_return(
        bar_lock := flexmock()
    )
    flexmock(module).should_receive('stream_member')
    flexmock(module.threading).should_receive('Thread').with_args(
        target=module.stream_member,
        args=(foo_members, '/run/borgmatic/tarballs/localhost/foo', foo_members[0], foo_lock),
    ).never()  # Directory members get skipped.
    flexmock(module.threading).should_receive('Thread').with_args(
        target=module.stream_member,
        args=(foo_members, '/run/borgmatic/tarballs/localhost/foo', foo_members[1], foo_lock),
    ).and_return(flexmock(start=lambda: None, join=lambda: None)).once()
    flexmock(module.threading).should_receive('Thread').with_args(
        target=module.stream_member,
        args=(bar_members, '/run/borgmatic/tarballs/localhost/bar', bar_members[0], bar_lock),
    ).and_return(flexmock(start=lambda: None, join=lambda: None)).once()
    tarballs = [{'name': 'foo', 'path': 'foo.tar.gz'}, {'name': 'bar', 'path': 'bar.tar'}]

    module.stream_tarballs(tarballs, borgmatic_runtime_directory='/run/borgmatic')


def test_load_data_source_dump_manifest_extracts_manifest_json():
    flexmock(module).should_receive('make_data_source_dump_patterns').and_return(flexmock())
    flexmock(module.borgmatic.hooks).should_receive(
        'data_source.dump.convert_glob_patterns_to_borg_pattern'
    ).and_return(flexmock())
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        flexmock(stdout=io.StringIO('{"manifest": {}}'))
    )

    assert module.load_data_source_dump_manifest(
        hook_config=flexmock(),
        config=flexmock(),
        repository={'path': 'test.borg'},
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        archive_name=flexmock(),
        data_source={'name': 'foo', 'path': 'foo.tar.gz'},
        borgmatic_runtime_directory=flexmock(),
    ) == {'manifest': {}}


def test_load_data_source_with_invalid_json_raises():
    flexmock(module).should_receive('make_data_source_dump_patterns').and_return(flexmock())
    flexmock(module.borgmatic.hooks).should_receive(
        'data_source.dump.convert_glob_patterns_to_borg_pattern'
    ).and_return(flexmock())
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        flexmock(stdout=io.StringIO('{'))
    )

    with pytest.raises(ValueError):
        assert module.load_data_source_dump_manifest(
            hook_config=flexmock(),
            config=flexmock(),
            repository={'path': 'test.borg'},
            local_borg_version=flexmock(),
            global_arguments=flexmock(),
            local_path=flexmock(),
            remote_path=flexmock(),
            archive_name=flexmock(),
            data_source={'name': 'foo', 'path': 'foo.tar.gz'},
            borgmatic_runtime_directory=flexmock(),
        ) == {'manifest': {}}


def test_strip_member_path_prefix_removes_prefix_from_member_path():
    assert (
        module.strip_member_path_prefix('borgmatic/tarballs/localhost/example/foo/bar/baz.txt')
        == 'foo/bar/baz.txt'
    )


def test_strip_member_path_prefix_without_prefix_strips_nothing():
    assert module.strip_member_path_prefix('foo/bar/baz.txt') is None


def test_restore_data_source_dump_exports_and_rewrites_and_saves_tarball():
    flexmock(module.os).should_receive('remove')
    extract_process_stdout = flexmock()
    source_members = [
        flexmock(name='dir', key='original1', isfile=lambda: False),
        flexmock(name='dir/foo.txt', key='original2', isfile=lambda: True),
    ]
    source_tar = flexmock()
    source_tar.should_receive('__iter__').and_return(iter(source_members))
    source_tar.should_receive('extractfile').with_args(
        source_members[0]
    ).never()  # Directories are skipped.
    source_tar.should_receive('extractfile').with_args(source_members[1]).and_return(
        foo_data := flexmock()
    ).once()
    flexmock(module.tarfile).should_receive('open').with_args(
        mode='r|', fileobj=extract_process_stdout
    ).and_return(source_tar)
    destination_tar = flexmock()
    destination_tar.should_receive('addfile').with_args(
        source_members[0], None
    ).once()  # Directories have no data.
    destination_tar.should_receive('addfile').with_args(source_members[1], foo_data).once()
    flexmock(module.tarfile).should_receive('open').with_args(
        'foo.tar.gz', mode='x:gz', fileobj=None
    ).and_return(destination_tar)
    flexmock(module).should_receive('strip_member_path_prefix').replace_with(
        lambda member_name: member_name
    )

    module.restore_data_source_dump(
        hook_config=flexmock(),
        config=flexmock(),
        data_source={'name': 'foo', 'path': 'foo.tar.gz'},
        dry_run=False,
        extract_process=flexmock(stdout=extract_process_stdout),
        manifest={
            'dir': {'type': 53, 'key': 'value1'},
            'dir/foo.txt': {'type': 53, 'key': 'value2'},
        },
        connection_params=flexmock(),
        borgmatic_runtime_directory=flexmock(),
    )

    assert source_members[0].type == b'5'
    assert source_members[0].key == 'value1'
    assert source_members[1].type == b'5'
    assert source_members[1].key == 'value2'


def test_restore_data_source_dump_with_missing_tarball_exports_and_rewrites_and_saves_tarball():
    flexmock(module.os).should_receive('remove').and_raise(FileNotFoundError)
    extract_process_stdout = flexmock()
    exported_members = [
        flexmock(name='dir', key='original1', isfile=lambda: False),
        flexmock(name='dir/foo.txt', key='original2', isfile=lambda: True),
    ]
    exported_tar = flexmock()
    exported_tar.should_receive('__iter__').and_return(iter(exported_members))
    exported_tar.should_receive('extractfile').with_args(
        exported_members[0]
    ).never()  # Directories are skipped.
    exported_tar.should_receive('extractfile').with_args(exported_members[1]).and_return(
        foo_data := flexmock()
    ).once()
    flexmock(module.tarfile).should_receive('open').with_args(
        mode='r|', fileobj=extract_process_stdout
    ).and_return(exported_tar)
    destination_tar = flexmock()
    destination_tar.should_receive('addfile').with_args(
        exported_members[0], None
    ).once()  # Directories have no data.
    destination_tar.should_receive('addfile').with_args(exported_members[1], foo_data).once()
    flexmock(module.tarfile).should_receive('open').with_args(
        'foo.tar.gz', mode='x:gz', fileobj=None
    ).and_return(destination_tar)
    flexmock(module).should_receive('strip_member_path_prefix').replace_with(
        lambda member_name: member_name
    )

    module.restore_data_source_dump(
        hook_config=flexmock(),
        config=flexmock(),
        data_source={'name': 'foo', 'path': 'foo.tar.gz'},
        dry_run=False,
        extract_process=flexmock(stdout=extract_process_stdout),
        manifest={
            'dir': {'type': 53, 'key': 'value1'},
            'dir/foo.txt': {'type': 53, 'key': 'value2'},
        },
        connection_params=flexmock(),
        borgmatic_runtime_directory=flexmock(),
    )

    assert exported_members[0].type == b'5'
    assert exported_members[0].key == 'value1'
    assert exported_members[1].type == b'5'
    assert exported_members[1].key == 'value2'


def test_restore_data_source_dump_with_dry_run_skips_tarball_remove_and_write():
    flexmock(module.os).should_receive('remove').never()
    extract_process_stdout = flexmock()
    exported_members = [
        flexmock(name='dir', key='original1', isfile=lambda: False),
        flexmock(name='dir/foo.txt', key='original2', isfile=lambda: True),
    ]
    exported_tar = flexmock()
    exported_tar.should_receive('__iter__').and_return(iter(exported_members))
    exported_tar.should_receive('extractfile').with_args(
        exported_members[0]
    ).never()  # Directories are skipped.
    exported_tar.should_receive('extractfile').with_args(exported_members[1]).and_return(
        foo_data := flexmock()
    ).once()
    flexmock(module.tarfile).should_receive('open').with_args(
        mode='r|', fileobj=extract_process_stdout
    ).and_return(exported_tar)
    destination_tar = flexmock()
    destination_tar.should_receive('addfile').with_args(
        exported_members[0],
        None,  # Directories have no data.
    ).once()
    destination_tar.should_receive('addfile').with_args(exported_members[1], foo_data).once()
    flexmock(sys.modules['builtins']).should_receive('open').with_args(
        module.os.devnull,
        'wb',
    ).and_return(dev_null := flexmock())
    flexmock(module.tarfile).should_receive('open').with_args(
        None, mode='x:gz', fileobj=dev_null
    ).and_return(destination_tar)
    flexmock(module).should_receive('strip_member_path_prefix').replace_with(
        lambda member_name: member_name
    )

    module.restore_data_source_dump(
        hook_config=flexmock(),
        config=flexmock(),
        data_source={'name': 'foo', 'path': 'foo.tar.gz'},
        dry_run=True,
        extract_process=flexmock(stdout=extract_process_stdout),
        manifest={
            'dir': {'type': 53, 'key': 'value1'},
            'dir/foo.txt': {'type': 53, 'key': 'value2'},
        },
        connection_params=flexmock(),
        borgmatic_runtime_directory=flexmock(),
    )

    assert exported_members[0].type == b'5'
    assert exported_members[0].key == 'value1'
    assert exported_members[1].type == b'5'
    assert exported_members[1].key == 'value2'


def test_restore_data_source_dump_with_no_compression_exports_and_rewrites_and_saves_tarball():
    flexmock(module.os).should_receive('remove')
    extract_process_stdout = flexmock()
    exported_members = [
        flexmock(name='dir', key='original1', isfile=lambda: False),
        flexmock(name='dir/foo.txt', key='original2', isfile=lambda: True),
    ]
    exported_tar = flexmock()
    exported_tar.should_receive('__iter__').and_return(iter(exported_members))
    exported_tar.should_receive('extractfile').with_args(
        exported_members[0]
    ).never()  # Directories are skipped.
    exported_tar.should_receive('extractfile').with_args(exported_members[1]).and_return(
        foo_data := flexmock()
    ).once()
    flexmock(module.tarfile).should_receive('open').with_args(
        mode='r|', fileobj=extract_process_stdout
    ).and_return(exported_tar)
    destination_tar = flexmock()
    destination_tar.should_receive('addfile').with_args(
        exported_members[0], None
    ).once()  # Directories have no data.
    destination_tar.should_receive('addfile').with_args(exported_members[1], foo_data).once()
    flexmock(module.tarfile).should_receive('open').with_args(
        'foo.tar', mode='x:', fileobj=None
    ).and_return(destination_tar)
    flexmock(module).should_receive('strip_member_path_prefix').replace_with(
        lambda member_name: member_name
    )

    module.restore_data_source_dump(
        hook_config=flexmock(),
        config=flexmock(),
        data_source={'name': 'foo', 'path': 'foo.tar'},
        dry_run=False,
        extract_process=flexmock(stdout=extract_process_stdout),
        manifest={
            'dir': {'type': 53, 'key': 'value1'},
            'dir/foo.txt': {'type': 53, 'key': 'value2'},
        },
        connection_params=flexmock(),
        borgmatic_runtime_directory=flexmock(),
    )

    assert exported_members[0].type == b'5'
    assert exported_members[0].key == 'value1'
    assert exported_members[1].type == b'5'
    assert exported_members[1].key == 'value2'


def test_restore_data_source_dump_with_unknown_compression_raises():
    flexmock(module.os).should_receive('remove')
    exported_tar = flexmock()
    exported_tar.should_receive('__iter__').never()
    exported_tar.should_receive('extractfile').never()
    flexmock(module.tarfile).should_receive('open').never()

    with pytest.raises(ValueError):
        module.restore_data_source_dump(
            hook_config=flexmock(),
            config=flexmock(),
            data_source={'name': 'foo', 'path': 'foo.tar.lz4'},
            dry_run=False,
            extract_process=flexmock(),
            manifest={
                'dir': {'type': 53, 'key': 'value1'},
                'dir/foo.txt': {'type': 53, 'key': 'value2'},
            },
            connection_params=flexmock(),
            borgmatic_runtime_directory=flexmock(),
        )


def test_restore_data_source_dump_with_exported_member_missing_from_manifest_skips_it():
    flexmock(module.os).should_receive('remove')
    extract_process_stdout = flexmock()
    exported_members = [
        flexmock(name='dir', key='original1', isfile=lambda: False),
        flexmock(name='dir/foo.txt', key='original2', isfile=lambda: True),
        flexmock(name='missing', key='original', isfile=lambda: True),
    ]
    exported_tar = flexmock()
    exported_tar.should_receive('__iter__').and_return(iter(exported_members))
    exported_tar.should_receive('extractfile').with_args(
        exported_members[0]
    ).never()  # Directories are skipped.
    exported_tar.should_receive('extractfile').with_args(exported_members[1]).and_return(
        foo_data := flexmock()
    ).once()
    flexmock(module.tarfile).should_receive('open').with_args(
        mode='r|', fileobj=extract_process_stdout
    ).and_return(exported_tar)
    destination_tar = flexmock()
    destination_tar.should_receive('addfile').with_args(
        exported_members[0], None
    ).once()  # Directories have no data.
    destination_tar.should_receive('addfile').with_args(exported_members[1], foo_data).once()
    flexmock(module.tarfile).should_receive('open').with_args(
        'foo.tar.gz', mode='x:gz', fileobj=None
    ).and_return(destination_tar)
    destination_tar.should_receive('addfile').with_args(exported_members[2], object).never()
    flexmock(module).should_receive('strip_member_path_prefix').replace_with(
        lambda member_name: member_name
    )

    module.restore_data_source_dump(
        hook_config=flexmock(),
        config=flexmock(),
        data_source={'name': 'foo', 'path': 'foo.tar.gz'},
        dry_run=False,
        extract_process=flexmock(stdout=extract_process_stdout),
        manifest={
            'dir': {'type': 53, 'key': 'value1'},
            'dir/foo.txt': {'type': 53, 'key': 'value2'},
        },
        connection_params=flexmock(),
        borgmatic_runtime_directory=flexmock(),
    )

    assert exported_members[0].type == b'5'
    assert exported_members[0].key == 'value1'
    assert exported_members[1].type == b'5'
    assert exported_members[1].key == 'value2'


def test_main_parses_environment_variables_and_streams_tarballs():
    flexmock(module.borgmatic.logger).should_receive('configure_logging')
    flexmock(module).should_receive('stream_tarballs').with_args(
        [{'name': 'foo', 'path': 'foo.tgz'}], '/run/borgmatic'
    ).once()

    try:
        module.os.environ['BORGMATIC_TARBALLS_CONFIG'] = '[{"name": "foo", "path": "foo.tgz"}]'
        module.os.environ['BORGMATIC_RUNTIME_DIRECTORY'] = '/run/borgmatic'

        module.main()
    finally:
        module.os.environ.pop('BORGMATIC_TARBALLS_CONFIG', None)
        module.os.environ.pop('BORGMATIC_RUNTIME_DIRECTORY', None)


def test_main_with_invalid_json_raises():
    flexmock(module.borgmatic.logger).should_receive('configure_logging')
    flexmock(module).should_receive('stream_tarballs').never()

    try:
        module.os.environ['BORGMATIC_TARBALLS_CONFIG'] = '{'

        with pytest.raises(ValueError):
            module.main()
    finally:
        module.os.environ.pop('BORGMATIC_TARBALLS_CONFIG', None)


def test_main_with_missing_config_raises():
    flexmock(module.borgmatic.logger).should_receive('configure_logging')
    flexmock(module).should_receive('stream_tarballs').never()

    with pytest.raises(ValueError):
        module.main()


def test_main_with_missing_runtime_directory_raises():
    flexmock(module.borgmatic.logger).should_receive('configure_logging')
    flexmock(module).should_receive('stream_tarballs').never()

    try:
        module.os.environ['BORGMATIC_TARBALLS_CONFIG'] = '[]'

        with pytest.raises(ValueError):
            module.main()
    finally:
        module.os.environ.pop('BORGMATIC_TARBALLS_CONFIG', None)
