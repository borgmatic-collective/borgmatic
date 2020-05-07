import pytest
from flexmock import flexmock

from borgmatic.hooks import dump as module


def test_make_database_dump_path_joins_arguments():
    assert module.make_database_dump_path('/tmp', 'super_databases') == '/tmp/super_databases'


def test_make_database_dump_path_defaults_without_source_directory():
    assert module.make_database_dump_path(None, 'super_databases') == '~/.borgmatic/super_databases'


def test_make_database_dump_filename_uses_name_and_hostname():
    flexmock(module.os.path).should_receive('expanduser').and_return('databases')

    assert (
        module.make_database_dump_filename('databases', 'test', 'hostname')
        == 'databases/hostname/test'
    )


def test_make_database_dump_filename_without_hostname_defaults_to_localhost():
    flexmock(module.os.path).should_receive('expanduser').and_return('databases')

    assert module.make_database_dump_filename('databases', 'test') == 'databases/localhost/test'


def test_make_database_dump_filename_with_invalid_name_raises():
    flexmock(module.os.path).should_receive('expanduser').and_return('databases')

    with pytest.raises(ValueError):
        module.make_database_dump_filename('databases', 'invalid/name')


def test_create_named_pipe_for_dump_does_not_raise():
    flexmock(module.os).should_receive('makedirs')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.os).should_receive('mkfifo')

    module.create_named_pipe_for_dump('/path/to/pipe')


def test_remove_database_dumps_removes_dump_for_each_database():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    flexmock(module).should_receive('make_database_dump_filename').with_args(
        'databases', 'foo', None
    ).and_return('databases/localhost/foo')
    flexmock(module).should_receive('make_database_dump_filename').with_args(
        'databases', 'bar', None
    ).and_return('databases/localhost/bar')

    flexmock(module.os.path).should_receive('isdir').and_return(False)
    flexmock(module.os).should_receive('remove').with_args('databases/localhost/foo').once()
    flexmock(module.os).should_receive('remove').with_args('databases/localhost/bar').once()
    flexmock(module.os).should_receive('listdir').with_args('databases/localhost').and_return(
        ['bar']
    ).and_return([])

    flexmock(module.os).should_receive('rmdir').with_args('databases/localhost').once()

    module.remove_database_dumps('databases', databases, 'SuperDB', 'test.yaml', dry_run=False)


def test_remove_database_dumps_removes_dump_in_directory_format():
    databases = [{'name': 'foo'}]
    flexmock(module).should_receive('make_database_dump_filename').with_args(
        'databases', 'foo', None
    ).and_return('databases/localhost/foo')

    flexmock(module.os.path).should_receive('isdir').and_return(True)
    flexmock(module.os).should_receive('remove').never()
    flexmock(module.shutil).should_receive('rmtree').with_args('databases/localhost/foo').once()
    flexmock(module.os).should_receive('listdir').with_args('databases/localhost').and_return([])
    flexmock(module.os).should_receive('rmdir').with_args('databases/localhost').once()

    module.remove_database_dumps('databases', databases, 'SuperDB', 'test.yaml', dry_run=False)


def test_remove_database_dumps_with_dry_run_skips_removal():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    flexmock(module.os).should_receive('rmdir').never()
    flexmock(module.os).should_receive('remove').never()

    module.remove_database_dumps('databases', databases, 'SuperDB', 'test.yaml', dry_run=True)


def test_remove_database_dumps_without_databases_does_not_raise():
    module.remove_database_dumps('databases', [], 'SuperDB', 'test.yaml', dry_run=False)


def test_convert_glob_patterns_to_borg_patterns_removes_leading_slash():
    assert module.convert_glob_patterns_to_borg_patterns(('/etc/foo/bar',)) == ['sh:etc/foo/bar']
