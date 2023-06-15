from flexmock import flexmock

from borgmatic.commands.completion import bash as module


def test_parser_flags_flattens_and_joins_flags():
    assert (
        module.parser_flags(
            flexmock(
                _actions=[
                    flexmock(option_strings=['--foo', '--bar']),
                    flexmock(option_strings=['--baz']),
                ]
            )
        )
        == '--foo --bar --baz'
    )
