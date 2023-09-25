import logging

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
    Ping the configured Apprise service URLs. Use the given configuration filename in any log
    entries. If this is a dry run, then don't actually ping anything.
    '''
    try:
        import apprise
        from apprise import NotifyType, NotifyFormat
    except ImportError:
        logger.warning('Unable to import Apprise in monitoring hook')
        return

    state_to_notify_type = {
        'start': NotifyType.INFO,
        'finish': NotifyType.SUCCESS,
        'fail': NotifyType.FAILURE,
        'log': NotifyType.INFO
    }

    run_states = hook_config.get('states', ['fail'])

    if state.name.lower() not in run_states:
        return

    state_config = hook_config.get(
        state.name.lower(),
        {
            'title': f'A borgmatic {state.name} event happened',
            'body': f'A borgmatic {state.name} event happened'
        },
    )

    if not hook_config.get('services'):
        logger.info(f'{config_filename}: No Apprise services to ping')
        return

    dry_run_string = ' (dry run; not actually pinging)' if dry_run else ''
    labels_string = ', '.join(map(lambda service: service['label'], hook_config.get('services')))
    logger.info(f'{config_filename}: Pinging Apprise services: {labels_string}{dry_run_string}')

    title = state_config.get('title', '')
    body = state_config.get('body')
    notify_type = state_to_notify_type[state.name.lower()]

    apprise_object = apprise.Apprise()
    apprise_object.add(list(map(lambda service: service['url'], hook_config.get('services'))))

    if dry_run:
        return

    result = apprise_object.notify(
        title=title,
        body=body,
        body_format=NotifyFormat.TEXT,
        notify_type=notify_type)

    if result is False:
        logger.warning(f'{config_filename}: error sending some apprise notifications')


def destroy_monitor(
    ping_url_or_uuid, config, config_filename, monitoring_log_level, dry_run
):  # pragma: no cover
    '''
    No destruction is necessary for this monitor.
    '''
    pass
