from functools import partial

from atticmatic.config import Section_format, option
from atticmatic.backends import shared

# An atticmatic backend that supports Borg for actually handling backups.

COMMAND = 'borg'
CONFIG_FORMAT = (
    Section_format(
        'location',
        (
            option('source_directories'),
            option('source_directories_glob', int, required=False),
            option('one_file_system', required=False),
            option('repository'),
        ),
    ),
    Section_format(
        'storage',
        (
            option('encryption_passphrase', required=False),
            option('compression', required=False),
            option('umask', int, required=False),
        ),
    ),
    shared.CONFIG_FORMAT[2],  # retention
    Section_format(
        'consistency',
        (
            option('checks', required=False),
            option('check_last', required=False),
        ),
    )
)


initialize = partial(shared.initialize, command=COMMAND)

create_archive = partial(shared.create_archive, command=COMMAND)
prune_archives = partial(shared.prune_archives, command=COMMAND)
check_archives = partial(shared.check_archives, command=COMMAND)
