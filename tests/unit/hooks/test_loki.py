from flexmock import flexmock
from borgmatic.hooks import loki
import json
import platform
import logging
import requests


def test_log_handler_gets_added():
    hook_config = {'url': 'http://localhost:3100/loki/api/v1/push', 'labels': {'app': 'borgmatic'}}
    config_filename = 'test.yaml'
    dry_run = True
    loki.initialize_monitor(hook_config, '', config_filename, '', dry_run)
    for handler in tuple(logging.getLogger().handlers):
        if isinstance(handler, loki.Loki_log_handler):
            assert True
            return
    assert False


def test_ping():
    hook_config = {'url': 'http://localhost:3100/loki/api/v1/push', 'labels': {'app': 'borgmatic'}}
    config_filename = 'test.yaml'
    dry_run = True
    loki.initialize_monitor(hook_config, '', config_filename, '', dry_run)
    loki.ping_monitor(hook_config, '', config_filename, loki.monitor.State.FINISH, '', dry_run)
    for handler in tuple(logging.getLogger().handlers):
        if isinstance(handler, loki.Loki_log_handler):
            assert len(handler.buffer) <= 1
            return
    assert False


def test_log_handler_gets_removed():
    hook_config = {'url': 'http://localhost:3100/loki/api/v1/push', 'labels': {'app': 'borgmatic'}}
    config_filename = 'test.yaml'
    dry_run = True
    loki.initialize_monitor(hook_config, '', config_filename, '', dry_run)
    loki.destroy_monitor(hook_config, '', config_filename, '', dry_run)
    for handler in tuple(logging.getLogger().handlers):
        if isinstance(handler, loki.Loki_log_handler):
            assert False


def test_log_handler_gets_labels():
    buffer = loki.Loki_log_buffer('', False)
    buffer.add_label('test', 'label')
    assert buffer.root['streams'][0]['stream']['test'] == 'label'
    buffer.add_label('test2', 'label2')
    assert buffer.root['streams'][0]['stream']['test2'] == 'label2'


def test_log_handler_label_replacment():
    hook_config = {
        'url': 'http://localhost:3100/loki/api/v1/push',
        'labels': {'hostname': '__hostname', 'config': '__config', 'config_full': '__config_path'},
    }
    config_filename = '/mock/path/test.yaml'
    dry_run = True
    loki.initialize_monitor(hook_config, '', config_filename, '', dry_run)
    for handler in tuple(logging.getLogger().handlers):
        if isinstance(handler, loki.Loki_log_handler):
            assert handler.buffer.root['streams'][0]['stream']['hostname'] == platform.node()
            assert handler.buffer.root['streams'][0]['stream']['config'] == 'test.yaml'
            assert handler.buffer.root['streams'][0]['stream']['config_full'] == config_filename
            return
    assert False


def test_log_handler_gets_logs():
    buffer = loki.Loki_log_buffer('', False)
    assert len(buffer) == 0
    buffer.add_value('Some test log line')
    assert len(buffer) == 1
    buffer.add_value('Another test log line')
    assert len(buffer) == 2


def test_log_handler_gets_raw():
    handler = loki.Loki_log_handler('', False)
    handler.emit(flexmock(getMessage=lambda: 'Some test log line'))
    assert len(handler.buffer) == 1


def test_log_handler_json():
    buffer = loki.Loki_log_buffer('', False)
    assert json.loads(buffer.to_request()) == json.loads('{"streams":[{"stream":{},"values":[]}]}')


def test_log_handler_json_labels():
    buffer = loki.Loki_log_buffer('', False)
    buffer.add_label('test', 'label')
    assert json.loads(buffer.to_request()) == json.loads(
        '{"streams":[{"stream":{"test": "label"},"values":[]}]}'
    )


def test_log_handler_json_log_lines():
    buffer = loki.Loki_log_buffer('', False)
    buffer.add_value('Some test log line')
    assert json.loads(buffer.to_request())['streams'][0]['values'][0][1] == 'Some test log line'


def test_log_handler_post():
    handler = loki.Loki_log_handler('', False)
    flexmock(loki.requests).should_receive('post').and_return(
        flexmock(raise_for_status=lambda: '')
    ).once()
    for x in range(150):
        handler.raw(x)


def test_post_failiure():
    handler = loki.Loki_log_handler('', False)
    flexmock(loki.requests).should_receive('post').and_return(
        flexmock(raise_for_status=lambda: (_ for _ in ()).throw(requests.RequestException()))
    ).once()
    for x in range(150):
        handler.raw(x)


def test_empty_flush():
    handler = loki.Loki_log_handler('', False)
    handler.flush()
