import logging
import shlex

import borgmatic.borg.environment
import borgmatic.borg.feature
import borgmatic.config.paths
import borgmatic.execute
from borgmatic.borg import flags
from borgmatic.borg.pattern import write_patterns_file

logger = logging.getLogger(__name__)


def diff(
    repository,
    archive,
    second_archive,
    config,
    local_borg_version,
    diff_arguments,
    global_arguments,
    local_path,
    remote_path=None,
    patterns=None,
):
    '''
    Given a local or remote repository path, two archive names, a configuration dict, the local Borg
    version string, an argparse.Namespace of diff arguments, an argparse.Namespace of global
    arguments, optional local and remote Borg paths, executes the diff command with the given
    arguments.
    '''
    borgmatic.logger.add_custom_log_levels()

    lock_wait = config.get('lock_wait')
    extra_borg_options = config.get('extra_borg_options', {}).get('diff', '')

    if diff_arguments.only_patterns:
        # Write patterns to a temporary file and use that file with --patterns-from.
        patterns_file = write_patterns_file(
            patterns,
            borgmatic.config.paths.get_working_directory(config),
        )
    else:
        patterns_file = None

    if borgmatic.borg.feature.available(
        borgmatic.borg.feature.Feature.NUMERIC_IDS, local_borg_version
    ):
        numeric_ids_flags = ('--numeric-ids',) if config.get('numeric_ids') else ()
    else:
        numeric_ids_flags = ('--numeric-owner',) if config.get('numeric_ids') else ()

    diff_command = (
        (local_path, 'diff')
        + (('--remote-path', remote_path) if remote_path else ())
        + ('--log-json',)
        + (('--lock-wait', str(lock_wait)) if lock_wait is not None else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + (
            ('--patterns-from', patterns_file.name)
            if patterns_file and diff_arguments.only_patterns
            else ()
        )
        + numeric_ids_flags
        + (('--same-chunker-params',) if diff_arguments.same_chunker_params else ())
        + (('--sort-by', ','.join(diff_arguments.sort_keys)) if diff_arguments.sort_keys else ())
        + (('--content-only',) if diff_arguments.content_only else ())
        + (tuple(shlex.split(extra_borg_options)) if extra_borg_options else ())
        + (
            (*flags.make_repository_flags(repository, local_borg_version), archive)
            if borgmatic.borg.feature.available(
                borgmatic.borg.feature.Feature.SEPARATE_REPOSITORY_ARCHIVE,
                local_borg_version,
            )
            else flags.make_repository_archive_flags(repository, archive, local_borg_version)
        )
        + (second_archive,)
    )

    borgmatic.execute.execute_command(
        full_command=diff_command,
        output_log_level=logging.ANSWER,
        environment=borgmatic.borg.environment.make_environment(config),
        working_directory=borgmatic.config.paths.get_working_directory(config),
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )
