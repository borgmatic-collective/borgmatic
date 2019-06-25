import collections
from argparse import ArgumentParser

from borgmatic.config import collect

SUBPARSER_ALIASES = {
    'init': ['--init', '-I'],
    'prune': ['--prune', '-p'],
    'create': ['--create', '-C'],
    'check': ['--check', '-k'],
    'extract': ['--extract', '-x'],
    'list': ['--list', '-l'],
    'info': ['--info', '-i'],
}


def parse_subparser_arguments(unparsed_arguments, top_level_parser, subparsers):
    '''
    Given a sequence of arguments, a top-level parser (containing subparsers), and a subparsers
    object as returned by argparse.ArgumentParser().add_subparsers(), ask each subparser to parse
    its own arguments and the top-level parser to parse any remaining arguments.

    Return the result as a dict mapping from subparser name (or "global") to a parsed namespace of
    arguments.
    '''
    arguments = collections.OrderedDict()
    remaining_arguments = list(unparsed_arguments)
    alias_to_subparser_name = {
        alias: subparser_name
        for subparser_name, aliases in SUBPARSER_ALIASES.items()
        for alias in aliases
    }

    # Give each requested action's subparser a shot at parsing all arguments.
    for subparser_name, subparser in subparsers.choices.items():
        if subparser_name not in unparsed_arguments:
            continue

        remaining_arguments.remove(subparser_name)
        canonical_name = alias_to_subparser_name.get(subparser_name, subparser_name)

        parsed, remaining = subparser.parse_known_args(unparsed_arguments)
        arguments[canonical_name] = parsed

    # If no actions are explicitly requested, assume defaults: prune, create, and check.
    if not arguments and '--help' not in unparsed_arguments and '-h' not in unparsed_arguments:
        for subparser_name in ('prune', 'create', 'check'):
            subparser = subparsers.choices[subparser_name]
            parsed, remaining = subparser.parse_known_args(unparsed_arguments)
            arguments[subparser_name] = parsed

    # Then ask each subparser, one by one, to greedily consume arguments. Any arguments that remain
    # are global arguments.
    for subparser_name in arguments.keys():
        subparser = subparsers.choices[subparser_name]
        parsed, remaining_arguments = subparser.parse_known_args(remaining_arguments)

    arguments['global'] = top_level_parser.parse_args(remaining_arguments)

    return arguments


def parse_arguments(*unparsed_arguments):
    '''
    Given command-line arguments with which this script was invoked, parse the arguments and return
    them as a dict mapping from subparser name (or "global") to an argparse.Namespace instance.
    '''
    config_paths = collect.get_default_config_paths()

    global_parser = ArgumentParser(add_help=False)
    global_group = global_parser.add_argument_group('global arguments')

    global_group.add_argument(
        '-c',
        '--config',
        nargs='*',
        dest='config_paths',
        default=config_paths,
        help='Configuration filenames or directories, defaults to: {}'.format(
            ' '.join(config_paths)
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
        choices=range(0, 3),
        default=0,
        help='Display verbose progress to the console (from none to lots: 0, 1, or 2)',
    )
    global_group.add_argument(
        '--syslog-verbosity',
        type=int,
        choices=range(0, 3),
        default=0,
        help='Display verbose progress to syslog (from none to lots: 0, 1, or 2)',
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
            A simple wrapper script for the Borg backup software that creates and prunes backups.
            If none of the action options are given, then borgmatic defaults to: prune, create, and
            check archives.
            ''',
        parents=[global_parser],
    )

    subparsers = top_level_parser.add_subparsers(
        title='actions',
        metavar='',
        help='Specify zero or more actions. Defaults to prune, create, and check. Use --help with action for details:',
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
        help='Prune archives according to the retention policy',
        description='Prune archives according to the retention policy',
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
    prune_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

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
        help='Display progress for each file as it is processed',
    )
    create_group.add_argument(
        '--stats',
        dest='stats',
        default=False,
        action='store_true',
        help='Display statistics of archive',
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
    check_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    extract_parser = subparsers.add_parser(
        'extract',
        aliases=SUBPARSER_ALIASES['extract'],
        help='Extract a named archive to the current directory',
        description='Extract a named archive to the current directory',
        add_help=False,
    )
    extract_group = extract_parser.add_argument_group('extract arguments')
    extract_group.add_argument(
        '--repository',
        help='Path of repository to use, defaults to the configured repository if there is only one',
    )
    extract_group.add_argument('--archive', help='Name of archive to operate on', required=True)
    extract_group.add_argument(
        '--restore-path',
        nargs='+',
        dest='restore_paths',
        help='Paths to restore from archive, defaults to the entire archive',
    )
    extract_group.add_argument(
        '--progress',
        dest='progress',
        default=False,
        action='store_true',
        help='Display progress for each file as it is processed',
    )
    extract_group.add_argument(
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
        '--repository',
        help='Path of repository to use, defaults to the configured repository if there is only one',
    )
    list_group.add_argument('--archive', help='Name of archive to operate on')
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
        '--sort-by', metavar='KEYS', help='Comma-separated list of sorting keys'
    )
    list_group.add_argument(
        '--first', metavar='N', help='List first N archives after other filters are applied'
    )
    list_group.add_argument(
        '--last', metavar='N', help='List first N archives after other filters are applied'
    )
    list_group.add_argument(
        '-e', '--exclude', metavar='PATTERN', help='Exclude paths matching the pattern'
    )
    list_group.add_argument(
        '--exclude-from', metavar='FILENAME', help='Exclude paths from exclude file, one per line'
    )
    list_group.add_argument('--pattern', help='Include or exclude paths matching a pattern')
    list_group.add_argument(
        '--pattern-from',
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
        '--json', dest='json', default=False, action='store_true', help='Output results as JSON'
    )
    info_group.add_argument('-h', '--help', action='help', help='Show this help message and exit')

    arguments = parse_subparser_arguments(unparsed_arguments, top_level_parser, subparsers)

    if arguments['global'].excludes_filename:
        raise ValueError(
            'The --excludes option has been replaced with exclude_patterns in configuration'
        )

    if 'init' in arguments and arguments['global'].dry_run:
        raise ValueError('The init action cannot be used with the --dry-run option')

    if (
        'list' in arguments
        and 'info' in arguments
        and arguments['list'].json
        and arguments['info'].json
    ):
        raise ValueError('With the --json option, list and info actions cannot be used together')

    return arguments
