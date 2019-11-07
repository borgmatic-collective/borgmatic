import logging

import requests

logger = logging.getLogger(__name__)


def ping_cronhub(ping_url, config_filename, dry_run, state):
    '''
    Ping the given Cronhub URL, substituting in the state string. Use the given configuration
    filename in any log entries. If this is a dry run, then don't actually ping anything.
    '''
    if not ping_url:
        logger.debug('{}: No Cronhub hook set'.format(config_filename))
        return

    dry_run_label = ' (dry run; not actually pinging)' if dry_run else ''
    formatted_state = '/{}/'.format(state)
    ping_url = ping_url.replace('/start/', formatted_state).replace('/ping/', formatted_state)

    logger.info('{}: Pinging Cronhub {}{}'.format(config_filename, state, dry_run_label))
    logger.debug('{}: Using Cronhub ping URL {}'.format(config_filename, ping_url))

    if not dry_run:
        logging.getLogger('urllib3').setLevel(logging.ERROR)
        requests.get(ping_url)
