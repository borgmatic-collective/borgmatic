import io
import sys

import pytest
from flexmock import flexmock

from borgmatic.hooks.data_source import dump as module


def test_make_data_source_dump_path_joins_arguments():
    assert module.make_data_source_dump_path('/tmp', 'super_databases') == '/tmp/super_databases'


def test_make_data_source_dump_filename_uses_name_and_hostname():
    assert (
        module.make_data_source_dump_filename('databases', 'test', 'hostname')
        == 'databases/hostname/test'
    )


def test_make_data_source_dump_filename_uses_name_and_hostname_and_port():
    assert (
        module.make_data_source_dump_filename('databases', 'test', 'hostname', 1234)
        == 'databases/hostname:1234/test'
    )


def test_make_data_source_dump_filename_users_label():
    assert (
        module.make_data_source_dump_filename('databases', 'test', 'hostname', 1234, 'custom_label')
        == 'databases/custom_label/test'
    )


def test_make_data_source_dump_filename_without_hostname_defaults_to_localhost():
    assert module.make_data_source_dump_filename('databases', 'test') == 'databases/localhost/test'


def test_make_data_source_dump_filename_with_invalid_name_raises():
    with pytest.raises(ValueError):
        module.make_data_source_dump_filename('databases', 'invalid/name')


def test_write_data_source_dumps_metadata_writes_json_to_file():
    dumps_metadata = [
        module.borgmatic.actions.restore.Dump('databases', 'foo'),
        module.borgmatic.actions.restore.Dump('databases', 'bar'),
    ]
    dumps_stream = io.StringIO('password')
    dumps_stream.name = '/run/borgmatic/databases/dumps.json'
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args(dumps_stream.name, 'w', encoding='utf-8').and_return(
        dumps_stream
    )
    flexmock(dumps_stream).should_receive('close')  # Prevent close() so getvalue() below works.

    module.write_data_source_dumps_metadata('/run/borgmatic', 'databases', dumps_metadata)

    assert (
        dumps_stream.getvalue()
        == '{"dumps": [{"data_source_name": "foo", "hook_name": "databases", "hostname": "localhost", "port": null}, {"data_source_name": "bar", "hook_name": "databases", "hostname": "localhost", "port": null}]}'
    )


def test_write_data_source_dumps_metadata_with_operating_system_error_raises():
    dumps_metadata = [
        module.borgmatic.actions.restore.Dump('databases', 'foo'),
        module.borgmatic.actions.restore.Dump('databases', 'bar'),
    ]
    dumps_stream = io.StringIO('password')
    dumps_stream.name = '/run/borgmatic/databases/dumps.json'
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args(dumps_stream.name, 'w', encoding='utf-8').and_raise(
        OSError
    )

    with pytest.raises(ValueError):
        module.write_data_source_dumps_metadata('/run/borgmatic', 'databases', dumps_metadata)


def test_parse_data_source_dumps_metadata_converts_json_to_dump_instances():
    dumps_json = '{"dumps": [{"data_source_name": "foo", "hook_name": "databases", "hostname": "localhost", "port": null}, {"data_source_name": "bar", "hook_name": "databases", "hostname": "example.org", "port": 1234}]}'

    assert module.parse_data_source_dumps_metadata(
        dumps_json, 'borgmatic/databases/dumps.json'
    ) == (
        module.borgmatic.actions.restore.Dump('databases', 'foo'),
        module.borgmatic.actions.restore.Dump('databases', 'bar', 'example.org', 1234),
    )


def test_parse_data_source_dumps_metadata_with_invalid_json_raises():
    with pytest.raises(ValueError):
        module.parse_data_source_dumps_metadata('[{', 'borgmatic/databases/dumps.json')


def test_parse_data_source_dumps_metadata_with_unknown_keys_raises():
    dumps_json = (
        '{"dumps": [{"data_source_name": "foo", "hook_name": "databases", "wtf": "is this"}]}'
    )

    with pytest.raises(ValueError):
        module.parse_data_source_dumps_metadata(dumps_json, 'borgmatic/databases/dumps.json')


def test_parse_data_source_dumps_metadata_with_missing_dumps_key_raises():
    dumps_json = '{"not": "what we are looking for"}'

    with pytest.raises(ValueError):
        module.parse_data_source_dumps_metadata(dumps_json, 'borgmatic/databases/dumps.json')


def test_create_parent_directory_for_dump_does_not_raise():
    flexmock(module.os).should_receive('makedirs')

    module.create_parent_directory_for_dump('/path/to/parent')


def test_create_named_pipe_for_dump_does_not_raise():
    flexmock(module).should_receive('create_parent_directory_for_dump')
    flexmock(module.os).should_receive('mkfifo')

    module.create_named_pipe_for_dump('/path/to/pipe')


def test_remove_data_source_dumps_removes_dump_path():
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.shutil).should_receive('rmtree').with_args('databases').once()

    module.remove_data_source_dumps('databases', 'SuperDB', dry_run=False)


def test_remove_data_source_dumps_with_dry_run_skips_removal():
    flexmock(module.os.path).should_receive('exists').never()
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps('databases', 'SuperDB', dry_run=True)


def test_remove_data_source_dumps_without_dump_path_present_skips_removal():
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps('databases', 'SuperDB', dry_run=False)


def test_convert_glob_patterns_to_borg_pattern_makes_multipart_regular_expression():
    assert (
        module.convert_glob_patterns_to_borg_pattern(('/etc/foo/bar', '/bar/*/baz'))
        == 're:(?s:etc/foo/bar)|(?s:bar/.*/baz)'
    )
