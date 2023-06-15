from borgmatic.commands.completion import fish as module


def test_fish_completion_does_not_raise():
    assert module.fish_completion()
