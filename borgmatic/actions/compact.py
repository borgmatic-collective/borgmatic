import logging

import borgmatic.borg.compact
import borgmatic.borg.feature
import borgmatic.config.validate
import borgmatic.hooks.command

logger = logging.getLogger(__name__)


def run_compact(
    config_filename,
    repository,
    config,
    local_borg_version,
    compact_arguments,
    global_arguments,
    dry_run_label,
    local_path,
    remote_path,
):
    '''
    Run the "compact" action for the given repository.
    '''
    if compact_arguments.repository and not borgmatic.config.validate.repositories_match(
        repository, compact_arguments.repository
    ):
        return

    if borgmatic.borg.feature.available(borgmatic.borg.feature.Feature.COMPACT, local_borg_version):
        logger.info(f'Compacting segments{dry_run_label}')
        borgmatic.borg.compact.compact_segments(
            global_arguments.dry_run,
            repository['path'],
            config,
            local_borg_version,
            global_arguments,
            local_path=local_path,
            remote_path=remote_path,
            cleanup_commits=compact_arguments.cleanup_commits,
        )
    else:  # pragma: nocover
        logger.info('Skipping compact (only available/needed in Borg 1.2+)')
