import pytest
from flexmock import flexmock

from borgmatic.hooks import database as module


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
