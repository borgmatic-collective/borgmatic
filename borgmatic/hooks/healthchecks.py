import logging

import requests

logger = logging.getLogger(__name__)


def ping_healthchecks(ping_url_or_uuid, config_filename, dry_run, append=None):
    '''
    Ping the given Healthchecks URL or UUID, appending the append string if any. Use the given
    configuration filename in any log entries. If this is a dry run, then don't actually ping
    anything.
    '''
    if not ping_url_or_uuid:
        logger.debug('{}: No Healthchecks hook set'.format(config_filename))
        return

    ping_url = (
        ping_url_or_uuid
        if ping_url_or_uuid.startswith('http')
        else 'https://hc-ping.com/{}'.format(ping_url_or_uuid)
    )
    dry_run_label = ' (dry run; not actually pinging)' if dry_run else ''

    if append:
        ping_url = '{}/{}'.format(ping_url, append)

    logger.info(
        '{}: Pinging Healthchecks{}{}'.format(
            config_filename, ' ' + append if append else '', dry_run_label
        )
    )
    logger.debug('{}: Using Healthchecks ping URL {}'.format(config_filename, ping_url))

    if not dry_run:
        logging.getLogger('urllib3').setLevel(logging.ERROR)
        requests.get(ping_url)
