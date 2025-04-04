import argparse
import copy

from flexmock import flexmock

import borgmatic.borg.info
import borgmatic.borg.list
import borgmatic.borg.mount
import borgmatic.borg.prune
import borgmatic.borg.repo_list
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

    if '--json' in command:
        return '{}'


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
        {}, 'transfer', '--source-repository', 'foo'
    )['transfer']
    flexmock(borgmatic.borg.transfer).should_receive('execute_command').replace_with(
        assert_command_does_not_duplicate_flags
    )

    for argument_name in dir(arguments):
        if argument_name.startswith('_'):
            continue

        borgmatic.borg.transfer.transfer_archives(
            False,
            'repo',
            {},
            '2.3.4',
            fuzz_argument(arguments, argument_name),
            global_arguments=flexmock(log_json=False),
        )


def test_prune_archives_command_does_not_duplicate_flags_or_raise():
    arguments = borgmatic.commands.arguments.parse_arguments({}, 'prune')['prune']
    flexmock(borgmatic.borg.prune).should_receive('execute_command').replace_with(
        assert_command_does_not_duplicate_flags
    )

    for argument_name in dir(arguments):
        if argument_name.startswith('_'):
            continue

        borgmatic.borg.prune.prune_archives(
            False,
            'repo',
            {},
            '2.3.4',
            fuzz_argument(arguments, argument_name),
            argparse.Namespace(log_json=False),
        )


def test_mount_archive_command_does_not_duplicate_flags_or_raise():
    arguments = borgmatic.commands.arguments.parse_arguments({}, 'mount', '--mount-point', 'tmp')[
        'mount'
    ]
    flexmock(borgmatic.borg.mount).should_receive('execute_command').replace_with(
        assert_command_does_not_duplicate_flags
    )

    for argument_name in dir(arguments):
        if argument_name.startswith('_'):
            continue

        borgmatic.borg.mount.mount_archive(
            'repo',
            'archive',
            fuzz_argument(arguments, argument_name),
            {},
            '2.3.4',
            argparse.Namespace(log_json=False),
        )


def test_make_list_command_does_not_duplicate_flags_or_raise():
    arguments = borgmatic.commands.arguments.parse_arguments({}, 'list')['list']

    for argument_name in dir(arguments):
        if argument_name.startswith('_'):
            continue

        command = borgmatic.borg.list.make_list_command(
            'repo',
            {},
            '2.3.4',
            fuzz_argument(arguments, argument_name),
            argparse.Namespace(log_json=False),
        )

        assert_command_does_not_duplicate_flags(command)


def test_make_repo_list_command_does_not_duplicate_flags_or_raise():
    arguments = borgmatic.commands.arguments.parse_arguments({}, 'repo-list')['repo-list']

    for argument_name in dir(arguments):
        if argument_name.startswith('_'):
            continue

        command = borgmatic.borg.repo_list.make_repo_list_command(
            'repo',
            {},
            '2.3.4',
            fuzz_argument(arguments, argument_name),
            global_arguments=flexmock(log_json=True),
        )

        assert_command_does_not_duplicate_flags(command)


def test_display_archives_info_command_does_not_duplicate_flags_or_raise():
    arguments = borgmatic.commands.arguments.parse_arguments({}, 'info')['info']
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
            'repo',
            {},
            '2.3.4',
            fuzz_argument(arguments, argument_name),
            argparse.Namespace(log_json=False),
        )
