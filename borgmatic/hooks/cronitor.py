import logging

import requests

logger = logging.getLogger(__name__)


def ping_cronitor(ping_url, config_filename, dry_run, append):
    '''
    Ping the given Cronitor URL, appending the append string. Use the given configuration filename
    in any log entries. If this is a dry run, then don't actually ping anything.
    '''
    if not ping_url:
        logger.debug('{}: No Cronitor hook set'.format(config_filename))
        return

    dry_run_label = ' (dry run; not actually pinging)' if dry_run else ''
    ping_url = '{}/{}'.format(ping_url, append)

    logger.info('{}: Pinging Cronitor {}{}'.format(config_filename, append, dry_run_label))
    logger.debug('{}: Using Cronitor ping URL {}'.format(config_filename, ping_url))

    if not dry_run:
        logging.getLogger('urllib3').setLevel(logging.ERROR)
        requests.get(ping_url)
