import collections
import json
import logging
import os
import sys
from argparse import ArgumentParser
from subprocess import CalledProcessError

import colorama
import pkg_resources

from borgmatic import hook
from borgmatic.borg import check as borg_check
from borgmatic.borg import create as borg_create
from borgmatic.borg import environment as borg_environment
from borgmatic.borg import extract as borg_extract
from borgmatic.borg import info as borg_info
from borgmatic.borg import init as borg_init
from borgmatic.borg import list as borg_list
from borgmatic.borg import prune as borg_prune
from borgmatic.config import checks, collect, convert, validate
from borgmatic.logger import configure_logging, should_do_markup
from borgmatic.signals import configure_signals
from borgmatic.verbosity import verbosity_to_log_level

logger = logging.getLogger(__name__)

LEGACY_CONFIG_PATH = '/etc/borgmatic/config'
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

    subparsers = top_level_parser.add_subparsers(title='actions', metavar='')
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
        description='List archives',
        add_help=False,
    )
    list_group = list_parser.add_argument_group('list arguments')
    list_group.add_argument(
        '--repository',
        help='Path of repository to use, defaults to the configured repository if there is only one',
    )
    list_group.add_argument('--archive', help='Name of archive to operate on')
    list_group.add_argument(
        '--json', dest='json', default=False, action='store_true', help='Output results as JSON'
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


def run_configuration(config_filename, config, arguments):  # pragma: no cover
    '''
    Given a config filename, the corresponding parsed config dict, and command-line arguments as a
    dict from subparser name to a namespace of parsed arguments, execute its defined pruning,
    backups, consistency checks, and/or other actions.

    Yield JSON output strings from executing any actions that produce JSON.
    '''
    (location, storage, retention, consistency, hooks) = (
        config.get(section_name, {})
        for section_name in ('location', 'storage', 'retention', 'consistency', 'hooks')
    )
    global_arguments = arguments['global']

    try:
        local_path = location.get('local_path', 'borg')
        remote_path = location.get('remote_path')
        borg_environment.initialize(storage)

        if 'create' in arguments:
            hook.execute_hook(
                hooks.get('before_backup'),
                hooks.get('umask'),
                config_filename,
                'pre-backup',
                global_arguments.dry_run,
            )

        for repository_path in location['repositories']:
            yield from run_actions(
                arguments=arguments,
                location=location,
                storage=storage,
                retention=retention,
                consistency=consistency,
                local_path=local_path,
                remote_path=remote_path,
                repository_path=repository_path,
            )

        if 'create' in arguments:
            hook.execute_hook(
                hooks.get('after_backup'),
                hooks.get('umask'),
                config_filename,
                'post-backup',
                global_arguments.dry_run,
            )
    except (OSError, CalledProcessError):
        hook.execute_hook(
            hooks.get('on_error'),
            hooks.get('umask'),
            config_filename,
            'on-error',
            global_arguments.dry_run,
        )
        raise


def run_actions(
    *,
    arguments,
    location,
    storage,
    retention,
    consistency,
    local_path,
    remote_path,
    repository_path
):  # pragma: no cover
    '''
    Given parsed command-line arguments as an argparse.ArgumentParser instance, several different
    configuration dicts, local and remote paths to Borg, and a repository name, run all actions
    from the command-line arguments on the given repository.

    Yield JSON output strings from executing any actions that produce JSON.
    '''
    repository = os.path.expanduser(repository_path)
    global_arguments = arguments['global']
    dry_run_label = ' (dry run; not making any changes)' if global_arguments.dry_run else ''
    if 'init' in arguments:
        logger.info('{}: Initializing repository'.format(repository))
        borg_init.initialize_repository(
            repository,
            arguments['init'].encryption_mode,
            arguments['init'].append_only,
            arguments['init'].storage_quota,
            local_path=local_path,
            remote_path=remote_path,
        )
    if 'prune' in arguments:
        logger.info('{}: Pruning archives{}'.format(repository, dry_run_label))
        borg_prune.prune_archives(
            global_arguments.dry_run,
            repository,
            storage,
            retention,
            local_path=local_path,
            remote_path=remote_path,
            stats=arguments['prune'].stats,
        )
    if 'create' in arguments:
        logger.info('{}: Creating archive{}'.format(repository, dry_run_label))
        json_output = borg_create.create_archive(
            global_arguments.dry_run,
            repository,
            location,
            storage,
            local_path=local_path,
            remote_path=remote_path,
            progress=arguments['create'].progress,
            stats=arguments['create'].stats,
            json=arguments['create'].json,
        )
        if json_output:
            yield json.loads(json_output)
    if 'check' in arguments and checks.repository_enabled_for_checks(repository, consistency):
        logger.info('{}: Running consistency checks'.format(repository))
        borg_check.check_archives(
            repository, storage, consistency, local_path=local_path, remote_path=remote_path
        )
    if 'extract' in arguments:
        if arguments['extract'].repository is None or repository == arguments['extract'].repository:
            logger.info(
                '{}: Extracting archive {}'.format(repository, arguments['extract'].archive)
            )
            borg_extract.extract_archive(
                global_arguments.dry_run,
                repository,
                arguments['extract'].archive,
                arguments['extract'].restore_paths,
                location,
                storage,
                local_path=local_path,
                remote_path=remote_path,
                progress=arguments['extract'].progress,
            )
    if 'list' in arguments:
        if arguments['list'].repository is None or repository == arguments['list'].repository:
            logger.info('{}: Listing archives'.format(repository))
            json_output = borg_list.list_archives(
                repository,
                storage,
                arguments['list'].archive,
                local_path=local_path,
                remote_path=remote_path,
                json=arguments['list'].json,
            )
            if json_output:
                yield json.loads(json_output)
    if 'info' in arguments:
        logger.info('{}: Displaying summary info for archives'.format(repository))
        json_output = borg_info.display_archives_info(
            repository,
            storage,
            local_path=local_path,
            remote_path=remote_path,
            json=arguments['info'].json,
        )
        if json_output:
            yield json.loads(json_output)


def load_configurations(config_filenames):
    '''
    Given a sequence of configuration filenames, load and validate each configuration file. Return
    the results as a tuple of: dict of configuration filename to corresponding parsed configuration,
    and sequence of logging.LogRecord instances containing any parse errors.
    '''
    # Dict mapping from config filename to corresponding parsed config dict.
    configs = collections.OrderedDict()
    logs = []

    # Parse and load each configuration file.
    for config_filename in config_filenames:
        try:
            configs[config_filename] = validate.parse_configuration(
                config_filename, validate.schema_filename()
            )
        except (ValueError, OSError, validate.Validation_error) as error:
            logs.extend(
                [
                    logging.makeLogRecord(
                        dict(
                            levelno=logging.CRITICAL,
                            levelname='CRITICAL',
                            msg='{}: Error parsing configuration file'.format(config_filename),
                        )
                    ),
                    logging.makeLogRecord(
                        dict(levelno=logging.CRITICAL, levelname='CRITICAL', msg=error)
                    ),
                ]
            )

    return (configs, logs)


def collect_configuration_run_summary_logs(configs, arguments):
    '''
    Given a dict of configuration filename to corresponding parsed configuration, and parsed
    command-line arguments as a dict from subparser name to a parsed namespace of arguments, run
    each configuration file and yield a series of logging.LogRecord instances containing summary
    information about each run.

    As a side effect of running through these configuration files, output their JSON results, if
    any, to stdout.
    '''
    # Run cross-file validation checks.
    if 'extract' in arguments:
        repository = arguments['extract'].repository
    elif 'list' in arguments and arguments['list'].archive:
        repository = arguments['list'].repository
    else:
        repository = None

    if repository:
        try:
            validate.guard_configuration_contains_repository(repository, configs)
        except ValueError as error:
            yield logging.makeLogRecord(
                dict(levelno=logging.CRITICAL, levelname='CRITICAL', msg=error)
            )
            return

    # Execute the actions corresponding to each configuration file.
    json_results = []
    for config_filename, config in configs.items():
        try:
            json_results.extend(list(run_configuration(config_filename, config, arguments)))
            yield logging.makeLogRecord(
                dict(
                    levelno=logging.INFO,
                    levelname='INFO',
                    msg='{}: Successfully ran configuration file'.format(config_filename),
                )
            )
        except (ValueError, OSError, CalledProcessError) as error:
            yield logging.makeLogRecord(
                dict(
                    levelno=logging.CRITICAL,
                    levelname='CRITICAL',
                    msg='{}: Error running configuration file'.format(config_filename),
                )
            )
            yield logging.makeLogRecord(
                dict(levelno=logging.CRITICAL, levelname='CRITICAL', msg=error)
            )

    if json_results:
        sys.stdout.write(json.dumps(json_results))

    if not configs:
        yield logging.makeLogRecord(
            dict(
                levelno=logging.CRITICAL,
                levelname='CRITICAL',
                msg='{}: No configuration files found'.format(
                    ' '.join(arguments['global'].config_paths)
                ),
            )
        )


def exit_with_help_link():  # pragma: no cover
    '''
    Display a link to get help and exit with an error code.
    '''
    logger.critical('')
    logger.critical('Need some help? https://torsion.org/borgmatic/#issues')
    sys.exit(1)


def main():  # pragma: no cover
    configure_signals()

    try:
        arguments = parse_arguments(*sys.argv[1:])
    except ValueError as error:
        configure_logging(logging.CRITICAL)
        logger.critical(error)
        exit_with_help_link()
    except SystemExit as error:
        if error.code == 0:
            raise error
        configure_logging(logging.CRITICAL)
        logger.critical('Error parsing arguments: {}'.format(' '.join(sys.argv)))
        exit_with_help_link()

    global_arguments = arguments['global']
    if global_arguments.version:
        print(pkg_resources.require('borgmatic')[0].version)
        sys.exit(0)

    config_filenames = tuple(collect.collect_config_filenames(global_arguments.config_paths))
    configs, parse_logs = load_configurations(config_filenames)

    colorama.init(autoreset=True, strip=not should_do_markup(global_arguments.no_color, configs))
    configure_logging(
        verbosity_to_log_level(global_arguments.verbosity),
        verbosity_to_log_level(global_arguments.syslog_verbosity),
    )

    logger.debug('Ensuring legacy configuration is upgraded')
    convert.guard_configuration_upgraded(LEGACY_CONFIG_PATH, config_filenames)

    summary_logs = list(collect_configuration_run_summary_logs(configs, arguments))

    logger.info('')
    logger.info('summary:')
    [
        logger.handle(log)
        for log in parse_logs + summary_logs
        if log.levelno >= logger.getEffectiveLevel()
    ]

    if any(log.levelno == logging.CRITICAL for log in summary_logs):
        exit_with_help_link()
