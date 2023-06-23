import argparse

from flexmock import flexmock

import borgmatic.logger
from borgmatic.actions.config import validate as module


def test_run_validate_with_show_renders_configurations():
    log_lines = []
    borgmatic.logger.add_custom_log_levels()

    def fake_logger_answer(message):
        log_lines.append(message)

    flexmock(module.logger).should_receive('answer').replace_with(fake_logger_answer)

    module.run_validate(argparse.Namespace(show=True), {'test.yaml': {'foo': {'bar': 'baz'}}})

    assert log_lines == ['''foo:\n    bar: baz\n''']


def test_run_validate_with_show_and_multiple_configs_renders_each():
    log_lines = []
    borgmatic.logger.add_custom_log_levels()

    def fake_logger_answer(message):
        log_lines.append(message)

    flexmock(module.logger).should_receive('answer').replace_with(fake_logger_answer)

    module.run_validate(
        argparse.Namespace(show=True),
        {'test.yaml': {'foo': {'bar': 'baz'}}, 'other.yaml': {'quux': 'value'}},
    )

    assert log_lines == ['---', 'foo:\n    bar: baz\n', '---', 'quux: value\n']
