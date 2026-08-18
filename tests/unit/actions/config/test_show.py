from flexmock import flexmock

import borgmatic.logger
from borgmatic.actions.config import show as module


def test_run_show_with_single_configuration_file_does_not_separate_output():
    log_lines = []
    borgmatic.logger.add_custom_log_levels()

    def fake_logger_answer(message):
        log_lines.append(message)

    flexmock(module.logger).should_receive('answer').replace_with(fake_logger_answer)
    show_arguments = flexmock(option=None, json=False)
    flexmock(module.borgmatic.config.generate).should_receive('render_configuration').and_return(
        'output'
    )

    module.run_show(show_arguments, configs={'test.yaml': {}})

    assert log_lines == ['output']


def test_run_show_with_multiple_configuration_files_separates_output():
    log_lines = []
    borgmatic.logger.add_custom_log_levels()

    def fake_logger_answer(message):
        log_lines.append(message)

    flexmock(module.logger).should_receive('answer').replace_with(fake_logger_answer)
    show_arguments = flexmock(option=None, json=False)
    flexmock(module.borgmatic.config.generate).should_receive('render_configuration').and_return(
        'output'
    ).and_return('other')

    module.run_show(show_arguments, configs={'test.yaml': {}, 'other.yaml': {}})

    assert log_lines == ['---', 'output', '---', 'other']


def test_run_show_with_option_limits_output():
    log_lines = []
    borgmatic.logger.add_custom_log_levels()

    def fake_logger_answer(message):
        log_lines.append(message)

    flexmock(module.logger).should_receive('answer').replace_with(fake_logger_answer)
    show_arguments = flexmock(option='foo', json=False)
    flexmock(module.borgmatic.config.generate).should_receive('render_configuration').with_args(
        33
    ).and_return('33')
    flexmock(module.borgmatic.config.generate).should_receive('render_configuration').with_args(
        None
    ).and_return('null')

    module.run_show(show_arguments, configs={'test.yaml': {'foo': 33, 'bar': 44}, 'other.yaml': {}})

    assert log_lines == ['---', '33', '---', 'null']


def test_run_show_with_json_outputs_json():
    flexmock(borgmatic.logger).should_receive('add_custom_log_levels')
    show_arguments = flexmock(option=None, json=True)
    flexmock(module.sys.stdout).should_receive('write').with_args(
        '[{"foo": 33}, {"bar": 44}]'
    ).once()

    module.run_show(show_arguments, configs={'test.yaml': {'foo': 33}, 'other.yaml': {'bar': 44}})


def test_run_show_with_json_and_option_limits_json():
    flexmock(borgmatic.logger).should_receive('add_custom_log_levels')
    show_arguments = flexmock(option='foo', json=True)
    flexmock(module.sys.stdout).should_receive('write').with_args('[33, null]').once()

    module.run_show(show_arguments, configs={'test.yaml': {'foo': 33}, 'other.yaml': {'bar': 44}})
