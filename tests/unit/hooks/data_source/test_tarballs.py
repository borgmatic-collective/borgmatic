import io
import pytest
import sys

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
        assert module.dump_data_sources(
            tarballs=tarballs,
            config=flexmock(),
            config_paths=flexmock(),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=flexmock(),
            dry_run=False,
        ) == (stream_process,)


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
        assert module.dump_data_sources(
            tarballs=tarballs,
            config=flexmock(),
            config_paths=flexmock(),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=flexmock(),
            dry_run=False,
        ) == (stream_process,)


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
