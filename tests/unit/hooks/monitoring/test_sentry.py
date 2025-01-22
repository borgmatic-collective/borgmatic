import pytest
from flexmock import flexmock

import borgmatic.hooks.monitoring.monitor
from borgmatic.hooks.monitoring import sentry as module


@pytest.mark.parametrize(
    'state,configured_states,expected_status',
    (
        (borgmatic.hooks.monitoring.monitor.State.START, ['start'], 'in_progress'),
        (
            borgmatic.hooks.monitoring.monitor.State.START,
            ['start', 'finish', 'fail'],
            'in_progress',
        ),
        (borgmatic.hooks.monitoring.monitor.State.START, None, 'in_progress'),
        (borgmatic.hooks.monitoring.monitor.State.FINISH, ['finish'], 'ok'),
        (borgmatic.hooks.monitoring.monitor.State.FAIL, ['fail'], 'error'),
    ),
)
def test_ping_monitor_constructs_cron_url_and_pings_it(state, configured_states, expected_status):
    hook_config = {
        'data_source_name_url': 'https://5f80ec@o294220.ingest.us.sentry.io/203069',
        'monitor_slug': 'test',
    }

    if configured_states:
        hook_config['states'] = configured_states

    flexmock(module.requests).should_receive('get').with_args(
        f'https://o294220.ingest.us.sentry.io/api/203069/cron/test/5f80ec/?status={expected_status}'
    ).and_return(flexmock(ok=True))

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        state,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_unconfigured_state_bails():
    hook_config = {
        'data_source_name_url': 'https://5f80ec@o294220.ingest.us.sentry.io/203069',
        'monitor_slug': 'test',
        'states': ['fail'],
    }
    flexmock(module.requests).should_receive('get').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


@pytest.mark.parametrize(
    'data_source_name_url',
    (
        '5f80ec@o294220.ingest.us.sentry.io/203069',
        'https://o294220.ingest.us.sentry.io/203069',
        'https://5f80ec@/203069',
        'https://5f80ec@o294220.ingest.us.sentry.io',
        'https://5f80ec@o294220.ingest.us.sentry.io/203069/',
    ),
)
def test_ping_monitor_with_invalid_data_source_name_url_bails(data_source_name_url):
    hook_config = {
        'data_source_name_url': data_source_name_url,
        'monitor_slug': 'test',
    }

    flexmock(module.requests).should_receive('get').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_invalid_sentry_state_bails():
    hook_config = {
        'data_source_name_url': 'https://5f80ec@o294220.ingest.us.sentry.io/203069',
        'monitor_slug': 'test',
        # This should never actually happen in practice, because the config schema prevents it.
        'states': ['log'],
    }
    flexmock(module.requests).should_receive('get').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.LOG,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_dry_run_bails():
    hook_config = {
        'data_source_name_url': 'https://5f80ec@o294220.ingest.us.sentry.io/203069',
        'monitor_slug': 'test',
    }
    flexmock(module.requests).should_receive('get').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.START,
        monitoring_log_level=1,
        dry_run=True,
    )
