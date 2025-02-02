import collections
import itertools
import sys
from argparse import ArgumentParser

from borgmatic.config import collect

ACTION_ALIASES = {
    'repo-create': ['rcreate', 'init', '-I'],
    'prune': ['-p'],
    'compact': [],
    'create': ['-C'],
    'check': ['-k'],
    'config': [],
    'delete': [],
    'extract': ['-x'],
    'export-tar': [],
    'mount': ['-m'],
    'umount': ['-u'],
    'restore': ['-r'],
    'repo-delete': ['rdelete'],
    'repo-list': ['rlist'],
    'list': ['-l'],
    'repo-info': ['rinfo'],
    'info': ['-i'],
    'transfer': [],
    'break-lock': [],
    'key': [],
    'borg': [],
}


def get_subaction_parsers(action_parser):
    '''
    Given an argparse.ArgumentParser instance, lookup the subactions in it and return a dict from
    subaction name to subaction parser.
    '''
    if not action_parser._subparsers:
        return {}

    return {
        subaction_name: subaction_parser
        for group_action in action_parser._subparsers._group_actions
        for subaction_name, subaction_parser in group_action.choices.items()
    }


def get_subactions_for_actions(action_parsers):
    '''
    Given a dict from action name to an argparse.ArgumentParser instance, make a map from action
    name to the names of contained sub-actions.
    '''
    return {
        action: tuple(
            subaction_name
            for group_action in action_parser._subparsers._group_actions
            for subaction_name in group_action.choices.keys()
        )
        for action, action_parser in action_parsers.items()
        if action_parser._subparsers
    }


def omit_values_colliding_with_action_names(unparsed_arguments, parsed_arguments):
    '''
    Given a sequence of string arguments and a dict from action name to parsed argparse.Namespace
    arguments, return the string arguments with any values omitted that happen to be the same as
    the name of a borgmatic action.

    This prevents, for instance, "check --only extract" from triggering the "extract" action.
    '''
    remaining_arguments = list(unparsed_arguments)

    for action_name, parsed in parsed_arguments.items():
        for value in vars(parsed).values():
            if isinstance(value, str):
                if value in ACTION_ALIASES.keys() and value in remaining_arguments:
                    remaining_arguments.remove(value)
            elif isinstance(value, list):
                for item in value:
                    if item in ACTION_ALIASES.keys() and item in remaining_arguments:
                        remaining_arguments.remove(item)

    return tuple(remaining_arguments)


def parse_and_record_action_arguments(
    unparsed_arguments, parsed_arguments, action_parser, action_name, canonical_name=None
):
    '''
    Given unparsed arguments as a sequence of strings, parsed arguments as a dict from action name
    to parsed argparse.Namespace, a parser to parse with, an action name, and an optional canonical
    action name (in case this the action name is an alias), parse the arguments and return a list of
    any remaining string arguments that were not parsed. Also record the parsed argparse.Namespace
    by setting it into the given parsed arguments. Return None if no parsing occurs because the
    given action doesn't apply to the given unparsed arguments.
    '''
    filtered_arguments = omit_values_colliding_with_action_names(
        unparsed_arguments, parsed_arguments
    )

    if action_name not in filtered_arguments:
        return tuple(unparsed_arguments)

    parsed, remaining = action_parser.parse_known_args(filtered_arguments)
    parsed_arguments[canonical_name or action_name] = parsed

    # Special case: If this is a "borg" action, greedily consume all arguments after (+1) the "borg"
    # argument.
    if action_name == 'borg':
        borg_options_index = remaining.index('borg') + 1
        parsed_arguments['borg'].options = remaining[borg_options_index:]
        remaining = remaining[:borg_options_index]

    return tuple(argument for argument in remaining if argument != action_name)


def argument_is_flag(argument):
    '''
    Return True if the given argument looks like a flag, e.g. '--some-flag', as opposed to a
    non-flag value.
    '''
    return isinstance(argument, str) and argument.startswith('--')


def group_arguments_with_values(arguments):
    '''
    Given a sequence of arguments, return a sequence of tuples where each one contains either a
    single argument (such as for a stand-alone flag) or a flag argument and its corresponding value.

    For instance, given the following arguments sequence as input:

      ('--foo', '--bar', '33', '--baz')

    ... return the following output:

      (('--foo',), ('--bar', '33'), ('--baz',))
    '''
    grouped_arguments = []
    index = 0

    while index < len(arguments):
        this_argument = arguments[index]

        try:
            next_argument = arguments[index + 1]
        except IndexError:
            grouped_arguments.append((this_argument,))
            break

        if (
            argument_is_flag(this_argument)
            and not argument_is_flag(next_argument)
            and next_argument not in ACTION_ALIASES
        ):
            grouped_arguments.append((this_argument, next_argument))
            index += 2
            continue

        grouped_arguments.append((this_argument,))
        index += 1

    return tuple(grouped_arguments)


def get_unparsable_arguments(remaining_action_arguments):
    '''
    Given a sequence of argument tuples (one per action parser that parsed arguments), determine the
    remaining arguments that no action parsers have consumed.
    '''
    if not remaining_action_arguments:
        return ()

    grouped_action_arguments = tuple(
        group_arguments_with_values(action_arguments)
        for action_arguments in remaining_action_arguments
    )

    return tuple(
        itertools.chain.from_iterable(
            argument_group
            for argument_group in dict.fromkeys(
                itertools.chain.from_iterable(grouped_action_arguments)
            ).keys()
            if all(
                argument_group in action_arguments for action_arguments in grouped_action_arguments
            )
        )
    )


