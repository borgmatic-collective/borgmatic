import logging

import apprise
from apprise import NotifyType, NotifyFormat

logger = logging.getLogger(__name__)


def initialize_monitor(
    ping_url, config, config_filename, monitoring_log_level, dry_run
):  # pragma: no cover
    '''
    No initialization is necessary for this monitor.
    '''
    pass


def ping_monitor(hook_config, config, config_filename, state, monitoring_log_level, dry_run):
    '''
    Ping the configured Apprise service URLs.
    Use the given configuration filename in any log entries.
    If this is a dry run, then don't actually ping anything.
    '''
    run_states = hook_config.get('states', ['fail'])

    if state.name.lower() not in run_states:
        return

    state_config = hook_config.get(
        state.name.lower(),
        {
            'title': f'A borgmatic {state.name} event happened',
            'body': f'A borgmatic {state.name} event happened',
            'notification_type': default_notify_type(state.name.lower()),
            # 'tag': ['borgmatic'],
        },
    )

    # TODO: Currently not very meaningful message.
    # However, the Apprise service URLs can contain sensitive info.
    dry_run_label = ' (dry run; not actually pinging)' if dry_run else ''
    logger.info(f'{config_filename}: Pinging Apprise {dry_run_label}')
    logger.debug(f'{config_filename}: Using Apprise ping')

    title = state_config.get('title', '')
    body = state_config.get('body')
    notify_type = state_config.get('notification_type', 'success')

    apobj = apprise.Apprise()
    apobj.add(hook_config.get('service_urls'))

    if dry_run:
        return

    result = apobj.notify(
        title=title,
        body=body,
        body_format=NotifyFormat.TEXT,
        notify_type=get_notify_type(notify_type)
    )

    if result is False:
        logger.warning(f'{config_filename}: error sending some apprise notifications')


def get_notify_type(s):
    if s == 'info':
        return NotifyType.INFO
    if s == 'success':
        return NotifyType.SUCCESS
    if s == 'warning':
        return NotifyType.WARNING
    if s == 'failure':
        return NotifyType.FAILURE


def default_notify_type(state):
    if state == 'start':
        return NotifyType.INFO
    if state == 'finish':
        return NotifyType.SUCCESS
    if state == 'fail':
        return NotifyType.FAILURE
    if state == 'log':
        return NotifyType.INFO


def destroy_monitor(
    ping_url_or_uuid, config, config_filename, monitoring_log_level, dry_run
):  # pragma: no cover
    '''
    No destruction is necessary for this monitor.
    '''
    pass
