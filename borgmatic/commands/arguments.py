import collections
from argparse import Action, ArgumentParser

from borgmatic.config import collect

SUBPARSER_ALIASES = {
    'init': ['--init', '-I'],
    'prune': ['--prune', '-p'],
    'compact': [],
    'create': ['--create', '-C'],
    'check': ['--check', '-k'],
    'extract': ['--extract', '-x'],
    'export-tar': ['--export-tar'],
    'mount': ['--mount', '-m'],
    'umount': ['--umount', '-u'],
    'restore': ['--restore', '-r'],
    'list': ['--list', '-l'],
    'info': ['--info', '-i'],
    'borg': [],
}


def parse_subparser_arguments(unparsed_arguments, subparsers):
    '''
    Given a sequence of arguments and a dict from subparser name to argparse.ArgumentParser
    instance, give each requested action's subparser a shot at parsing all arguments. This allows
    common arguments like "--repository" to be shared across multiple subparsers.

    Return the result as a tuple of (a dict mapping from subparser name to a parsed namespace of
    arguments, a list of remaining arguments not claimed by any subparser).
    '''
    arguments = collections.OrderedDict()
    remaining_arguments = list(unparsed_arguments)
    alias_to_subparser_name = {
        alias: subparser_name
        for subparser_name, aliases in SUBPARSER_ALIASES.items()
        for alias in aliases
    }

    # If the "borg" action is used, skip all other subparsers. This avoids confusion like
    # "borg list" triggering borgmatic's own list action.
    if 'borg' in unparsed_arguments:
        subparsers = {'borg': subparsers['borg']}

    for subparser_name, subparser in subparsers.items():
        if subparser_name not in remaining_arguments:
            continue

        canonical_name = alias_to_subparser_name.get(subparser_name, subparser_name)

        # If a parsed value happens to be the same as the name of a subparser, remove it from the
        # remaining arguments. This prevents, for instance, "check --only extract" from triggering
        # the "extract" subparser.
        parsed, unused_remaining = subparser.parse_known_args(unparsed_arguments)
        for value in vars(parsed).values():
            if isinstance(value, str):
                if value in subparsers:
                    remaining_arguments.remove(value)
            elif isinstance(value, list):
                for item in value:
                    if item in subparsers:
                        remaining_arguments.remove(item)

        arguments[canonical_name] = parsed

    # If no actions are explicitly requested, assume defaults: prune, compact, create, and check.
    if not arguments and '--help' not in unparsed_arguments and '-h' not in unparsed_arguments:
        for subparser_name in ('prune', 'compact', 'create', 'check'):
            subparser = subparsers[subparser_name]
            parsed, unused_remaining = subparser.parse_known_args(unparsed_arguments)
            arguments[subparser_name] = parsed

    remaining_arguments = list(unparsed_arguments)

    # Now ask each subparser, one by one, to greedily consume arguments.
    for subparser_name, subparser in subparsers.items():
        if subparser_name not in arguments.keys():
            continue

        subparser = subparsers[subparser_name]
        unused_parsed, remaining_arguments = subparser.parse_known_args(remaining_arguments)

    # Special case: If "borg" is present in the arguments, consume all arguments after (+1) the
    # "borg" action.
    if 'borg' in arguments:
        borg_options_index = remaining_arguments.index('borg') + 1
        arguments['borg'].options = remaining_arguments[borg_options_index:]
        remaining_arguments = remaining_arguments[:borg_options_index]

    # Remove the subparser names themselves.
    for subparser_name, subparser in subparsers.items():
        if subparser_name in remaining_arguments:
            remaining_arguments.remove(subparser_name)

    return (arguments, remaining_arguments)


class Extend_action(Action):
    '''
    An argparse action to support Python 3.8's "extend" action in older versions of Python.
    '''

    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest, None)

        if items:
            items.extend(values)
        else:
            setattr(namespace, self.dest, list(values))


