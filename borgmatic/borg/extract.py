import logging
import sys
import subprocess

from borgmatic.verbosity import VERBOSITY_SOME, VERBOSITY_LOTS


logger = logging.getLogger(__name__)


def extract_last_archive_dry_run(verbosity, repository, remote_path=None):
    '''
    Perform an extraction dry-run of just the most recent archive. If there are no archives, skip
    the dry-run.
    '''
    remote_path_flags = ('--remote-path', remote_path) if remote_path else ()
    verbosity_flags = {
        VERBOSITY_SOME: ('--info',),
        VERBOSITY_LOTS: ('--debug',),
    }.get(verbosity, ())

    full_list_command = (
        'borg', 'list',
        '--short',
        repository,
    ) + remote_path_flags + verbosity_flags

    list_output = subprocess.check_output(full_list_command).decode(sys.stdout.encoding)

    last_archive_name = list_output.strip().split('\n')[-1]
    if not last_archive_name:
        return

    list_flag = ('--list',) if verbosity == VERBOSITY_LOTS else ()
    full_extract_command = (
        'borg', 'extract',
        '--dry-run',
        '{repository}::{last_archive_name}'.format(
            repository=repository,
            last_archive_name=last_archive_name,
        ),
    ) + remote_path_flags + verbosity_flags + list_flag

    logger.debug(' '.join(full_extract_command))
    subprocess.check_call(full_extract_command)