def parse_arguments_for_actions(unparsed_arguments, action_parsers, global_parser):
    '''
    Given a sequence of arguments, a dict from action name to argparse.ArgumentParser instance,
    and the global parser as a argparse.ArgumentParser instance, give each requested action's
    parser a shot at parsing all arguments. This allows common arguments like "--repository" to be
    shared across multiple action parsers.

    Return the result as a tuple of: (a dict mapping from action name to an argparse.Namespace of
    parsed arguments, a tuple of argument tuples where each is the remaining arguments not claimed
    by any action parser).
    '''
    arguments = collections.OrderedDict()
    help_requested = bool('--help' in unparsed_arguments or '-h' in unparsed_arguments)
    remaining_action_arguments = []
    alias_to_action_name = {
        alias: action_name for action_name, aliases in ACTION_ALIASES.items() for alias in aliases
    }

    # If the "borg" action is used, skip all other action parsers. This avoids confusion like
    # "borg list" triggering borgmatic's own list action.
    if 'borg' in unparsed_arguments:
        action_parsers = {'borg': action_parsers['borg']}

    # Ask each action parser, one by one, to parse arguments.
    for argument in unparsed_arguments:
        action_name = argument
        canonical_name = alias_to_action_name.get(action_name, action_name)
        action_parser = action_parsers.get(action_name)

        if not action_parser:
            continue

        subaction_parsers = get_subaction_parsers(action_parser)

        # But first parse with subaction parsers, if any.
        if subaction_parsers:
            subactions_parsed = False

            for subaction_name, subaction_parser in subaction_parsers.items():
                remaining_action_arguments.append(
                    tuple(
                        argument
                        for argument in parse_and_record_action_arguments(
                            unparsed_arguments,
                            arguments,
                            subaction_parser,
                            subaction_name,
                        )
                        if argument != action_name
                    )
                )

                if subaction_name in arguments:
                    subactions_parsed = True

            if not subactions_parsed:
                if help_requested:
                    action_parser.print_help()
                    sys.exit(0)
                else:
                    raise ValueError(
                        f"Missing sub-action after {action_name} action. Expected one of: {', '.join(get_subactions_for_actions(action_parsers)[action_name])}"
                    )
        # Otherwise, parse with the main action parser.
        else:
            remaining_action_arguments.append(
                parse_and_record_action_arguments(
                    unparsed_arguments, arguments, action_parser, action_name, canonical_name
                )
            )

    # If no actions were explicitly requested, assume defaults.
    if not arguments and not help_requested:
        for default_action_name in ('create', 'prune', 'compact', 'check'):
            default_action_parser = action_parsers[default_action_name]
            remaining_action_arguments.append(
                parse_and_record_action_arguments(
                    tuple(unparsed_arguments) + (default_action_name,),
                    arguments,
                    default_action_parser,
                    default_action_name,
                )
            )

    arguments['global'], remaining = global_parser.parse_known_args(unparsed_arguments)
    remaining_action_arguments.append(remaining)

    return (
        arguments,
        tuple(remaining_action_arguments) if arguments else unparsed_arguments,
    )


