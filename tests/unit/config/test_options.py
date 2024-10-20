from flexmock import flexmock

from borgmatic.config import options as module


def test_get_working_directory_passes_through_plain_directory():
    flexmock(module.os.path).should_receive('expanduser').and_return('/home/foo')
    assert module.get_working_directory({'working_directory': '/home/foo'}) == '/home/foo'


def test_get_working_directory_expands_tildes():
    flexmock(module.os.path).should_receive('expanduser').and_return('/home/foo')
    assert module.get_working_directory({'working_directory': '~/foo'}) == '/home/foo'


def test_get_working_directory_handles_no_configured_directory():
    assert module.get_working_directory({}) is None
