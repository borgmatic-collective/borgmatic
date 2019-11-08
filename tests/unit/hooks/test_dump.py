import pytest
from flexmock import flexmock

from borgmatic.hooks import dump as module


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


def test_remove_database_dumps_removes_dump_for_each_database():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    flexmock(module).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/foo'
    ).and_return('databases/localhost/bar')
    flexmock(module.os).should_receive('listdir').and_return([])
    flexmock(module.os).should_receive('rmdir')

    for name in ('foo', 'bar'):
        flexmock(module.os).should_receive('remove').with_args(
            'databases/localhost/{}'.format(name)
        ).once()

    module.remove_database_dumps('databases', databases, 'SuperDB', 'test.yaml', dry_run=False)


def test_remove_database_dumps_with_dry_run_skips_removal():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    flexmock(module.os).should_receive('rmdir').never()
    flexmock(module.os).should_receive('remove').never()

    module.remove_database_dumps('databases', databases, 'SuperDB', 'test.yaml', dry_run=True)


def test_remove_database_dumps_without_databases_does_not_raise():
    module.remove_database_dumps('databases', [], 'SuperDB', 'test.yaml', dry_run=False)
