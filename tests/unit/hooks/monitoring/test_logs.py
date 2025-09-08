import pytest
from flexmock import flexmock

from borgmatic.hooks.monitoring import logs as module


def test_forgetful_buffering_handler_emit_collects_log_records():
    handler = module.Forgetful_buffering_handler(identifier='test', byte_capacity=100, log_level=1)
    handler.emit(flexmock(getMessage=lambda: 'foo'))
    handler.emit(flexmock(getMessage=lambda: 'bar'))

    assert handler.buffer == ['foo\n', 'bar\n']
    assert not handler.forgot


def test_forgetful_buffering_handler_emit_collects_log_records_with_zero_byte_capacity():
    handler = module.Forgetful_buffering_handler(identifier='test', byte_capacity=0, log_level=1)
    handler.emit(flexmock(getMessage=lambda: 'foo'))
    handler.emit(flexmock(getMessage=lambda: 'bar'))

    assert handler.buffer == ['foo\n', 'bar\n']
    assert not handler.forgot


def test_forgetful_buffering_handler_emit_forgets_log_records_when_capacity_reached():
    handler = module.Forgetful_buffering_handler(
        identifier='test',
        byte_capacity=len('foo\nbar\n'),
        log_level=1,
    )
    handler.emit(flexmock(getMessage=lambda: 'foo'))
    assert handler.buffer == ['foo\n']
    handler.emit(flexmock(getMessage=lambda: 'bar'))
    assert handler.buffer == ['foo\n', 'bar\n']
    handler.emit(flexmock(getMessage=lambda: 'baz'))
    assert handler.buffer == ['bar\n', 'baz\n']
    handler.emit(flexmock(getMessage=lambda: 'quux'))
    assert handler.buffer == ['quux\n']
    assert handler.forgot


def test_add_handler_does_not_raise():
    logger = flexmock(handlers=[flexmock(level=0)])
    flexmock(module.logging).should_receive('getLogger').and_return(logger)
    flexmock(logger).should_receive('addHandler')
    flexmock(logger).should_receive('removeHandler')
    flexmock(logger).should_receive('setLevel')

    module.add_handler(flexmock())


def test_get_handler_matches_by_identifier():
    handlers = [
        flexmock(),
        flexmock(),
        module.Forgetful_buffering_handler(identifier='other', byte_capacity=100, log_level=1),
        module.Forgetful_buffering_handler(identifier='test', byte_capacity=100, log_level=1),
        flexmock(),
    ]
    flexmock(module.logging.getLogger(), handlers=handlers)

    assert module.get_handler('test') == handlers[3]


def test_get_handler_without_match_raises():
    handlers = [
        flexmock(),
        module.Forgetful_buffering_handler(identifier='other', byte_capacity=100, log_level=1),
    ]
    flexmock(module.logging.getLogger(), handlers=handlers)

    with pytest.raises(ValueError):
        assert module.get_handler('test')


def test_format_buffered_logs_for_payload_flattens_log_buffer():
    handler = module.Forgetful_buffering_handler(identifier='test', byte_capacity=100, log_level=1)
    handler.buffer = ['foo\n', 'bar\n']
    flexmock(module).should_receive('get_handler').and_return(handler)

    payload = module.format_buffered_logs_for_payload(identifier='test')

    assert payload == 'foo\nbar\n'


def test_format_buffered_logs_for_payload_inserts_truncation_indicator_when_logs_forgotten():
    handler = module.Forgetful_buffering_handler(identifier='test', byte_capacity=100, log_level=1)
    handler.buffer = ['foo\n', 'bar\n']
    handler.forgot = True
    flexmock(module).should_receive('get_handler').and_return(handler)

    payload = module.format_buffered_logs_for_payload(identifier='test')

    assert payload == '...\nfoo\nbar\n'


def test_format_buffered_logs_for_payload_without_handler_produces_empty_payload():
    flexmock(module).should_receive('get_handler').and_raise(ValueError)

    payload = module.format_buffered_logs_for_payload(identifier='test')

    assert payload == ''


def test_remove_handler_with_matching_handler_does_not_raise():
    flexmock(module).should_receive('get_handler').and_return(flexmock())
    logger = flexmock(handlers=[flexmock(level=0)])
    flexmock(module.logging).should_receive('getLogger').and_return(logger)
    flexmock(logger).should_receive('removeHandler')
    flexmock(logger).should_receive('setLevel')

    module.remove_handler('test')


def test_remove_handler_without_matching_handler_does_not_raise():
    flexmock(module).should_receive('get_handler').and_raise(ValueError)

    module.remove_handler('test')
