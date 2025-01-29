import logging
import operator

import borgmatic.hooks.monitoring.logs
import borgmatic.hooks.monitoring.monitor

logger = logging.getLogger(__name__)


DEFAULT_LOGS_SIZE_LIMIT_BYTES = 100000
HANDLER_IDENTIFIER = 'apprise'


def initialize_monitor(hook_config, config, config_filename, monitoring_log_level, dry_run):
    '''
    Add a handler to the root logger that stores in memory the most recent logs emitted. That way,
    we can send them all to an Apprise notification service upon a finish or failure state. But skip
    this if the "send_logs" option is false.
    '''
    if hook_config.get('send_logs') is False:
        return

    logs_size_limit = max(
        hook_config.get('logs_size_limit', DEFAULT_LOGS_SIZE_LIMIT_BYTES)
        - len(borgmatic.hooks.monitoring.logs.PAYLOAD_TRUNCATION_INDICATOR),
        0,
    )

    borgmatic.hooks.monitoring.logs.add_handler(
        borgmatic.hooks.monitoring.logs.Forgetful_buffering_handler(
            HANDLER_IDENTIFIER, logs_size_limit, monitoring_log_level
        )
    )


def ping_monitor(hook_config, config, config_filename, state, monitoring_log_level, dry_run):
    '''
    Ping the configured Apprise service URLs. Use the given configuration filename in any log
    entries. If this is a dry run, then don't actually ping anything.
    '''
    try:
        import apprise
        from apprise import NotifyFormat, NotifyType
    except ImportError:  # pragma: no cover
        logger.warning('Unable to import Apprise in monitoring hook')
        return

    state_to_notify_type = {
        'start': NotifyType.INFO,
        'finish': NotifyType.SUCCESS,
        'fail': NotifyType.FAILURE,
        'log': NotifyType.INFO,
    }

    run_states = hook_config.get('states', ['fail'])

    if state.name.lower() not in run_states:
        return

    state_config = hook_config.get(
        state.name.lower(),
        {
            'title': f'A borgmatic {state.name} event happened',
            'body': f'A borgmatic {state.name} event happened',
        },
    )

    if not hook_config.get('services'):
        logger.info('No Apprise services to ping')
        return

    dry_run_string = ' (dry run; not actually pinging)' if dry_run else ''
    labels_string = ', '.join(map(operator.itemgetter('label'), hook_config.get('services')))
    logger.info(f'Pinging Apprise services: {labels_string}{dry_run_string}')

    apprise_object = apprise.Apprise()
    apprise_object.add(list(map(operator.itemgetter('url'), hook_config.get('services'))))

    if dry_run:
        return

    body = state_config.get('body')

    if state in (
        borgmatic.hooks.monitoring.monitor.State.FINISH,
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        borgmatic.hooks.monitoring.monitor.State.LOG,
    ):
        formatted_logs = borgmatic.hooks.monitoring.logs.format_buffered_logs_for_payload(
            HANDLER_IDENTIFIER
        )
        if formatted_logs:
            body += f'\n\n{formatted_logs}'

    result = apprise_object.notify(
        title=state_config.get('title', ''),
        body=body,
        body_format=NotifyFormat.TEXT,
        notify_type=state_to_notify_type[state.name.lower()],
    )

    if result is False:
        logger.warning('Error sending some Apprise notifications')


def destroy_monitor(hook_config, config, monitoring_log_level, dry_run):
    '''
    Remove the monitor handler that was added to the root logger. This prevents the handler from
    getting reused by other instances of this monitor.
    '''
    borgmatic.hooks.monitoring.logs.remove_handler(HANDLER_IDENTIFIER)
