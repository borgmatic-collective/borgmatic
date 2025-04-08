import logging
import shlex

import borgmatic.borg.environment
import borgmatic.borg.feature
import borgmatic.config.paths
import borgmatic.execute
from borgmatic.borg import flags
from borgmatic.borg.pattern import write_patterns_file

logger = logging.getLogger(__name__)


def recreate_archive(
    repository,
    archive,
    config,
    local_borg_version,
    recreate_arguments,
    global_arguments,
    local_path,
    remote_path=None,
    patterns=None,
):
    '''
    Given a local or remote repository path, an archive name, a configuration dict, the local Borg
    version string, an argparse.Namespace of recreate arguments, an argparse.Namespace of global
    arguments, optional local and remote Borg paths, executes the recreate command with the given
    arguments.
    '''
    lock_wait = config.get('lock_wait', None)
    exclude_flags = flags.make_exclude_flags(config)
    compression = config.get('compression', None)
    chunker_params = config.get('chunker_params', None)

    # Available recompress MODES: "if-different", "always", "never" (default)
    recompress = config.get('recompress', None)

    # Write patterns to a temporary file and use that file with --patterns-from.
    patterns_file = write_patterns_file(
        patterns, borgmatic.config.paths.get_working_directory(config)
    )

    recreate_command = (
        (local_path, 'recreate')
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--log-json',) if config.get('log_json') else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait is not None else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + (('--patterns-from', patterns_file.name) if patterns_file else ())
        + (
            (
                '--list',
                '--filter',
                flags.make_list_filter_flags(local_borg_version, global_arguments.dry_run),
            )
            if config.get('list_details')
            else ()
        )
        # Flag --target works only for a single archive.
        + (('--target', recreate_arguments.target) if recreate_arguments.target and archive else ())
        + (
            ('--comment', shlex.quote(recreate_arguments.comment))
            if recreate_arguments.comment
            else ()
        )
        + (('--timestamp', recreate_arguments.timestamp) if recreate_arguments.timestamp else ())
        + (('--compression', compression) if compression else ())
        + (('--chunker-params', chunker_params) if chunker_params else ())
        + (('--recompress', recompress) if recompress else ())
        + exclude_flags
        + (
            (
                flags.make_repository_flags(repository, local_borg_version)
                + flags.make_match_archives_flags(
                    archive or config.get('match_archives'),
                    config.get('archive_name_format'),
                    local_borg_version,
                )
            )
            if borgmatic.borg.feature.available(
                borgmatic.borg.feature.Feature.SEPARATE_REPOSITORY_ARCHIVE, local_borg_version
            )
            else (
                flags.make_repository_archive_flags(repository, archive, local_borg_version)
                if archive
                else flags.make_repository_flags(repository, local_borg_version)
            )
        )
    )

    if global_arguments.dry_run:
        logger.info('Skipping the archive recreation (dry run)')
        return

    borgmatic.execute.execute_command(
        full_command=recreate_command,
        output_log_level=logging.INFO,
        environment=borgmatic.borg.environment.make_environment(config),
        working_directory=borgmatic.config.paths.get_working_directory(config),
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )
