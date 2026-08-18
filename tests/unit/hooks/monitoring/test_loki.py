import json

import pytest
from flexmock import flexmock

from borgmatic.hooks.monitoring import loki as module


def test_loki_log_buffer_add_value_gets_raw():
    '''
    Assert that adding values to the log buffer increases it's length.
    '''
    buffer = module.Loki_log_buffer(flexmock(), dry_run=False)
    assert len(buffer) == 0

    buffer.add_value('Some test log line')
    assert len(buffer) == 1

    buffer.add_value('Another test log line')
    assert len(buffer) == 2


def test_loki_log_buffer_json_serializes_empty_buffer():
    '''
    Assert that the buffer correctly serializes when empty.
    '''
    buffer = module.Loki_log_buffer(flexmock(), dry_run=False)

    assert json.loads(buffer.to_request()) == json.loads('{"streams":[{"stream":{},"values":[]}]}')


def test_loki_log_buffer_json_serializes_labels():
    '''
    Assert that the buffer correctly serializes with labels.
    '''
    buffer = module.Loki_log_buffer(flexmock(), dry_run=False)
    buffer.add_label('test', 'label')

    assert json.loads(buffer.to_request()) == json.loads(
        '{"streams":[{"stream":{"test": "label"},"values":[]}]}',
    )


def test_loki_log_buffer_json_serializes_log_lines():
    '''
    Assert that log lines end up in the correct place in the log buffer.
    '''
    buffer = module.Loki_log_buffer(flexmock(), dry_run=False)
    buffer.add_value('Some test log line')

    assert json.loads(buffer.to_request())['streams'][0]['values'][0][1] == 'Some test log line'


def test_loki_log_buffer_add_label_gets_labels():
    buffer = module.Loki_log_buffer(flexmock(), dry_run=False)

    buffer.add_label('test', 'label')
    assert buffer.root['streams'][0]['stream']['test'] == 'label'

    buffer.add_label('test2', 'label2')
    assert buffer.root['streams'][0]['stream']['test2'] == 'label2'


def test_loki_log_handler_emit_with_send_logs_records_log_message():
    handler = module.Loki_log_handler(flexmock(), send_logs=True, log_level=10, dry_run=False)
    flexmock(handler).should_receive('raw').once()

    handler.emit(flexmock(getMessage=lambda: 'Some test log line'))


def test_loki_log_handler_emit_without_send_logs_skips_log_message():
    handler = module.Loki_log_handler(flexmock(), send_logs=False, log_level=10, dry_run=False)
    flexmock(handler).should_receive('raw').never()

    handler.emit(flexmock(getMessage=lambda: 'Some test log line'))


def test_loki_log_handler_flush_with_empty_buffer_does_not_raise():
    handler = module.Loki_log_handler(flexmock(), send_logs=False, log_level=10, dry_run=False)

    handler.flush()


def test_loki_log_buffer_init_with_tls_stores_cert_and_key_paths():
    buffer = module.Loki_log_buffer(
        flexmock(),
        dry_run=False,
        tls_cert_path='/path/to/cert.crt',
        tls_key_path='/path/to/key.key',
    )

    assert buffer.tls_cert_path == '/path/to/cert.crt'
    assert buffer.tls_key_path == '/path/to/key.key'


def test_loki_log_handler_init_with_tls_passes_paths_to_buffer():
    handler = module.Loki_log_handler(
        flexmock(),
        send_logs=False,
        log_level=10,
        dry_run=False,
        tls_cert_path='/path/to/cert.crt',
        tls_key_path='/path/to/key.key',
    )

    assert handler.buffer.tls_cert_path == '/path/to/cert.crt'
    assert handler.buffer.tls_key_path == '/path/to/key.key'


def test_initialize_monitor_with_only_cert_path_raises():
    hook_config = {
        'url': 'http://localhost:3100/loki/api/v1/push',
        'tls': {'cert_path': '/path/to/cert.crt'},
    }

    with pytest.raises(ValueError):
        module.initialize_monitor(hook_config, {}, 'test.yaml', 1, False)


def test_initialize_monitor_with_only_key_path_raises():
    hook_config = {
        'url': 'http://localhost:3100/loki/api/v1/push',
        'tls': {'key_path': '/path/to/key.key'},
    }

    with pytest.raises(ValueError):
        module.initialize_monitor(hook_config, {}, 'test.yaml', 1, False)
