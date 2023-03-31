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


def make_match_archives_flags(archive_name_format, local_borg_version):
    '''
    Return the match archives flags that would match archives created with the given archive name
    format (if any). This is done by replacing certain archive name format placeholders for
    ephemeral data (like "{now}") with globs.
    '''
    if not archive_name_format:
        return ()

    match_archives = re.sub(r'\{(now|utcnow|pid)([:%\w\.-]*)\}', '*', archive_name_format)

    if feature.available(feature.Feature.MATCH_ARCHIVES, local_borg_version):
        return ('--match-archives', f'sh:{match_archives}')
    else:
        return ('--glob-archives', f'{match_archives}')
