from flexmock import flexmock

from borgmatic.commands import generate_config as module


def test_main_does_not_raise():
    flexmock(module.borgmatic.commands.borgmatic).should_receive('main')

    module.main()
