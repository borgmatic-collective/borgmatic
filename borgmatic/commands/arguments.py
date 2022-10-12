import collections
from argparse import Action, ArgumentParser

from borgmatic.config import collect

SUBPARSER_ALIASES = {
    'rcreate': ['init', '-I'],
    'prune': ['-p'],
    'compact': [],
    'create': ['-C'],
    'check': ['-k'],
    'extract': ['-x'],
    'export-tar': [],
    'mount': ['-m'],
    'umount': ['-u'],
    'restore': ['-r'],
    'rlist': [],
    'list': ['-l'],
    'rinfo': [],
    'info': ['-i'],
    'transfer': [],
    'break-lock': [],
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


def make_parsers():
    '''
    Build a top-level parser and its subparsers and return them as a tuple.
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
    rcreate_parser = subparsers.add_parser(
        'rcreate',
        aliases=SUBPARSER_ALIASES['rcreate'],
        help='Create a new, empty Borg repository',
        description='Create a new, empty Borg repository',
        add_help=False,
    )
    rcreate_group = rcreate_parser.add_argument_group('rcreate arguments')
    rcreate_group.add_argument(
        '-e',
        '--encryption',
        dest='encryption_mode',
        help='Borg repository encryption mode',
        required=True,
    )
    rcreate_group.add_argument(
        '--source-repository',
        '--other-repo',
        metavar='KEY_REPOSITORY',
        help='Path to an existing Borg repository whose key material should be reused (Borg 2.x+ only)',
    )
    rcreate_group.add_argument(
        '--copy-crypt-key',
        action='store_true',
        help='Copy the crypt key used for authenticated encryption from the source repository, defaults to a new random key (Borg 2.x+ only)',
    )
    rcreate_group.add_argument(
        '--append-only', action='store_true', help='Create an append-only repository',
    )
    rcreate_group.add_argument(
        '--storage-quota', help='Create a repository with a fixed storage quota',
    )
    rcreate_group.add_argument(
        '--make-parent-dirs',
        action='store_true',
        help='Create any missing parent directories of the repository directory',
    )
    rcreate_group.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit'
    )

    transfer_parser = subparsers.add_parser(
        'transfer',
        aliases=SUBPARSER_ALIASES['transfer'],
        help='Transfer archives from one repository to another, optionally upgrading the transferred data (Borg 2.0+ only)',
        description='Transfer archives from one repository to another, optionally upgrading the transferred data (Borg 2.0+ only)',
        add_help=False,
    )
    transfer_group = transfer_parser.add_argument_group('transfer arguments')
    transfer_group.add_argument(
        '--repository',
        help='Path of existing destination repository to transfer archives to, defaults to the configured repository if there is only one',
    )
    transfer_group.add_argument(
        '--source-repository',
        help='Path of existing source repository to transfer archives from',
        required=True,
    )
    transfer_group.add_argument(
        '--archive',
        help='Name of single archive to transfer (or "latest"), defaults to transferring all archives',
    )
    transfer_group.add_argument(
        '--upgrader',
        help='Upgrader type used to convert the transfered data, e.g. "From12To20" to upgrade data from Borg 1.2 to 2.0 format, defaults to no conversion',
    )
    transfer_group.add_argument(
        '-a',
        '--match-archives',
        '--glob-archives',
        metavar='PATTERN',
        help='Only transfer archives with names matching this pattern',
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
        '-h', '--help', action='help', help='Show this help message and exit'
    )

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
        '--list', dest='list_archives', action='store_true', help='List archives kept/pruned'
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
        help='Cleanup commit-only 17-byte segment files left behind by Borg 1.1 (flag in Borg 1.2 only)',
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
        help='Create an archive (actually perform a backup)',
        description='Create an archive (actually perform a backup)',
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
        '--list', '--files', dest='list_files', action='store_true', help='Show per-file details'
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
        help='Attempt to repair any inconsistencies found (for interactive use)',
    )
    check_group.add_argument(
        '--only',
        metavar='CHECK',
        choices=('repository', 'archives', 'data', 'extract'),
        dest='only',
        action='append',
        help='Run a particular consistency check (repository, archives, data, or extract) instead of configured checks (subject to configured frequency, can specify flag multiple times)',
    )
    check_group.add_argument(
        '--force',
        default=False,
        action='store_true',
        help='Ignore configured check frequencies and run checks unconditionally',
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

    rlist_parser = subparsers.add_parser(
        'rlist',
        aliases=SUBPARSER_ALIASES['rlist'],
        help='List repository',
        description='List the archives in a repository',
        add_help=False,
    )
    rlist_group = rlist_parser.add_argument_group('rlist arguments')
    rlist_group.add_argument(
        '--repository', help='Path of repository to list, defaults to the configured repositories',
    )
    rlist_group.add_argument(
        '--short', default=False, action='store_true', help='Output only archive names'
    )
    rlist_group.add_argument('--format', help='Format for archive listing')
    rlist_group.add_argument(
        '--json', default=False, action='store_true', help='Output results as JSON'
    )
    rlist_group.add_argument(
        '-P', '--prefix', help='Only list archive names starting with this prefix'
    )
    rlist_group.add_argument(
        '-a',
        '--match-archives',
        '--glob-archives',
        metavar='PATTERN',
        help='Only list archive names matching this pattern',
    )
    rlist_group.add_argument(
        '--sort-by', metavar='KEYS', help='Comma-separated list of sorting keys'
    )
    rlist_group.add_argument(
        '--first', metavar='N', help='List first N archives after other filters are applied'
    )
    rlist_group.add_argument(
        '--last', metavar='N', help='List last N archives after other filters are applied'
    )
    rlist_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    list_parser = subparsers.add_parser(
        'list',
        aliases=SUBPARSER_ALIASES['list'],
        help='List archive',
        description='List the files in an archive or search for a file across archives',
        add_help=False,
    )
    list_group = list_parser.add_argument_group('list arguments')
    list_group.add_argument(
        '--repository',
        help='Path of repository containing archive to list, defaults to the configured repositories',
    )
    list_group.add_argument('--archive', help='Name of the archive to list (or "latest")')
    list_group.add_argument(
        '--path',
        metavar='PATH',
        nargs='+',
        dest='paths',
        help='Paths or patterns to list from a single selected archive (via "--archive"), defaults to listing the entire archive',
    )
    list_group.add_argument(
        '--find',
        metavar='PATH',
        nargs='+',
        dest='find_paths',
        help='Partial paths or patterns to search for and list across multiple archives',
    )
    list_group.add_argument(
        '--short', default=False, action='store_true', help='Output only path names'
    )
    list_group.add_argument('--format', help='Format for file listing')
    list_group.add_argument(
        '--json', default=False, action='store_true', help='Output results as JSON'
    )
    list_group.add_argument(
        '-P', '--prefix', help='Only list archive names starting with this prefix'
    )
    list_group.add_argument(
        '-a',
        '--match-archives',
        '--glob-archives',
        metavar='PATTERN',
        help='Only list archive names matching this pattern',
    )
    list_group.add_argument(
        '--successful',
        default=True,
        action='store_true',
        help='Deprecated; no effect. Newer versions of Borg shows successful (non-checkpoint) archives by default.',
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

    rinfo_parser = subparsers.add_parser(
        'rinfo',
        aliases=SUBPARSER_ALIASES['rinfo'],
        help='Show repository summary information such as disk space used',
        description='Show repository summary information such as disk space used',
        add_help=False,
    )
    rinfo_group = rinfo_parser.add_argument_group('rinfo arguments')
    rinfo_group.add_argument(
        '--repository',
        help='Path of repository to show info for, defaults to the configured repository if there is only one',
    )
    rinfo_group.add_argument(
        '--json', dest='json', default=False, action='store_true', help='Output results as JSON'
    )
    rinfo_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    info_parser = subparsers.add_parser(
        'info',
        aliases=SUBPARSER_ALIASES['info'],
        help='Show archive summary information such as disk space used',
        description='Show archive summary information such as disk space used',
        add_help=False,
    )
    info_group = info_parser.add_argument_group('info arguments')
    info_group.add_argument(
        '--repository',
        help='Path of repository containing archive to show info for, defaults to the configured repository if there is only one',
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
        '--match-archives',
        '--glob-archives',
        metavar='PATTERN',
        help='Only show info for archive names matching this pattern',
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

    break_lock_parser = subparsers.add_parser(
        'break-lock',
        aliases=SUBPARSER_ALIASES['break-lock'],
        help='Break the repository and cache locks left behind by Borg aborting',
        description='Break Borg repository and cache locks left behind by Borg aborting',
        add_help=False,
    )
    break_lock_group = break_lock_parser.add_argument_group('break-lock arguments')
    break_lock_group.add_argument(
        '--repository',
        help='Path of repository to break the lock for, defaults to the configured repository if there is only one',
    )
    break_lock_group.add_argument(
        '-h', '--help', action='help', help='Show this help message and exit'
    )

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

    return top_level_parser, subparsers


def parse_arguments(*unparsed_arguments):
    '''
    Given command-line arguments with which this script was invoked, parse the arguments and return
    them as a dict mapping from subparser name (or "global") to an argparse.Namespace instance.
    '''
    top_level_parser, subparsers = make_parsers()

    arguments, remaining_arguments = parse_subparser_arguments(
        unparsed_arguments, subparsers.choices
    )
    arguments['global'] = top_level_parser.parse_args(remaining_arguments)

    if arguments['global'].excludes_filename:
        raise ValueError(
            'The --excludes flag has been replaced with exclude_patterns in configuration.'
        )

    if (
        ('list' in arguments and 'rinfo' in arguments and arguments['list'].json)
        or ('list' in arguments and 'info' in arguments and arguments['list'].json)
        or ('rinfo' in arguments and 'info' in arguments and arguments['rinfo'].json)
    ):
        raise ValueError('With the --json flag, multiple actions cannot be used together.')

    if (
        'transfer' in arguments
        and arguments['transfer'].archive
        and arguments['transfer'].match_archives
    ):
        raise ValueError(
            'With the transfer action, only one of --archive and --glob-archives flags can be used.'
        )

    if 'info' in arguments and (
        (arguments['info'].archive and arguments['info'].prefix)
        or (arguments['info'].archive and arguments['info'].match_archives)
        or (arguments['info'].prefix and arguments['info'].match_archives)
    ):
        raise ValueError(
            'With the info action, only one of --archive, --prefix, or --match-archives flags can be used.'
        )

    return arguments
