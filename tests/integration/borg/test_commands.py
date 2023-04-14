import copy

from flexmock import flexmock

import borgmatic.borg.info
import borgmatic.borg.list
import borgmatic.borg.rlist
import borgmatic.borg.transfer
import borgmatic.commands.arguments


def assert_command_does_not_duplicate_flags(command, *args, **kwargs):
    '''
    Assert that the given Borg command sequence does not contain any duplicated flags, e.g.
    "--match-archives" twice anywhere in the command.
    '''
    flag_counts = {}

    for flag_name in command:
        if not flag_name.startswith('--'):
            continue

        if flag_name in flag_counts:
            flag_counts[flag_name] += 1
        else:
            flag_counts[flag_name] = 1

    assert flag_counts == {
        flag_name: 1 for flag_name in flag_counts
    }, f"Duplicate flags found in: {' '.join(command)}"


def fuzz_argument(arguments, argument_name):
    '''
    Given an argparse.Namespace instance of arguments and an argument name in it, copy the arguments
    namespace and set the argument name in the copy with a fake value. Return the copied arguments.

    This is useful for "fuzzing" a unit under test by passing it each possible argument in turn,
    making sure it doesn't blow up or duplicate Borg arguments.
    '''
    arguments_copy = copy.copy(arguments)
    value = getattr(arguments_copy, argument_name)
    setattr(arguments_copy, argument_name, not value if isinstance(value, bool) else 'value')

    return arguments_copy


def test_transfer_archives_command_does_not_duplicate_flags_or_raise():
    arguments = borgmatic.commands.arguments.parse_arguments(
        'transfer', '--source-repository', 'foo'
    )['transfer']
    flexmock(borgmatic.borg.transfer).should_receive('execute_command').replace_with(
        assert_command_does_not_duplicate_flags
    )

    for argument_name in dir(arguments):
        if argument_name.startswith('_'):
            continue

        borgmatic.borg.transfer.transfer_archives(
            False, 'repo', {}, '2.3.4', fuzz_argument(arguments, argument_name)
        )


def test_make_list_command_does_not_duplicate_flags_or_raise():
    arguments = borgmatic.commands.arguments.parse_arguments('list')['list']

    for argument_name in dir(arguments):
        if argument_name.startswith('_'):
            continue

        command = borgmatic.borg.list.make_list_command(
            'repo', {}, '2.3.4', fuzz_argument(arguments, argument_name)
        )

        assert_command_does_not_duplicate_flags(command)


def test_make_rlist_command_does_not_duplicate_flags_or_raise():
    arguments = borgmatic.commands.arguments.parse_arguments('rlist')['rlist']

    for argument_name in dir(arguments):
        if argument_name.startswith('_'):
            continue

        command = borgmatic.borg.rlist.make_rlist_command(
            'repo', {}, '2.3.4', fuzz_argument(arguments, argument_name)
        )

        assert_command_does_not_duplicate_flags(command)


def test_display_archives_info_command_does_not_duplicate_flags_or_raise():
    arguments = borgmatic.commands.arguments.parse_arguments('info')['info']
    flexmock(borgmatic.borg.info).should_receive('execute_command_and_capture_output').replace_with(
        assert_command_does_not_duplicate_flags
    )
    flexmock(borgmatic.borg.info).should_receive('execute_command').replace_with(
        assert_command_does_not_duplicate_flags
    )

    for argument_name in dir(arguments):
        if argument_name.startswith('_'):
            continue

        borgmatic.borg.info.display_archives_info(
            'repo', {}, '2.3.4', fuzz_argument(arguments, argument_name)
        )
