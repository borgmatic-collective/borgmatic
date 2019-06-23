import subprocess

from flexmock import flexmock

from borgmatic.commands import borgmatic as module


def test_borgmatic_version_matches_news_version():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    borgmatic_version = subprocess.check_output(('borgmatic', '--version')).decode('ascii')
    news_version = open('NEWS').readline()

    assert borgmatic_version == news_version