def parse_arguments(*unparsed_arguments):
    '''
    Given command-line arguments with which this script was invoked, parse the arguments and return
    them as a dict mapping from subparser name (or "global") to an argparse.Namespace instance.
    '''
    config_paths = collect.get_default_config_paths(expand_home=True)
    unexpanded_config_paths = collect.get_default_config_paths(expand_home=False)

    global_parser = ArgumentParser(add_help=False)
    global_parser.register('action', 'extend', Extend_action)
    global_group = global_parser.add_argument_group('global arguments')

    global_group.add_argument(
        '-c',
        '--config',
        nargs='*',
        dest='config_paths',
        default=config_paths,
        help='Configuration filenames or directories, defaults to: {}'.format(
            ' '.join(unexpanded_config_paths)
        ),
    )
    global_group.add_argument(
        '--excludes',
        dest='excludes_filename',
        help='Deprecated in favor of exclude_patterns within configuration',
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
        choices=range(-1, 3),
        default=0,
        help='Display verbose progress to the console (from only errors to very verbose: -1, 0, 1, or 2)',
    )
    global_group.add_argument(
        '--syslog-verbosity',
        type=int,
        choices=range(-1, 3),
        default=0,
        help='Log verbose progress to syslog (from only errors to very verbose: -1, 0, 1, or 2). Ignored when console is interactive or --log-file is given',
    )
    global_group.add_argument(
        '--log-file-verbosity',
        type=int,
        choices=range(-1, 3),
        default=0,
        help='Log verbose progress to log file (from only errors to very verbose: -1, 0, 1, or 2). Only used when --log-file is given',
    )
    global_group.add_argument(
        '--monitoring-verbosity',
        type=int,
        choices=range(-1, 3),
        default=0,
        help='Log verbose progress to monitoring integrations that support logging (from only errors to very verbose: -1, 0, 1, or 2)',
    )
    global_group.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Write log messages to this file instead of syslog',
    )
    global_group.add_argument(
        '--override',
        metavar='SECTION.OPTION=VALUE',
        nargs='+',
        dest='overrides',
        action='extend',
        help='One or more configuration file options to override with specified values',
    )
    global_group.add_argument(
        '--version',
        dest='version',
        default=False,
        action='store_true',
        help='Display installed version number of borgmatic and exit',
    )

    top_level_parser = ArgumentParser(
        description='''
            Simple, configuration-driven backup software for servers and workstations. If none of
            the action options are given, then borgmatic defaults to: prune, compact, create, and
            check.
            ''',
        parents=[global_parser],
    )

    subparsers = top_level_parser.add_subparsers(
        title='actions',
        metavar='',
        help='Specify zero or more actions. Defaults to prune, compact, create, and check. Use --help with action for details:',
    )
    init_parser = subparsers.add_parser(
        'init',
        aliases=SUBPARSER_ALIASES['init'],
        help='Initialize an empty Borg repository',
        description='Initialize an empty Borg repository',
        add_help=False,
    )
    init_group = init_parser.add_argument_group('init arguments')
    init_group.add_argument(
        '-e',
        '--encryption',
        dest='encryption_mode',
        help='Borg repository encryption mode',
        required=True,
    )
    init_group.add_argument(
        '--append-only',
        dest='append_only',
        action='store_true',
        help='Create an append-only repository',
    )
    init_group.add_argument(
        '--storage-quota',
        dest='storage_quota',
        help='Create a repository with a fixed storage quota',
    )
    init_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    prune_parser = subparsers.add_parser(
        'prune',
        aliases=SUBPARSER_ALIASES['prune'],
        help='Prune archives according to the retention policy (with Borg 1.2+, run compact afterwards to actually free space)',
        description='Prune archives according to the retention policy (with Borg 1.2+, run compact afterwards to actually free space)',
        add_help=False,
    )
    prune_group = prune_parser.add_argument_group('prune arguments')
    prune_group.add_argument(
        '--stats',
        dest='stats',
        default=False,
        action='store_true',
        help='Display statistics of archive',
    )
    prune_group.add_argument(
        '--files', dest='files', default=False, action='store_true', help='Show per-file details'
    )
    prune_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    compact_parser = subparsers.add_parser(
        'compact',
        aliases=SUBPARSER_ALIASES['compact'],
        help='Compact segments to free space (Borg 1.2+ only)',
        description='Compact segments to free space (Borg 1.2+ only)',
        add_help=False,
    )
    compact_group = compact_parser.add_argument_group('compact arguments')
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
        help='Cleanup commit-only 17-byte segment files left behind by Borg 1.1',
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

    create_parser = subparsers.add_parser(
        'create',
        aliases=SUBPARSER_ALIASES['create'],
        help='Create archives (actually perform backups)',
        description='Create archives (actually perform backups)',
        add_help=False,
    )
    create_group = create_parser.add_argument_group('create arguments')
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
        '--files', dest='files', default=False, action='store_true', help='Show per-file details'
    )
    create_group.add_argument(
        '--json', dest='json', default=False, action='store_true', help='Output results as JSON'
    )
    create_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    check_parser = subparsers.add_parser(
        'check',
        aliases=SUBPARSER_ALIASES['check'],
        help='Check archives for consistency',
        description='Check archives for consistency',
        add_help=False,
    )
    check_group = check_parser.add_argument_group('check arguments')
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
        help='Attempt to repair any inconsistencies found (experimental and only for interactive use)',
    )
    check_group.add_argument(
        '--only',
        metavar='CHECK',
        choices=('repository', 'archives', 'data', 'extract'),
        dest='only',
        action='append',
        help='Run a particular consistency check (repository, archives, data, or extract) instead of configured checks; can specify flag multiple times',
    )
    check_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    extract_parser = subparsers.add_parser(
        'extract',
        aliases=SUBPARSER_ALIASES['extract'],
        help='Extract files from a named archive to the current directory',
        description='Extract a named archive to the current directory',
        add_help=False,
    )
    extract_group = extract_parser.add_argument_group('extract arguments')
    extract_group.add_argument(
        '--repository',
        help='Path of repository to extract, defaults to the configured repository if there is only one',
    )
    extract_group.add_argument(
        '--archive', help='Name of archive to extract (or "latest")', required=True
    )
    extract_group.add_argument(
        '--path',
        '--restore-path',
        metavar='PATH',
        nargs='+',
        dest='paths',
        help='Paths to extract from archive, defaults to the entire archive',
    )
    extract_group.add_argument(
        '--destination',
        metavar='PATH',
        dest='destination',
        help='Directory to extract files into, defaults to the current directory',
    )
    extract_group.add_argument(
        '--strip-components',
        type=int,
        metavar='NUMBER',
        dest='strip_components',
        help='Number of leading path components to remove from each extracted path. Skip paths with fewer elements',
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

    export_tar_parser = subparsers.add_parser(
        'export-tar',
        aliases=SUBPARSER_ALIASES['export-tar'],
        help='Export an archive to a tar-formatted file or stream',
        description='Export an archive to a tar-formatted file or stream',
        add_help=False,
    )
    export_tar_group = export_tar_parser.add_argument_group('export-tar arguments')
    export_tar_group.add_argument(
        '--repository',
        help='Path of repository to export from, defaults to the configured repository if there is only one',
    )
    export_tar_group.add_argument(
        '--archive', help='Name of archive to export (or "latest")', required=True
    )
    export_tar_group.add_argument(
        '--path',
        metavar='PATH',
        nargs='+',
        dest='paths',
        help='Paths to export from archive, defaults to the entire archive',
    )
    export_tar_group.add_argument(
        '--destination',
        metavar='PATH',
        dest='destination',
        help='Path to destination export tar file, or "-" for stdout (but be careful about dirtying output with --verbosity or --files)',
        required=True,
    )
    export_tar_group.add_argument(
        '--tar-filter', help='Name of filter program to pipe data through'
    )
    export_tar_group.add_argument(
        '--files', default=False, action='store_true', help='Show per-file details'
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

    mount_parser = subparsers.add_parser(
        'mount',
        aliases=SUBPARSER_ALIASES['mount'],
        help='Mount files from a named archive as a FUSE filesystem',
        description='Mount a named archive as a FUSE filesystem',
        add_help=False,
    )
    mount_group = mount_parser.add_argument_group('mount arguments')
    mount_group.add_argument(
        '--repository',
        help='Path of repository to use, defaults to the configured repository if there is only one',
    )
    mount_group.add_argument('--archive', help='Name of archive to mount (or "latest")')
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
        nargs='+',
        dest='paths',
        help='Paths to mount from archive, defaults to the entire archive',
    )
    mount_group.add_argument(
        '--foreground',
        dest='foreground',
        default=False,
        action='store_true',
        help='Stay in foreground until ctrl-C is pressed',
    )
    mount_group.add_argument('--options', dest='options', help='Extra Borg mount options')
    mount_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    umount_parser = subparsers.add_parser(
        'umount',
        aliases=SUBPARSER_ALIASES['umount'],
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

    restore_parser = subparsers.add_parser(
        'restore',
        aliases=SUBPARSER_ALIASES['restore'],
        help='Restore database dumps from a named archive',
        description='Restore database dumps from a named archive. (To extract files instead, use "borgmatic extract".)',
        add_help=False,
    )
    restore_group = restore_parser.add_argument_group('restore arguments')
    restore_group.add_argument(
        '--repository',
        help='Path of repository to restore from, defaults to the configured repository if there is only one',
    )
    restore_group.add_argument(
        '--archive', help='Name of archive to restore from (or "latest")', required=True
    )
    restore_group.add_argument(
        '--database',
        metavar='NAME',
        nargs='+',
        dest='databases',
        help='Names of databases to restore from archive, defaults to all databases. Note that any databases to restore must be defined in borgmatic\'s configuration',
    )
    restore_group.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit'
    )

    list_parser = subparsers.add_parser(
        'list',
        aliases=SUBPARSER_ALIASES['list'],
        help='List archives',
        description='List archives or the contents of an archive',
        add_help=False,
    )
    list_group = list_parser.add_argument_group('list arguments')
    list_group.add_argument(
        '--repository', help='Path of repository to list, defaults to the configured repositories',
    )
    list_group.add_argument('--archive', help='Name of archive to list (or "latest")')
    list_group.add_argument(
        '--path',
        metavar='PATH',
        nargs='+',
        dest='paths',
        help='Paths to list from archive, defaults to the entire archive',
    )
    list_group.add_argument(
        '--short', default=False, action='store_true', help='Output only archive or path names'
    )
    list_group.add_argument('--format', help='Format for file listing')
    list_group.add_argument(
        '--json', default=False, action='store_true', help='Output results as JSON'
    )
    list_group.add_argument(
        '-P', '--prefix', help='Only list archive names starting with this prefix'
    )
    list_group.add_argument(
        '-a', '--glob-archives', metavar='GLOB', help='Only list archive names matching this glob'
    )
    list_group.add_argument(
        '--successful',
        default=False,
        action='store_true',
        help='Only list archive names of successful (non-checkpoint) backups',
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

    info_parser = subparsers.add_parser(
        'info',
        aliases=SUBPARSER_ALIASES['info'],
        help='Display summary information on archives',
        description='Display summary information on archives',
        add_help=False,
    )
    info_group = info_parser.add_argument_group('info arguments')
    info_group.add_argument(
        '--repository',
        help='Path of repository to show info for, defaults to the configured repository if there is only one',
    )
    info_group.add_argument('--archive', help='Name of archive to show info for (or "latest")')
    info_group.add_argument(
        '--json', dest='json', default=False, action='store_true', help='Output results as JSON'
    )
    info_group.add_argument(
        '-P', '--prefix', help='Only show info for archive names starting with this prefix'
    )
    info_group.add_argument(
        '-a',
        '--glob-archives',
        metavar='GLOB',
        help='Only show info for archive names matching this glob',
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
    info_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    borg_parser = subparsers.add_parser(
        'borg',
        aliases=SUBPARSER_ALIASES['borg'],
        help='Run an arbitrary Borg command',
        description='Run an arbitrary Borg command based on borgmatic\'s configuration',
        add_help=False,
    )
    borg_group = borg_parser.add_argument_group('borg arguments')
    borg_group.add_argument(
        '--repository',
        help='Path of repository to pass to Borg, defaults to the configured repositories',
    )
    borg_group.add_argument('--archive', help='Name of archive to pass to Borg (or "latest")')
    borg_group.add_argument(
        '--',
        metavar='OPTION',
        dest='options',
        nargs='+',
        help='Options to pass to Borg, command first ("create", "list", etc). "--" is optional. To specify the repository or the archive, you must use --repository or --archive instead of providing them here.',
    )
    borg_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    arguments, remaining_arguments = parse_subparser_arguments(
        unparsed_arguments, subparsers.choices
    )
    arguments['global'] = top_level_parser.parse_args(remaining_arguments)

    if arguments['global'].excludes_filename:
        raise ValueError(
            'The --excludes option has been replaced with exclude_patterns in configuration'
        )

    if 'init' in arguments and arguments['global'].dry_run:
        raise ValueError('The init action cannot be used with the --dry-run option')

    if 'list' in arguments and arguments['list'].glob_archives and arguments['list'].successful:
        raise ValueError('The --glob-archives and --successful options cannot be used together')

    if (
        'list' in arguments
        and 'info' in arguments
        and arguments['list'].json
        and arguments['info'].json
    ):
        raise ValueError('With the --json option, list and info actions cannot be used together')

    return arguments
