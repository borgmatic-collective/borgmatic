import json

import requests
from flexmock import flexmock

from borgmatic.hooks.monitoring import loki as module


def test_loki_log_buffer_add_value_gets_raw():
    '''
    Assert that adding values to the log buffer increases it's length.
    '''
    buffer = module.Loki_log_buffer(flexmock(), False)
    assert len(buffer) == 0

    buffer.add_value('Some test log line')
    assert len(buffer) == 1

    buffer.add_value('Another test log line')
    assert len(buffer) == 2


def test_loki_log_buffer_json_serializes_empty_buffer():
    '''
    Assert that the buffer correctly serializes when empty.
    '''
    buffer = module.Loki_log_buffer(flexmock(), False)

    assert json.loads(buffer.to_request()) == json.loads('{"streams":[{"stream":{},"values":[]}]}')


def test_loki_log_buffer_json_serializes_labels():
    '''
    Assert that the buffer correctly serializes with labels.
    '''
    buffer = module.Loki_log_buffer(flexmock(), False)
    buffer.add_label('test', 'label')

    assert json.loads(buffer.to_request()) == json.loads(
        '{"streams":[{"stream":{"test": "label"},"values":[]}]}'
    )


def test_loki_log_buffer_json_serializes_log_lines():
    '''
    Assert that log lines end up in the correct place in the log buffer.
    '''
    buffer = module.Loki_log_buffer(flexmock(), False)
    buffer.add_value('Some test log line')

    assert json.loads(buffer.to_request())['streams'][0]['values'][0][1] == 'Some test log line'


def test_loki_log_handler_add_label_gets_labels():
    '''
    Assert that adding labels works.
    '''
    buffer = module.Loki_log_buffer(flexmock(), False)

    buffer.add_label('test', 'label')
    assert buffer.root['streams'][0]['stream']['test'] == 'label'

    buffer.add_label('test2', 'label2')
    assert buffer.root['streams'][0]['stream']['test2'] == 'label2'


def test_loki_log_handler_emit_gets_log_messages():
    '''
    Assert that adding log records works.
    '''
    handler = module.Loki_log_handler(flexmock(), False)
    handler.emit(flexmock(getMessage=lambda: 'Some test log line'))

    assert len(handler.buffer) == 1


def test_loki_log_handler_raw_posts_to_server():
    '''
    Assert that the flush function sends a post request after a certain limit.
    '''
    handler = module.Loki_log_handler(flexmock(), False)
    flexmock(module.requests).should_receive('post').and_return(
        flexmock(raise_for_status=lambda: '')
    ).once()

    for num in range(int(module.MAX_BUFFER_LINES * 1.5)):
        handler.raw(num)


def test_loki_log_handler_raw_post_failure_does_not_raise():
    '''
    Assert that the flush function catches request exceptions.
    '''
    handler = module.Loki_log_handler(flexmock(), False)
    flexmock(module.requests).should_receive('post').and_return(
        flexmock(raise_for_status=lambda: (_ for _ in ()).throw(requests.RequestException()))
    ).once()

    for num in range(int(module.MAX_BUFFER_LINES * 1.5)):
        handler.raw(num)


def test_loki_log_handler_flush_with_empty_buffer_does_not_raise():
    '''
    Test that flushing an empty buffer does indeed nothing.
    '''
    handler = module.Loki_log_handler(flexmock(), False)
    handler.flush()
