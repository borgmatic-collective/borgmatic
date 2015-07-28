from functools import partial

from atticmatic.config import Section_format, option
from atticmatic.backends import shared

# An atticmatic backend that supports Borg for actually handling backups.

COMMAND = 'borg'
CONFIG_FORMAT = (
    shared.CONFIG_FORMAT[0],  # location
    shared.CONFIG_FORMAT[1],  # retention
    Section_format(
        'consistency',
        (
            option('checks', required=False),
            option('check_last', required=False),
        ),
    )
)


create_archive = partial(shared.create_archive, command=COMMAND)
prune_archives = partial(shared.prune_archives, command=COMMAND)
check_archives = partial(shared.check_archives, command=COMMAND)
