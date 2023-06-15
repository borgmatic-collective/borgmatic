from borgmatic.commands.completion import actions as module


def test_upgrade_message_does_not_raise():
    module.upgrade_message(
        language='English', upgrade_command='read a lot', completion_file='your brain'
    )
