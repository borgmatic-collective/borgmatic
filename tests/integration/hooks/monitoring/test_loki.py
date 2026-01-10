import logging
import platform

import requests
from flexmock import flexmock

from borgmatic.hooks.monitoring import loki as module


def test_loki_log_handler_raw_with_send_logs_posts_to_server_after_buffer_full():
    handler = module.Loki_log_handler(flexmock(), send_logs=True, dry_run=False)
    flexmock(module.requests).should_receive('post').and_return(
        flexmock(raise_for_status=lambda: ''),
    ).once()

    for num in range(int(module.MAX_BUFFER_LINES * 1.5)):
        handler.raw(num)


def test_loki_log_handler_raw_without_send_logs_posts_to_server_without_buffering():
    handler = module.Loki_log_handler(flexmock(), send_logs=False, dry_run=False)
    flexmock(module.requests).should_receive('post').and_return(
        flexmock(raise_for_status=lambda: ''),
    ).times(3)

    for num in range(3):
        handler.raw(num)


def test_loki_log_handler_raw_post_failure_does_not_raise():
    handler = module.Loki_log_handler(flexmock(), send_logs=True, dry_run=False)
    flexmock(module.requests).should_receive('post').and_return(
        flexmock(raise_for_status=lambda: (_ for _ in ()).throw(requests.RequestException())),
    ).once()

    for num in range(int(module.MAX_BUFFER_LINES * 1.5)):
        handler.raw(num)


def test_initialize_monitor_replaces_labels():
    '''
    Assert that label placeholders get replaced.
    '''
    hook_config = {
        'url': 'http://localhost:3100/loki/api/v1/push',
        'labels': {'hostname': '__hostname', 'config': '__config', 'config_full': '__config_path'},
    }
    config_filename = '/mock/path/test.yaml'
    module.initialize_monitor(hook_config, flexmock(), config_filename, flexmock(), dry_run=False)

    for handler in tuple(logging.getLogger().handlers):
        if isinstance(handler, module.Loki_log_handler):
            assert handler.buffer.root['streams'][0]['stream']['hostname'] == platform.node()
            assert handler.buffer.root['streams'][0]['stream']['config'] == 'test.yaml'
            assert handler.buffer.root['streams'][0]['stream']['config_full'] == config_filename
            return

    raise AssertionError()


def test_initialize_monitor_adds_log_handler():
    '''
    Assert that calling initialize_monitor adds our logger to the root logger.
    '''
    hook_config = {'url': 'http://localhost:3100/loki/api/v1/push', 'labels': {'app': 'borgmatic'}}
    module.initialize_monitor(
        hook_config,
        flexmock(),
        config_filename='test.yaml',
        monitoring_log_level=flexmock(),
        dry_run=True,
    )

    for handler in tuple(logging.getLogger().handlers):
        if isinstance(handler, module.Loki_log_handler):
            return

    raise AssertionError()


def test_ping_monitor_sends_log_message():
    '''
    Assert that calling ping_monitor sends a message to Loki via our logger.
    '''
    hook_config = {'url': 'http://localhost:3100/loki/api/v1/push', 'labels': {'app': 'borgmatic'}}
    config_filename = 'test.yaml'
    post_called = False

    def post(url, data, timeout, headers):
        nonlocal post_called
        post_called = True

        assert any(
            value[1] == f'{module.MONITOR_STATE_TO_LOKI[module.monitor.State.FINISH]} backup'
            for value in module.json.loads(data)['streams'][0]['values']
        )

        return flexmock(raise_for_status=lambda: None)

    flexmock(module.requests).should_receive('post').replace_with(post)

    module.initialize_monitor(hook_config, flexmock(), config_filename, flexmock(), dry_run=False)
    module.ping_monitor(
        hook_config,
        flexmock(),
        config_filename,
        module.monitor.State.FINISH,
        flexmock(),
        dry_run=False,
    )
    module.destroy_monitor(hook_config, flexmock(), flexmock(), dry_run=False)

    assert post_called


def test_destroy_monitor_removes_log_handler():
    '''
    Assert that destroy_monitor removes the logger from the root logger.
    '''
    hook_config = {'url': 'http://localhost:3100/loki/api/v1/push', 'labels': {'app': 'borgmatic'}}
    config_filename = 'test.yaml'
    flexmock(module.requests).should_receive('post').never()

    module.initialize_monitor(hook_config, flexmock(), config_filename, flexmock(), dry_run=False)
    module.destroy_monitor(hook_config, flexmock(), flexmock(), dry_run=False)

    for handler in tuple(logging.getLogger().handlers):
        if isinstance(handler, module.Loki_log_handler):
            raise AssertionError()
