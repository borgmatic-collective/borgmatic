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


def test_make_data_source_dump_filename_without_hostname_defaults_to_localhost():
    assert module.make_data_source_dump_filename('databases', 'test') == 'databases/localhost/test'


def test_make_data_source_dump_filename_with_invalid_name_raises():
    with pytest.raises(ValueError):
        module.make_data_source_dump_filename('databases', 'invalid/name')


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

    module.remove_data_source_dumps('databases', 'SuperDB', 'test.yaml', dry_run=False)


def test_remove_data_source_dumps_with_dry_run_skips_removal():
    flexmock(module.os.path).should_receive('exists').never()
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps('databases', 'SuperDB', 'test.yaml', dry_run=True)


def test_remove_data_source_dumps_without_dump_path_present_skips_removal():
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps('databases', 'SuperDB', 'test.yaml', dry_run=False)


def test_convert_glob_patterns_to_borg_pattern_makes_multipart_regular_expression():
    assert (
        module.convert_glob_patterns_to_borg_pattern(('/etc/foo/bar', '/bar/*/baz'))
        == 're:(?s:etc/foo/bar)|(?s:bar/.*/baz)'
    )
