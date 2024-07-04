import itertools
import json
import logging
import re

from borgmatic.borg import feature

logger = logging.getLogger(__name__)


def make_flags(name, value):
    '''
    Given a flag name and its value, return it formatted as Borg-compatible flags.
    '''
    if not value:
        return ()

    flag = f"--{name.replace('_', '-')}"

    if value is True:
        return (flag,)

    return (flag, str(value))


def make_flags_from_arguments(arguments, excludes=()):
    '''
    Given borgmatic command-line arguments as an instance of argparse.Namespace, and optionally a
    list of named arguments to exclude, generate and return the corresponding Borg command-line
    flags as a tuple.
    '''
    return tuple(
        itertools.chain.from_iterable(
            make_flags(name, value=getattr(arguments, name))
            for name in sorted(vars(arguments))
            if name not in excludes and not name.startswith('_')
        )
    )


def make_repository_flags(repository_path, local_borg_version):
    '''
    Given the path of a Borg repository and the local Borg version, return Borg-version-appropriate
    command-line flags (as a tuple) for selecting that repository.
    '''
    return (
        ('--repo',)
        if feature.available(feature.Feature.SEPARATE_REPOSITORY_ARCHIVE, local_borg_version)
        else ()
    ) + (repository_path,)


def make_repository_archive_flags(repository_path, archive, local_borg_version):
    '''
    Given the path of a Borg repository, an archive name or pattern, and the local Borg version,
    return Borg-version-appropriate command-line flags (as a tuple) for selecting that repository
    and archive.
    '''
    return (
        ('--repo', repository_path, archive)
        if feature.available(feature.Feature.SEPARATE_REPOSITORY_ARCHIVE, local_borg_version)
        else (f'{repository_path}::{archive}',)
    )


DEFAULT_ARCHIVE_NAME_FORMAT = '{hostname}-{now:%Y-%m-%dT%H:%M:%S.%f}'  # noqa: FS003


def make_match_archives_flags(
    match_archives,
    archive_name_format,
    local_borg_version,
    default_archive_name_format=DEFAULT_ARCHIVE_NAME_FORMAT,
):
    '''
    Return match archives flags based on the given match archives value, if any. If it isn't set,
    return match archives flags to match archives created with the given (or default) archive name
    format. This is done by replacing certain archive name format placeholders for ephemeral data
    (like "{now}") with globs.
    '''
    if match_archives:
        if match_archives in {'*', 're:.*', 'sh:*'}:
            return ()

        if feature.available(feature.Feature.MATCH_ARCHIVES, local_borg_version):
            return ('--match-archives', match_archives)
        else:
            return ('--glob-archives', re.sub(r'^sh:', '', match_archives))

    derived_match_archives = re.sub(
        r'\{(now|utcnow|pid)([:%\w\.-]*)\}', '*', archive_name_format or default_archive_name_format
    )

    if derived_match_archives == '*':
        return ()

    if feature.available(feature.Feature.MATCH_ARCHIVES, local_borg_version):
        return ('--match-archives', f'sh:{derived_match_archives}')
    else:
        return ('--glob-archives', f'{derived_match_archives}')


def warn_for_aggressive_archive_flags(json_command, json_output):
    '''
    Given a JSON archives command and the resulting JSON string output from running it, parse the
    JSON and warn if the command used an archive flag but the output indicates zero archives were
    found.
    '''
    archive_flags_used = {'--glob-archives', '--match-archives'}.intersection(set(json_command))

    if not archive_flags_used:
        return

    try:
        if len(json.loads(json_output)['archives']) == 0:
            logger.warning('An archive filter was applied, but no matching archives were found.')
            logger.warning(
                'Try adding --match-archives "*" or adjusting archive_name_format/match_archives in configuration.'
            )
    except json.JSONDecodeError as error:
        logger.debug(f'Cannot parse JSON output from archive command: {error}')
    except (TypeError, KeyError):
        logger.debug('Cannot parse JSON output from archive command: No "archives" key found')