def make_parsers():
    '''
    Build a global arguments parser, individual action parsers, and a combined parser containing
    both. Return them as a tuple. The global parser is useful for parsing just global arguments
    while ignoring actions, and the combined parser is handy for displaying help that includes
    everything: global flags, a list of actions, etc.
    '''
    config_paths = collect.get_default_config_paths(expand_home=True)
    unexpanded_config_paths = collect.get_default_config_paths(expand_home=False)

    global_parser = ArgumentParser(add_help=False)
    global_group = global_parser.add_argument_group('global arguments')

    global_group.add_argument(
        '-c',
        '--config',
        dest='config_paths',
        action='append',
        help=f"Configuration filename or directory, can specify flag multiple times, defaults to: -c {' -c '.join(unexpanded_config_paths)}",
    )
    global_group.add_argument(
        '-n',
        '--dry-run',
        dest='dry_run',
        action='store_true',
        help='Go through the motions, but do not actually write to any repositories',
    )
    global_group.add_argument(
        '-nc', '--no-color', dest='no_color', action='store_true', help='Disable colored output'
    )
    global_group.add_argument(
        '-v',
        '--verbosity',
        type=int,
        choices=range(-2, 3),
        default=0,
        help='Display verbose progress to the console: -2 (disabled), -1 (errors only), 0 (responses to actions, the default), 1 (info about steps borgmatic is taking), or 2 (debug)',
    )
    global_group.add_argument(
        '--syslog-verbosity',
        type=int,
        choices=range(-2, 3),
        default=-2,
        help='Log verbose progress to syslog: -2 (disabled, the default), -1 (errors only), 0 (responses to actions), 1 (info about steps borgmatic is taking), or 2 (debug)',
    )
    global_group.add_argument(
        '--log-file-verbosity',
        type=int,
        choices=range(-2, 3),
        default=1,
        help='When --log-file is given, log verbose progress to file: -2 (disabled), -1 (errors only), 0 (responses to actions), 1 (info about steps borgmatic is taking, the default), or 2 (debug)',
    )
    global_group.add_argument(
        '--monitoring-verbosity',
        type=int,
        choices=range(-2, 3),
        default=1,
        help='When a monitoring integration supporting logging is configured, log verbose progress to it: -2 (disabled), -1 (errors only), responses to actions (0), 1 (info about steps borgmatic is taking, the default), or 2 (debug)',
    )
    global_group.add_argument(
        '--log-file',
        type=str,
        help='Write log messages to this file instead of syslog',
    )
    global_group.add_argument(
        '--log-file-format',
        type=str,
        help='Python format string used for log messages written to the log file',
    )
    global_group.add_argument(
        '--log-json',
        action='store_true',
        help='Write Borg log messages and console output as one JSON object per log line instead of formatted text',
    )
    global_group.add_argument(
        '--override',
        metavar='OPTION.SUBOPTION=VALUE',
        dest='overrides',
        action='append',
        help='Configuration file option to override with specified value, see documentation for overriding list or key/value options, can specify flag multiple times',
    )
    global_group.add_argument(
        '--no-environment-interpolation',
        dest='resolve_env',
        action='store_false',
        help='Do not resolve environment variables in configuration file',
    )
    global_group.add_argument(
        '--bash-completion',
        default=False,
        action='store_true',
        help='Show bash completion script and exit',
    )
    global_group.add_argument(
        '--fish-completion',
        default=False,
        action='store_true',
        help='Show fish completion script and exit',
    )
    global_group.add_argument(
        '--version',
        dest='version',
        default=False,
        action='store_true',
        help='Display installed version number of borgmatic and exit',
    )

    global_plus_action_parser = ArgumentParser(
        description='''
            Simple, configuration-driven backup software for servers and workstations. If no actions
            are given, then borgmatic defaults to: create, prune, compact, and check.
            ''',
        parents=[global_parser],
    )

    action_parsers = global_plus_action_parser.add_subparsers(
        title='actions',
        metavar='',
        help='Specify zero or more actions. Defaults to create, prune, compact, and check. Use --help with action for details:',
    )
    repo_create_parser = action_parsers.add_parser(
        'repo-create',
        aliases=ACTION_ALIASES['repo-create'],
        help='Create a new, empty Borg repository',
        description='Create a new, empty Borg repository',
        add_help=False,
    )
    repo_create_group = repo_create_parser.add_argument_group('repo-create arguments')
    repo_create_group.add_argument(
        '-e',
        '--encryption',
        dest='encryption_mode',
        help='Borg repository encryption mode',
        required=True,
    )
    repo_create_group.add_argument(
        '--source-repository',
        '--other-repo',
        metavar='KEY_REPOSITORY',
        help='Path to an existing Borg repository whose key material should be reused [Borg 2.x+ only]',
    )
    repo_create_group.add_argument(
        '--repository',
        help='Path of the new repository to create (must be already specified in a borgmatic configuration file), defaults to the configured repository if there is only one, quoted globs supported',
    )
    repo_create_group.add_argument(
        '--copy-crypt-key',
        action='store_true',
        help='Copy the crypt key used for authenticated encryption from the source repository, defaults to a new random key [Borg 2.x+ only]',
    )
    repo_create_group.add_argument(
        '--append-only',
        action='store_true',
        help='Create an append-only repository',
    )
    repo_create_group.add_argument(
        '--storage-quota',
        help='Create a repository with a fixed storage quota',
    )
    repo_create_group.add_argument(
        '--make-parent-dirs',
        action='store_true',
        help='Create any missing parent directories of the repository directory',
    )
    repo_create_group.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit'
    )

    transfer_parser = action_parsers.add_parser(
        'transfer',
        aliases=ACTION_ALIASES['transfer'],
        help='Transfer archives from one repository to another, optionally upgrading the transferred data [Borg 2.0+ only]',
        description='Transfer archives from one repository to another, optionally upgrading the transferred data [Borg 2.0+ only]',
        add_help=False,
    )
    transfer_group = transfer_parser.add_argument_group('transfer arguments')
    transfer_group.add_argument(
        '--repository',
        help='Path of existing destination repository to transfer archives to, defaults to the configured repository if there is only one, quoted globs supported',
    )
    transfer_group.add_argument(
        '--source-repository',
        help='Path of existing source repository to transfer archives from',
        required=True,
    )
    transfer_group.add_argument(
        '--archive',
        help='Name or hash of a single archive to transfer (or "latest"), defaults to transferring all archives',
    )
    transfer_group.add_argument(
        '--upgrader',
        help='Upgrader type used to convert the transferred data, e.g. "From12To20" to upgrade data from Borg 1.2 to 2.0 format, defaults to no conversion',
    )
    transfer_group.add_argument(
        '--progress',
        default=False,
        action='store_true',
        help='Display progress as each archive is transferred',
    )
    transfer_group.add_argument(
        '-a',
        '--match-archives',
        '--glob-archives',
        metavar='PATTERN',
        help='Only transfer archives with names, hashes, or series matching this pattern',
    )
    transfer_group.add_argument(
        '--sort-by', metavar='KEYS', help='Comma-separated list of sorting keys'
    )
    transfer_group.add_argument(
        '--first',
        metavar='N',
        help='Only transfer first N archives after other filters are applied',
    )
    transfer_group.add_argument(
        '--last', metavar='N', help='Only transfer last N archives after other filters are applied'
    )
    transfer_group.add_argument(
        '--oldest',
        metavar='TIMESPAN',
        help='Transfer archives within a specified time range starting from the timestamp of the oldest archive (e.g. 7d or 12m) [Borg 2.x+ only]',
    )
    transfer_group.add_argument(
        '--newest',
        metavar='TIMESPAN',
        help='Transfer archives within a time range that ends at timestamp of the newest archive and starts a specified time range ago (e.g. 7d or 12m) [Borg 2.x+ only]',
    )
    transfer_group.add_argument(
        '--older',
        metavar='TIMESPAN',
        help='Transfer archives that are older than the specified time range (e.g. 7d or 12m) from the current time [Borg 2.x+ only]',
    )
    transfer_group.add_argument(
        '--newer',
        metavar='TIMESPAN',
        help='Transfer archives that are newer than the specified time range (e.g. 7d or 12m) from the current time [Borg 2.x+ only]',
    )
    transfer_group.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit'
    )

    prune_parser = action_parsers.add_parser(
        'prune',
        aliases=ACTION_ALIASES['prune'],
        help='Prune archives according to the retention policy (with Borg 1.2+, you must run compact afterwards to actually free space)',
        description='Prune archives according to the retention policy (with Borg 1.2+, you must run compact afterwards to actually free space)',
        add_help=False,
    )
    prune_group = prune_parser.add_argument_group('prune arguments')
    prune_group.add_argument(
        '--repository',
        help='Path of specific existing repository to prune (must be already specified in a borgmatic configuration file), quoted globs supported',
    )
    prune_group.add_argument(
        '-a',
        '--match-archives',
        '--glob-archives',
        metavar='PATTERN',
        help='When pruning, only consider archives with names, hashes, or series matching this pattern',
    )
    prune_group.add_argument(
        '--stats',
        dest='stats',
        default=False,
        action='store_true',
        help='Display statistics of the pruned archive',
    )
    prune_group.add_argument(
        '--list', dest='list_archives', action='store_true', help='List archives kept/pruned'
    )
    prune_group.add_argument(
        '--oldest',
        metavar='TIMESPAN',
        help='Prune archives within a specified time range starting from the timestamp of the oldest archive (e.g. 7d or 12m) [Borg 2.x+ only]',
    )
    prune_group.add_argument(
        '--newest',
        metavar='TIMESPAN',
        help='Prune archives within a time range that ends at timestamp of the newest archive and starts a specified time range ago (e.g. 7d or 12m) [Borg 2.x+ only]',
    )
    prune_group.add_argument(
        '--older',
        metavar='TIMESPAN',
        help='Prune archives that are older than the specified time range (e.g. 7d or 12m) from the current time [Borg 2.x+ only]',
    )
    prune_group.add_argument(
        '--newer',
        metavar='TIMESPAN',
        help='Prune archives that are newer than the specified time range (e.g. 7d or 12m) from the current time [Borg 2.x+ only]',
    )
    prune_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    compact_parser = action_parsers.add_parser(
        'compact',
        aliases=ACTION_ALIASES['compact'],
        help='Compact segments to free space [Borg 1.2+, borgmatic 1.5.23+ only]',
        description='Compact segments to free space [Borg 1.2+, borgmatic 1.5.23+ only]',
        add_help=False,
    )
    compact_group = compact_parser.add_argument_group('compact arguments')
    compact_group.add_argument(
        '--repository',
        help='Path of specific existing repository to compact (must be already specified in a borgmatic configuration file), quoted globs supported',
    )
    compact_group.add_argument(
        '--progress',
        dest='progress',
        default=False,
        action='store_true',
        help='Display progress as each segment is compacted',
    )
    compact_group.add_argument(
        '--cleanup-commits',
        dest='cleanup_commits',
        default=False,
        action='store_true',
        help='Cleanup commit-only 17-byte segment files left behind by Borg 1.1 [flag in Borg 1.2 only]',
    )
    compact_group.add_argument(
        '--threshold',
        type=int,
        dest='threshold',
        help='Minimum saved space percentage threshold for compacting a segment, defaults to 10',
    )
    compact_group.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit'
    )

    create_parser = action_parsers.add_parser(
        'create',
        aliases=ACTION_ALIASES['create'],
        help='Create an archive (actually perform a backup)',
        description='Create an archive (actually perform a backup)',
        add_help=False,
    )
    create_group = create_parser.add_argument_group('create arguments')
    create_group.add_argument(
        '--repository',
        help='Path of specific existing repository to backup to (must be already specified in a borgmatic configuration file), quoted globs supported',
    )
    create_group.add_argument(
        '--progress',
        dest='progress',
        default=False,
        action='store_true',
        help='Display progress for each file as it is backed up',
    )
    create_group.add_argument(
        '--stats',
        dest='stats',
        default=False,
        action='store_true',
        help='Display statistics of archive',
    )
    create_group.add_argument(
        '--list', '--files', dest='list_files', action='store_true', help='Show per-file details'
    )
    create_group.add_argument(
        '--json', dest='json', default=False, action='store_true', help='Output results as JSON'
    )
    create_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    check_parser = action_parsers.add_parser(
        'check',
        aliases=ACTION_ALIASES['check'],
        help='Check archives for consistency',
        description='Check archives for consistency',
        add_help=False,
    )
    check_group = check_parser.add_argument_group('check arguments')
    check_group.add_argument(
        '--repository',
        help='Path of specific existing repository to check (must be already specified in a borgmatic configuration file), quoted globs supported',
    )
    check_group.add_argument(
        '--progress',
        dest='progress',
        default=False,
        action='store_true',
        help='Display progress for each file as it is checked',
    )
    check_group.add_argument(
        '--repair',
        dest='repair',
        default=False,
        action='store_true',
        help='Attempt to repair any inconsistencies found (for interactive use)',
    )
    check_group.add_argument(
        '--max-duration',
        metavar='SECONDS',
        help='How long to check the repository before interrupting the check, defaults to no interruption',
    )
    check_group.add_argument(
        '-a',
        '--match-archives',
        '--glob-archives',
        metavar='PATTERN',
        help='Only check archives with names, hashes, or series matching this pattern',
    )
    check_group.add_argument(
        '--only',
        metavar='CHECK',
        choices=('repository', 'archives', 'data', 'extract', 'spot'),
        dest='only_checks',
        action='append',
        help='Run a particular consistency check (repository, archives, data, extract, or spot) instead of configured checks (subject to configured frequency, can specify flag multiple times)',
    )
    check_group.add_argument(
        '--force',
        default=False,
        action='store_true',
        help='Ignore configured check frequencies and run checks unconditionally',
    )
    check_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    delete_parser = action_parsers.add_parser(
        'delete',
        aliases=ACTION_ALIASES['delete'],
        help='Delete an archive from a repository or delete an entire repository (with Borg 1.2+, you must run compact afterwards to actually free space)',
        description='Delete an archive from a repository or delete an entire repository (with Borg 1.2+, you must run compact afterwards to actually free space)',
        add_help=False,
    )
    delete_group = delete_parser.add_argument_group('delete arguments')
    delete_group.add_argument(
        '--repository',
        help='Path of repository to delete or delete archives from, defaults to the configured repository if there is only one, quoted globs supported',
    )
    delete_group.add_argument(
        '--archive',
        help='Archive name, hash, or series to delete',
    )
    delete_group.add_argument(
        '--list',
        dest='list_archives',
        action='store_true',
        help='Show details for the deleted archives',
    )
    delete_group.add_argument(
        '--stats',
        action='store_true',
        help='Display statistics for the deleted archives',
    )
    delete_group.add_argument(
        '--cache-only',
        action='store_true',
        help='Delete only the local cache for the given repository',
    )
    delete_group.add_argument(
        '--force',
        action='count',
        help='Force deletion of corrupted archives, can be given twice if once does not work',
    )
    delete_group.add_argument(
        '--keep-security-info',
        action='store_true',
        help='Do not delete the local security info when deleting a repository',
    )
    delete_group.add_argument(
        '--save-space',
        action='store_true',
        help='Work slower, but using less space [Not supported in Borg 2.x+]',
    )
    delete_group.add_argument(
        '--checkpoint-interval',
        type=int,
        metavar='SECONDS',
        help='Write a checkpoint at the given interval, defaults to 1800 seconds (30 minutes)',
    )
    delete_group.add_argument(
        '-a',
        '--match-archives',
        '--glob-archives',
        metavar='PATTERN',
        help='Only delete archives with names, hashes, or series matching this pattern',
    )
    delete_group.add_argument(
        '--sort-by', metavar='KEYS', help='Comma-separated list of sorting keys'
    )
    delete_group.add_argument(
        '--first', metavar='N', help='Delete first N archives after other filters are applied'
    )
    delete_group.add_argument(
        '--last', metavar='N', help='Delete last N archives after other filters are applied'
    )
    delete_group.add_argument(
        '--oldest',
        metavar='TIMESPAN',
        help='Delete archives within a specified time range starting from the timestamp of the oldest archive (e.g. 7d or 12m) [Borg 2.x+ only]',
    )
    delete_group.add_argument(
        '--newest',
        metavar='TIMESPAN',
        help='Delete archives within a time range that ends at timestamp of the newest archive and starts a specified time range ago (e.g. 7d or 12m) [Borg 2.x+ only]',
    )
    delete_group.add_argument(
        '--older',
        metavar='TIMESPAN',
        help='Delete archives that are older than the specified time range (e.g. 7d or 12m) from the current time [Borg 2.x+ only]',
    )
    delete_group.add_argument(
        '--newer',
        metavar='TIMESPAN',
        help='Delete archives that are newer than the specified time range (e.g. 7d or 12m) from the current time [Borg 2.x+ only]',
    )
    delete_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    extract_parser = action_parsers.add_parser(
        'extract',
        aliases=ACTION_ALIASES['extract'],
        help='Extract files from a named archive to the current directory',
        description='Extract a named archive to the current directory',
        add_help=False,
    )
    extract_group = extract_parser.add_argument_group('extract arguments')
    extract_group.add_argument(
        '--repository',
        help='Path of repository to extract, defaults to the configured repository if there is only one, quoted globs supported',
    )
    extract_group.add_argument(
        '--archive', help='Name or hash of a single archive to extract (or "latest")', required=True
    )
    extract_group.add_argument(
        '--path',
        '--restore-path',
        metavar='PATH',
        dest='paths',
        action='append',
        help='Path to extract from archive, can specify flag multiple times, defaults to the entire archive',
    )
    extract_group.add_argument(
        '--destination',
        metavar='PATH',
        dest='destination',
        help='Directory to extract files into, defaults to the current directory',
    )
    extract_group.add_argument(
        '--strip-components',
        type=lambda number: number if number == 'all' else int(number),
        metavar='NUMBER',
        help='Number of leading path components to remove from each extracted path or "all" to strip all leading path components. Skip paths with fewer elements',
    )
    extract_group.add_argument(
        '--progress',
        dest='progress',
        default=False,
        action='store_true',
        help='Display progress for each file as it is extracted',
    )
    extract_group.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit'
    )

    config_parser = action_parsers.add_parser(
        'config',
        aliases=ACTION_ALIASES['config'],
        help='Perform configuration file related operations',
        description='Perform configuration file related operations',
        add_help=False,
    )

    config_group = config_parser.add_argument_group('config arguments')
    config_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    config_parsers = config_parser.add_subparsers(
        title='config sub-actions',
    )

    config_bootstrap_parser = config_parsers.add_parser(
        'bootstrap',
        help='Extract the borgmatic configuration files from a named archive',
        description='Extract the borgmatic configuration files from a named archive',
        add_help=False,
    )
    config_bootstrap_group = config_bootstrap_parser.add_argument_group(
        'config bootstrap arguments'
    )
    config_bootstrap_group.add_argument(
        '--repository',
        help='Path of repository to extract config files from, quoted globs supported',
        required=True,
    )
    config_bootstrap_group.add_argument(
        '--local-path',
        help='Alternate Borg local executable. Defaults to "borg"',
        default='borg',
    )
    config_bootstrap_group.add_argument(
        '--remote-path',
        help='Alternate Borg remote executable. Defaults to "borg"',
        default='borg',
    )
    config_bootstrap_group.add_argument(
        '--user-runtime-directory',
        help='Path used for temporary runtime data like bootstrap metadata. Defaults to $XDG_RUNTIME_DIR or $TMPDIR or $TEMP or /var/run/$UID',
    )
    config_bootstrap_group.add_argument(
        '--borgmatic-source-directory',
        help='Deprecated. Path formerly used for temporary runtime data like bootstrap metadata. Defaults to ~/.borgmatic',
    )
    config_bootstrap_group.add_argument(
        '--archive',
        help='Name or hash of a single archive to extract config files from, defaults to "latest"',
        default='latest',
    )
    config_bootstrap_group.add_argument(
        '--destination',
        metavar='PATH',
        dest='destination',
        help='Directory to extract config files into, defaults to /',
        default='/',
    )
    config_bootstrap_group.add_argument(
        '--strip-components',
        type=lambda number: number if number == 'all' else int(number),
        metavar='NUMBER',
        help='Number of leading path components to remove from each extracted path or "all" to strip all leading path components. Skip paths with fewer elements',
    )
    config_bootstrap_group.add_argument(
        '--progress',
        dest='progress',
        default=False,
        action='store_true',
        help='Display progress for each file as it is extracted',
    )
    config_bootstrap_group.add_argument(
        '--ssh-command',
        metavar='COMMAND',
        help='Command to use instead of "ssh"',
    )
    config_bootstrap_group.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit'
    )

    config_generate_parser = config_parsers.add_parser(
        'generate',
        help='Generate a sample borgmatic configuration file',
        description='Generate a sample borgmatic configuration file',
        add_help=False,
    )
    config_generate_group = config_generate_parser.add_argument_group('config generate arguments')
    config_generate_group.add_argument(
        '-s',
        '--source',
        dest='source_filename',
        help='Optional configuration file to merge into the generated configuration, useful for upgrading your configuration',
    )
    config_generate_group.add_argument(
        '-d',
        '--destination',
        dest='destination_filename',
        default=config_paths[0],
        help=f'Destination configuration file, default: {unexpanded_config_paths[0]}',
    )
    config_generate_group.add_argument(
        '--overwrite',
        default=False,
        action='store_true',
        help='Whether to overwrite any existing destination file, defaults to false',
    )
    config_generate_group.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit'
    )

    config_validate_parser = config_parsers.add_parser(
        'validate',
        help='Validate borgmatic configuration files specified with --config (see borgmatic --help)',
        description='Validate borgmatic configuration files specified with --config (see borgmatic --help)',
        add_help=False,
    )
    config_validate_group = config_validate_parser.add_argument_group('config validate arguments')
    config_validate_group.add_argument(
        '-s',
        '--show',
        action='store_true',
        help='Show the validated configuration after all include merging has occurred',
    )
    config_validate_group.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit'
    )

    export_tar_parser = action_parsers.add_parser(
        'export-tar',
        aliases=ACTION_ALIASES['export-tar'],
        help='Export an archive to a tar-formatted file or stream',
        description='Export an archive to a tar-formatted file or stream',
        add_help=False,
    )
    export_tar_group = export_tar_parser.add_argument_group('export-tar arguments')
    export_tar_group.add_argument(
        '--repository',
        help='Path of repository to export from, defaults to the configured repository if there is only one, quoted globs supported',
    )
    export_tar_group.add_argument(
        '--archive', help='Name or hash of a single archive to export (or "latest")', required=True
    )
    export_tar_group.add_argument(
        '--path',
        metavar='PATH',
        dest='paths',
        action='append',
        help='Path to export from archive, can specify flag multiple times, defaults to the entire archive',
    )
    export_tar_group.add_argument(
        '--destination',
        metavar='PATH',
        dest='destination',
        help='Path to destination export tar file, or "-" for stdout (but be careful about dirtying output with --verbosity or --list)',
        required=True,
    )
    export_tar_group.add_argument(
        '--tar-filter', help='Name of filter program to pipe data through'
    )
    export_tar_group.add_argument(
        '--list', '--files', dest='list_files', action='store_true', help='Show per-file details'
    )
    export_tar_group.add_argument(
        '--strip-components',
        type=int,
        metavar='NUMBER',
        dest='strip_components',
        help='Number of leading path components to remove from each exported path. Skip paths with fewer elements',
    )
    export_tar_group.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit'
    )

    mount_parser = action_parsers.add_parser(
        'mount',
        aliases=ACTION_ALIASES['mount'],
        help='Mount files from a named archive as a FUSE filesystem',
        description='Mount a named archive as a FUSE filesystem',
        add_help=False,
    )
    mount_group = mount_parser.add_argument_group('mount arguments')
    mount_group.add_argument(
        '--repository',
        help='Path of repository to use, defaults to the configured repository if there is only one, quoted globs supported',
    )
    mount_group.add_argument(
        '--archive', help='Name or hash of a single archive to mount (or "latest")'
    )
    mount_group.add_argument(
        '--mount-point',
        metavar='PATH',
        dest='mount_point',
        help='Path where filesystem is to be mounted',
        required=True,
    )
    mount_group.add_argument(
        '--path',
        metavar='PATH',
        dest='paths',
        action='append',
        help='Path to mount from archive, can specify multiple times, defaults to the entire archive',
    )
    mount_group.add_argument(
        '--foreground',
        dest='foreground',
        default=False,
        action='store_true',
        help='Stay in foreground until ctrl-C is pressed',
    )
    mount_group.add_argument(
        '--first',
        metavar='N',
        help='Mount first N archives after other filters are applied',
    )
    mount_group.add_argument(
        '--last', metavar='N', help='Mount last N archives after other filters are applied'
    )
    mount_group.add_argument(
        '--oldest',
        metavar='TIMESPAN',
        help='Mount archives within a specified time range starting from the timestamp of the oldest archive (e.g. 7d or 12m) [Borg 2.x+ only]',
    )
    mount_group.add_argument(
        '--newest',
        metavar='TIMESPAN',
        help='Mount archives within a time range that ends at timestamp of the newest archive and starts a specified time range ago (e.g. 7d or 12m) [Borg 2.x+ only]',
    )
    mount_group.add_argument(
        '--older',
        metavar='TIMESPAN',
        help='Mount archives that are older than the specified time range (e.g. 7d or 12m) from the current time [Borg 2.x+ only]',
    )
    mount_group.add_argument(
        '--newer',
        metavar='TIMESPAN',
        help='Mount archives that are newer than the specified time range (e.g. 7d or 12m) from the current time [Borg 2.x+ only]',
    )
    mount_group.add_argument('--options', dest='options', help='Extra Borg mount options')
    mount_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    umount_parser = action_parsers.add_parser(
        'umount',
        aliases=ACTION_ALIASES['umount'],
        help='Unmount a FUSE filesystem that was mounted with "borgmatic mount"',
        description='Unmount a mounted FUSE filesystem',
        add_help=False,
    )
    umount_group = umount_parser.add_argument_group('umount arguments')
    umount_group.add_argument(
        '--mount-point',
        metavar='PATH',
        dest='mount_point',
        help='Path of filesystem to unmount',
        required=True,
    )
    umount_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    repo_delete_parser = action_parsers.add_parser(
        'repo-delete',
        aliases=ACTION_ALIASES['repo-delete'],
        help='Delete an entire repository (with Borg 1.2+, you must run compact afterwards to actually free space)',
        description='Delete an entire repository (with Borg 1.2+, you must run compact afterwards to actually free space)',
        add_help=False,
    )
    repo_delete_group = repo_delete_parser.add_argument_group('delete arguments')
    repo_delete_group.add_argument(
        '--repository',
        help='Path of repository to delete, defaults to the configured repository if there is only one, quoted globs supported',
    )
    repo_delete_group.add_argument(
        '--list',
        dest='list_archives',
        action='store_true',
        help='Show details for the archives in the given repository',
    )
    repo_delete_group.add_argument(
        '--force',
        action='count',
        help='Force deletion of corrupted archives, can be given twice if once does not work',
    )
    repo_delete_group.add_argument(
        '--cache-only',
        action='store_true',
        help='Delete only the local cache for the given repository',
    )
    repo_delete_group.add_argument(
        '--keep-security-info',
        action='store_true',
        help='Do not delete the local security info when deleting a repository',
    )
    repo_delete_group.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit'
    )

    restore_parser = action_parsers.add_parser(
        'restore',
        aliases=ACTION_ALIASES['restore'],
        help='Restore data source (e.g. database) dumps from a named archive',
        description='Restore data source (e.g. database) dumps from a named archive. (To extract files instead, use "borgmatic extract".)',
        add_help=False,
    )
    restore_group = restore_parser.add_argument_group('restore arguments')
    restore_group.add_argument(
        '--repository',
        help='Path of repository to restore from, defaults to the configured repository if there is only one, quoted globs supported',
    )
    restore_group.add_argument(
        '--archive',
        help='Name or hash of a single archive to restore from (or "latest")',
        required=True,
    )
    restore_group.add_argument(
        '--data-source',
        '--database',
        metavar='NAME',
        dest='data_sources',
        action='append',
        help="Name of data source (e.g. database) to restore from the archive, must be defined in borgmatic's configuration, can specify the flag multiple times, defaults to all data sources in the archive",
    )
    restore_group.add_argument(
        '--schema',
        metavar='NAME',
        dest='schemas',
        action='append',
        help='Name of schema to restore from the data source, can specify flag multiple times, defaults to all schemas. Schemas are only supported for PostgreSQL and MongoDB databases',
    )
    restore_group.add_argument(
        '--hostname',
        help='Database hostname to restore to. Defaults to the "restore_hostname" option in borgmatic\'s configuration',
    )
    restore_group.add_argument(
        '--port',
        help='Database port to restore to. Defaults to the "restore_port" option in borgmatic\'s configuration',
    )
    restore_group.add_argument(
        '--username',
        help='Username with which to connect to the database. Defaults to the "restore_username" option in borgmatic\'s configuration',
    )
    restore_group.add_argument(
        '--password',
        help='Password with which to connect to the restore database. Defaults to the "restore_password" option in borgmatic\'s configuration',
    )
    restore_group.add_argument(
        '--restore-path',
        help='Path to restore SQLite database dumps to. Defaults to the "restore_path" option in borgmatic\'s configuration',
    )
    restore_group.add_argument(
        '--original-hostname',
        help='The hostname where the dump to restore came from, only necessary if you need to disambiguate dumps',
    )
    restore_group.add_argument(
        '--original-port',
        type=int,
        help="The port where the dump to restore came from (if that port is in borgmatic's configuration), only necessary if you need to disambiguate dumps",
    )
    restore_group.add_argument(
        '--hook',
        help='The name of the data source hook for the dump to restore, only necessary if you need to disambiguate dumps',
    )
    restore_group.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit'
    )

    repo_list_parser = action_parsers.add_parser(
        'repo-list',
        aliases=ACTION_ALIASES['repo-list'],
        help='List repository',
        description='List the archives in a repository',
        add_help=False,
    )
    repo_list_group = repo_list_parser.add_argument_group('repo-list arguments')
    repo_list_group.add_argument(
        '--repository',
        help='Path of repository to list, defaults to the configured repositories, quoted globs supported',
    )
    repo_list_group.add_argument(
        '--short', default=False, action='store_true', help='Output only archive names'
    )
    repo_list_group.add_argument('--format', help='Format for archive listing')
    repo_list_group.add_argument(
        '--json', default=False, action='store_true', help='Output results as JSON'
    )
    repo_list_group.add_argument(
        '-P', '--prefix', help='Deprecated. Only list archive names starting with this prefix'
    )
    repo_list_group.add_argument(
        '-a',
        '--match-archives',
        '--glob-archives',
        metavar='PATTERN',
        help='Only list archive names, hashes, or series matching this pattern',
    )
    repo_list_group.add_argument(
        '--sort-by', metavar='KEYS', help='Comma-separated list of sorting keys'
    )
    repo_list_group.add_argument(
        '--first', metavar='N', help='List first N archives after other filters are applied'
    )
    repo_list_group.add_argument(
        '--last', metavar='N', help='List last N archives after other filters are applied'
    )
    repo_list_group.add_argument(
        '--oldest',
        metavar='TIMESPAN',
        help='List archives within a specified time range starting from the timestamp of the oldest archive (e.g. 7d or 12m) [Borg 2.x+ only]',
    )
    repo_list_group.add_argument(
        '--newest',
        metavar='TIMESPAN',
        help='List archives within a time range that ends at timestamp of the newest archive and starts a specified time range ago (e.g. 7d or 12m) [Borg 2.x+ only]',
    )
    repo_list_group.add_argument(
        '--older',
        metavar='TIMESPAN',
        help='List archives that are older than the specified time range (e.g. 7d or 12m) from the current time [Borg 2.x+ only]',
    )
    repo_list_group.add_argument(
        '--newer',
        metavar='TIMESPAN',
        help='List archives that are newer than the specified time range (e.g. 7d or 12m) from the current time [Borg 2.x+ only]',
    )
    repo_list_group.add_argument(
        '--deleted',
        default=False,
        action='store_true',
        help="List only deleted archives that haven't yet been compacted [Borg 2.x+ only]",
    )
    repo_list_group.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit'
    )

    list_parser = action_parsers.add_parser(
        'list',
        aliases=ACTION_ALIASES['list'],
        help='List archive',
        description='List the files in an archive or search for a file across archives',
        add_help=False,
    )
    list_group = list_parser.add_argument_group('list arguments')
    list_group.add_argument(
        '--repository',
        help='Path of repository containing archive to list, defaults to the configured repositories, quoted globs supported',
    )
    list_group.add_argument(
        '--archive', help='Name or hash of a single archive to list (or "latest")'
    )
    list_group.add_argument(
        '--path',
        metavar='PATH',
        dest='paths',
        action='append',
        help='Path or pattern to list from a single selected archive (via "--archive"), can specify flag multiple times, defaults to listing the entire archive',
    )
    list_group.add_argument(
        '--find',
        metavar='PATH',
        dest='find_paths',
        action='append',
        help='Partial path or pattern to search for and list across multiple archives, can specify flag multiple times',
    )
    list_group.add_argument(
        '--short', default=False, action='store_true', help='Output only path names'
    )
    list_group.add_argument('--format', help='Format for file listing')
    list_group.add_argument(
        '--json', default=False, action='store_true', help='Output results as JSON'
    )
    list_group.add_argument(
        '-P', '--prefix', help='Deprecated. Only list archive names starting with this prefix'
    )
    list_group.add_argument(
        '-a',
        '--match-archives',
        '--glob-archives',
        metavar='PATTERN',
        help='Only list archive names matching this pattern',
    )
    list_group.add_argument(
        '--sort-by', metavar='KEYS', help='Comma-separated list of sorting keys'
    )
    list_group.add_argument(
        '--first', metavar='N', help='List first N archives after other filters are applied'
    )
    list_group.add_argument(
        '--last', metavar='N', help='List last N archives after other filters are applied'
    )
    list_group.add_argument(
        '-e', '--exclude', metavar='PATTERN', help='Exclude paths matching the pattern'
    )
    list_group.add_argument(
        '--exclude-from', metavar='FILENAME', help='Exclude paths from exclude file, one per line'
    )
    list_group.add_argument('--pattern', help='Include or exclude paths matching a pattern')
    list_group.add_argument(
        '--patterns-from',
        metavar='FILENAME',
        help='Include or exclude paths matching patterns from pattern file, one per line',
    )
    list_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    repo_info_parser = action_parsers.add_parser(
        'repo-info',
        aliases=ACTION_ALIASES['repo-info'],
        help='Show repository summary information such as disk space used',
        description='Show repository summary information such as disk space used',
        add_help=False,
    )
    repo_info_group = repo_info_parser.add_argument_group('repo-info arguments')
    repo_info_group.add_argument(
        '--repository',
        help='Path of repository to show info for, defaults to the configured repository if there is only one, quoted globs supported',
    )
    repo_info_group.add_argument(
        '--json', dest='json', default=False, action='store_true', help='Output results as JSON'
    )
    repo_info_group.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit'
    )

    info_parser = action_parsers.add_parser(
        'info',
        aliases=ACTION_ALIASES['info'],
        help='Show archive summary information such as disk space used',
        description='Show archive summary information such as disk space used',
        add_help=False,
    )
    info_group = info_parser.add_argument_group('info arguments')
    info_group.add_argument(
        '--repository',
        help='Path of repository containing archive to show info for, defaults to the configured repository if there is only one, quoted globs supported',
    )
    info_group.add_argument(
        '--archive', help='Archive name, hash, or series to show info for (or "latest")'
    )
    info_group.add_argument(
        '--json', dest='json', default=False, action='store_true', help='Output results as JSON'
    )
    info_group.add_argument(
        '-P',
        '--prefix',
        help='Deprecated. Only show info for archive names starting with this prefix',
    )
    info_group.add_argument(
        '-a',
        '--match-archives',
        '--glob-archives',
        metavar='PATTERN',
        help='Only show info for archive names, hashes, or series matching this pattern',
    )
    info_group.add_argument(
        '--sort-by', metavar='KEYS', help='Comma-separated list of sorting keys'
    )
    info_group.add_argument(
        '--first',
        metavar='N',
        help='Show info for first N archives after other filters are applied',
    )
    info_group.add_argument(
        '--last', metavar='N', help='Show info for last N archives after other filters are applied'
    )
    info_group.add_argument(
        '--oldest',
        metavar='TIMESPAN',
        help='Show info for archives within a specified time range starting from the timestamp of the oldest archive (e.g. 7d or 12m) [Borg 2.x+ only]',
    )
    info_group.add_argument(
        '--newest',
        metavar='TIMESPAN',
        help='Show info for archives within a time range that ends at timestamp of the newest archive and starts a specified time range ago (e.g. 7d or 12m) [Borg 2.x+ only]',
    )
    info_group.add_argument(
        '--older',
        metavar='TIMESPAN',
        help='Show info for archives that are older than the specified time range (e.g. 7d or 12m) from the current time [Borg 2.x+ only]',
    )
    info_group.add_argument(
        '--newer',
        metavar='TIMESPAN',
        help='Show info for archives that are newer than the specified time range (e.g. 7d or 12m) from the current time [Borg 2.x+ only]',
    )
    info_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    break_lock_parser = action_parsers.add_parser(
        'break-lock',
        aliases=ACTION_ALIASES['break-lock'],
        help='Break the repository and cache locks left behind by Borg aborting',
        description='Break Borg repository and cache locks left behind by Borg aborting',
        add_help=False,
    )
    break_lock_group = break_lock_parser.add_argument_group('break-lock arguments')
    break_lock_group.add_argument(
        '--repository',
        help='Path of repository to break the lock for, defaults to the configured repository if there is only one, quoted globs supported',
    )
    break_lock_group.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit'
    )

    key_parser = action_parsers.add_parser(
        'key',
        aliases=ACTION_ALIASES['key'],
        help='Perform repository key related operations',
        description='Perform repository key related operations',
        add_help=False,
    )

    key_group = key_parser.add_argument_group('key arguments')
    key_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    key_parsers = key_parser.add_subparsers(
        title='key sub-actions',
    )

    key_export_parser = key_parsers.add_parser(
        'export',
        help='Export a copy of the repository key for safekeeping in case the original goes missing or gets damaged',
        description='Export a copy of the repository key for safekeeping in case the original goes missing or gets damaged',
        add_help=False,
    )
    key_export_group = key_export_parser.add_argument_group('key export arguments')
    key_export_group.add_argument(
        '--paper',
        action='store_true',
        help='Export the key in a text format suitable for printing and later manual entry',
    )
    key_export_group.add_argument(
        '--qr-html',
        action='store_true',
        help='Export the key in an HTML format suitable for printing and later manual entry or QR code scanning',
    )
    key_export_group.add_argument(
        '--repository',
        help='Path of repository to export the key for, defaults to the configured repository if there is only one, quoted globs supported',
    )
    key_export_group.add_argument(
        '--path',
        metavar='PATH',
        help='Path to export the key to, defaults to stdout (but be careful about dirtying the output with --verbosity)',
    )
    key_export_group.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit'
    )

    key_change_passphrase_parser = key_parsers.add_parser(
        'change-passphrase',
        help='Change the passphrase protecting the repository key',
        description='Change the passphrase protecting the repository key',
        add_help=False,
    )
    key_change_passphrase_group = key_change_passphrase_parser.add_argument_group(
        'key change-passphrase arguments'
    )
    key_change_passphrase_group.add_argument(
        '--repository',
        help='Path of repository to change the passphrase for, defaults to the configured repository if there is only one, quoted globs supported',
    )
    key_change_passphrase_group.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit'
    )

    borg_parser = action_parsers.add_parser(
        'borg',
        aliases=ACTION_ALIASES['borg'],
        help='Run an arbitrary Borg command',
        description="Run an arbitrary Borg command based on borgmatic's configuration",
        add_help=False,
    )
    borg_group = borg_parser.add_argument_group('borg arguments')
    borg_group.add_argument(
        '--repository',
        help='Path of repository to pass to Borg, defaults to the configured repositories, quoted globs supported',
    )
    borg_group.add_argument(
        '--archive', help='Archive name, hash, or series to pass to Borg (or "latest")'
    )
    borg_group.add_argument(
        '--',
        metavar='OPTION',
        dest='options',
        nargs='+',
        help='Options to pass to Borg, command first ("create", "list", etc). "--" is optional. To specify the repository or the archive, you must use --repository or --archive instead of providing them here.',
    )
    borg_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    return global_parser, action_parsers, global_plus_action_parser


