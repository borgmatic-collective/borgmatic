import itertools
import re

from borgmatic.borg import feature


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


def make_match_archives_flags(match_archives, archive_name_format, local_borg_version):
    '''
    Return match archives flags based on the given match archives value, if any. If it isn't set,
    return match archives flags to match archives created with the given (or default) archive name
    format. This is done by replacing certain archive name format placeholders for ephemeral data
    (like "{now}") with globs.
    '''
    if match_archives:
        if feature.available(feature.Feature.MATCH_ARCHIVES, local_borg_version):
            return ('--match-archives', match_archives)
        else:
            return ('--glob-archives', re.sub(r'^sh:', '', match_archives))

    derived_match_archives = re.sub(
        r'\{(now|utcnow|pid)([:%\w\.-]*)\}', '*', archive_name_format or DEFAULT_ARCHIVE_NAME_FORMAT
    )

    if derived_match_archives == '*':
        return ()

    if feature.available(feature.Feature.MATCH_ARCHIVES, local_borg_version):
        return ('--match-archives', f'sh:{derived_match_archives}')
    else:
        return ('--glob-archives', f'{derived_match_archives}')
