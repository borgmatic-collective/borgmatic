import logging
import platform

from flexmock import flexmock

from borgmatic.hooks import loki as module


def test_log_handler_label_replacment():
    '''
    Assert that label placeholders get replaced
    '''
    hook_config = {
        'url': 'http://localhost:3100/loki/api/v1/push',
        'labels': {'hostname': '__hostname', 'config': '__config', 'config_full': '__config_path'},
    }
    config_filename = '/mock/path/test.yaml'
    dry_run = True
    module.initialize_monitor(hook_config, flexmock(), config_filename, flexmock(), dry_run)
    for handler in tuple(logging.getLogger().handlers):
        if isinstance(handler, module.Loki_log_handler):
            assert handler.buffer.root['streams'][0]['stream']['hostname'] == platform.node()
            assert handler.buffer.root['streams'][0]['stream']['config'] == 'test.yaml'
            assert handler.buffer.root['streams'][0]['stream']['config_full'] == config_filename
            return
    assert False


def test_initalize_adds_log_handler():
    '''
    Assert that calling initialize_monitor adds our logger to the root logger
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
    assert False


def test_ping_adds_log_message():
    '''
    Assert that calling ping_monitor adds a message to our logger
    '''
    hook_config = {'url': 'http://localhost:3100/loki/api/v1/push', 'labels': {'app': 'borgmatic'}}
    config_filename = 'test.yaml'
    dry_run = True
    module.initialize_monitor(hook_config, flexmock(), config_filename, flexmock(), dry_run)
    module.ping_monitor(
        hook_config, flexmock(), config_filename, module.monitor.State.FINISH, flexmock(), dry_run
    )
    for handler in tuple(logging.getLogger().handlers):
        if isinstance(handler, module.Loki_log_handler):
            assert any(
                map(
                    lambda log: log
                    == f'{config_filename}: {module.MONITOR_STATE_TO_LOKI[module.monitor.State.FINISH]} backup',
                    map(lambda x: x[1], handler.buffer.root['streams'][0]['values']),
                )
            )
            return
    assert False


def test_log_handler_gets_removed():
    '''
    Assert that destroy_monitor removes the logger from the root logger
    '''
    hook_config = {'url': 'http://localhost:3100/loki/api/v1/push', 'labels': {'app': 'borgmatic'}}
    config_filename = 'test.yaml'
    dry_run = True
    module.initialize_monitor(hook_config, flexmock(), config_filename, flexmock(), dry_run)
    module.destroy_monitor(hook_config, flexmock(), config_filename, flexmock(), dry_run)
    for handler in tuple(logging.getLogger().handlers):
        if isinstance(handler, module.Loki_log_handler):
            assert False