def parse_arguments(*unparsed_arguments):
    '''
    Given command-line arguments with which this script was invoked, parse the arguments and return
    them as a dict mapping from action name (or "global") to an argparse.Namespace instance.

    Raise ValueError if the arguments cannot be parsed.
    Raise SystemExit with an error code of 0 if "--help" was requested.
    '''
    global_parser, action_parsers, global_plus_action_parser = make_parsers()
    arguments, remaining_action_arguments = parse_arguments_for_actions(
        unparsed_arguments, action_parsers.choices, global_parser
    )

    if not arguments['global'].config_paths:
        arguments['global'].config_paths = collect.get_default_config_paths(expand_home=True)

    for action_name in ('bootstrap', 'generate', 'validate'):
        if (
            action_name in arguments.keys() and len(arguments.keys()) > 2
        ):  # 2 = 1 for 'global' + 1 for the action
            raise ValueError(
                f'The {action_name} action cannot be combined with other actions. Please run it separately.'
            )

    unknown_arguments = get_unparsable_arguments(remaining_action_arguments)

    if unknown_arguments:
        if '--help' in unknown_arguments or '-h' in unknown_arguments:
            global_plus_action_parser.print_help()
            sys.exit(0)

        global_plus_action_parser.print_usage()
        raise ValueError(
            f"Unrecognized argument{'s' if len(unknown_arguments) > 1 else ''}: {' '.join(unknown_arguments)}"
        )

    if 'create' in arguments and arguments['create'].list_files and arguments['create'].progress:
        raise ValueError(
            'With the create action, only one of --list (--files) and --progress flags can be used.'
        )
    if 'create' in arguments and arguments['create'].list_files and arguments['create'].json:
        raise ValueError(
            'With the create action, only one of --list (--files) and --json flags can be used.'
        )

    if (
        ('list' in arguments and 'repo-info' in arguments and arguments['list'].json)
        or ('list' in arguments and 'info' in arguments and arguments['list'].json)
        or ('repo-info' in arguments and 'info' in arguments and arguments['repo-info'].json)
    ):
        raise ValueError('With the --json flag, multiple actions cannot be used together.')

    if (
        'transfer' in arguments
        and arguments['transfer'].archive
        and arguments['transfer'].match_archives
    ):
        raise ValueError(
            'With the transfer action, only one of --archive and --match-archives flags can be used.'
        )

    if 'list' in arguments and (arguments['list'].prefix and arguments['list'].match_archives):
        raise ValueError(
            'With the list action, only one of --prefix or --match-archives flags can be used.'
        )

    if 'repo-list' in arguments and (
        arguments['repo-list'].prefix and arguments['repo-list'].match_archives
    ):
        raise ValueError(
            'With the repo-list action, only one of --prefix or --match-archives flags can be used.'
        )

    if 'info' in arguments and (
        (arguments['info'].archive and arguments['info'].prefix)
        or (arguments['info'].archive and arguments['info'].match_archives)
        or (arguments['info'].prefix and arguments['info'].match_archives)
    ):
        raise ValueError(
            'With the info action, only one of --archive, --prefix, or --match-archives flags can be used.'
        )

    if 'borg' in arguments and arguments['global'].dry_run:
        raise ValueError('With the borg action, --dry-run is not supported.')

    return arguments
