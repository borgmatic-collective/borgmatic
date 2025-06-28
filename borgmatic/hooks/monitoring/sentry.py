import logging
import re

import requests

logger = logging.getLogger(__name__)


TIMEOUT_SECONDS = 10


def initialize_monitor(
    ping_url, config, config_filename, monitoring_log_level, dry_run
):  # pragma: no cover
    '''
    No initialization is necessary for this monitor.
    '''
    pass


DATA_SOURCE_NAME_URL_PATTERN = re.compile(
    '^(?P<protocol>.+)://(?P<username>.+)@(?P<hostname>.+)/(?P<project_id>.+)$'
)


def ping_monitor(hook_config, config, config_filename, state, monitoring_log_level, dry_run):
    '''
    Construct and ping a Sentry cron URL, based on the configured DSN URL and monitor slug. Use the
    given configuration filename in any log entries. If this is a dry run, then don't actually ping
    anything.
    '''
    run_states = hook_config.get('states', ['start', 'finish', 'fail'])

    if not state.name.lower() in run_states:
        return

    dry_run_label = ' (dry run; not actually pinging)' if dry_run else ''

    data_source_name_url = hook_config.get('data_source_name_url')
    monitor_slug = hook_config.get('monitor_slug')
    match = DATA_SOURCE_NAME_URL_PATTERN.match(data_source_name_url)

    if not match:
        logger.warning(f'Invalid Sentry data source name URL: {data_source_name_url}')
        return

    cron_url = f'{match.group("protocol")}://{match.group("hostname")}/api/{match.group("project_id")}/cron/{monitor_slug}/{match.group("username")}/'

    logger.info(f'Pinging Sentry {state.name.lower()}{dry_run_label}')
    logger.debug(f'Using Sentry cron URL {cron_url}')

    status = {
        'start': 'in_progress',
        'finish': 'ok',
        'fail': 'error',
    }.get(state.name.lower())

    if not status:
        logger.warning('Invalid Sentry state')
        return

    if dry_run:
        return

    logging.getLogger('urllib3').setLevel(logging.ERROR)
    try:
        response = requests.post(f'{cron_url}?status={status}', timeout=TIMEOUT_SECONDS)
        if not response.ok:
            response.raise_for_status()
    except requests.exceptions.RequestException as error:
        logger.warning(f'Sentry error: {error}')


def destroy_monitor(ping_url_or_uuid, config, monitoring_log_level, dry_run):  # pragma: no cover
    '''
    No destruction is necessary for this monitor.
    '''
    pass
