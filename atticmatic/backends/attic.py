from functools import partial

from atticmatic.backends import shared

# An atticmatic backend that supports Attic for actually handling backups.

COMMAND = 'attic'
CONFIG_FORMAT = shared.CONFIG_FORMAT


initialize = partial(shared.initialize, command=COMMAND)
create_archive = partial(shared.create_archive, command=COMMAND)
prune_archives = partial(shared.prune_archives, command=COMMAND)
check_archives = partial(shared.check_archives, command=COMMAND)
