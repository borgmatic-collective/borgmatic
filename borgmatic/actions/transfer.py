import logging

import borgmatic.borg.transfer

logger = logging.getLogger(__name__)


def run_transfer(
    repository,
    config,
    local_borg_version,
    transfer_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "transfer" action for the given repository.
    '''
    if transfer_arguments.archive and config.get('match_archives'):
        raise ValueError(
            'With the transfer action, only one of --archive and --match-archives/match_archives can be used.'
        )

    logger.info('Transferring archives to repository')

    borgmatic.borg.transfer.transfer_archives(
        global_arguments.dry_run,
        repository['path'],
        config,
        local_borg_version,
        transfer_arguments,
        global_arguments,
        local_path=local_path,
        remote_path=remote_path,
    )
