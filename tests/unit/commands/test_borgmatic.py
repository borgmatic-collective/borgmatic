import logging
import subprocess

from flexmock import flexmock

from borgmatic.commands import borgmatic as module


def test_run_configuration_runs_actions_for_each_repository():
    flexmock(module.borg_environment).should_receive('initialize')
    expected_results = [flexmock(), flexmock()]
    flexmock(module).should_receive('run_actions').and_return(expected_results[:1]).and_return(
        expected_results[1:]
    )
    config = {'location': {'repositories': ['foo', 'bar']}}
    arguments = {'global': flexmock()}

    results = list(module.run_configuration('test.yaml', config, arguments))

    assert results == expected_results


def test_run_configuration_executes_hooks_for_create_action():
    flexmock(module.borg_environment).should_receive('initialize')
    flexmock(module.command).should_receive('execute_hook').twice()
    flexmock(module.postgresql).should_receive('dump_databases').once()
    flexmock(module.healthchecks).should_receive('ping_healthchecks').twice()
    flexmock(module.postgresql).should_receive('remove_database_dumps').once()
    flexmock(module).should_receive('run_actions').and_return([])
    config = {'location': {'repositories': ['foo']}}
    arguments = {'global': flexmock(dry_run=False), 'create': flexmock()}

    list(module.run_configuration('test.yaml', config, arguments))


def test_run_configuration_logs_actions_error():
    flexmock(module.borg_environment).should_receive('initialize')
    flexmock(module.command).should_receive('execute_hook')
    flexmock(module.postgresql).should_receive('dump_databases')
    flexmock(module.healthchecks).should_receive('ping_healthchecks')
    expected_results = [flexmock()]
    flexmock(module).should_receive('make_error_log_records').and_return(expected_results)
    flexmock(module).should_receive('run_actions').and_raise(OSError)
    config = {'location': {'repositories': ['foo']}}
    arguments = {'global': flexmock(dry_run=False)}

    results = list(module.run_configuration('test.yaml', config, arguments))

    assert results == expected_results


def test_run_configuration_logs_pre_hook_error():
    flexmock(module.borg_environment).should_receive('initialize')
    flexmock(module.command).should_receive('execute_hook').and_raise(OSError).and_return(None)
    expected_results = [flexmock()]
    flexmock(module).should_receive('make_error_log_records').and_return(expected_results)
    flexmock(module).should_receive('run_actions').never()
    config = {'location': {'repositories': ['foo']}}
    arguments = {'global': flexmock(dry_run=False), 'create': flexmock()}

    results = list(module.run_configuration('test.yaml', config, arguments))

    assert results == expected_results


def test_run_configuration_logs_post_hook_error():
    flexmock(module.borg_environment).should_receive('initialize')
    flexmock(module.command).should_receive('execute_hook').and_return(None).and_raise(
        OSError
    ).and_return(None)
    expected_results = [flexmock()]
    flexmock(module).should_receive('make_error_log_records').and_return(expected_results)
    flexmock(module).should_receive('run_actions').and_return([])
    config = {'location': {'repositories': ['foo']}}
    arguments = {'global': flexmock(dry_run=False), 'create': flexmock()}

    results = list(module.run_configuration('test.yaml', config, arguments))

    assert results == expected_results


def test_run_configuration_logs_on_error_hook_error():
    flexmock(module.borg_environment).should_receive('initialize')
    flexmock(module.command).should_receive('execute_hook').and_raise(OSError)
    expected_results = [flexmock(), flexmock()]
    flexmock(module).should_receive('make_error_log_records').and_return(
        expected_results[:1]
    ).and_return(expected_results[1:])
    flexmock(module).should_receive('run_actions').and_raise(OSError)
    config = {'location': {'repositories': ['foo']}}
    arguments = {'global': flexmock(dry_run=False)}

    results = list(module.run_configuration('test.yaml', config, arguments))

    assert results == expected_results


def test_load_configurations_collects_parsed_configurations():
    configuration = flexmock()
    other_configuration = flexmock()
    flexmock(module.validate).should_receive('parse_configuration').and_return(
        configuration
    ).and_return(other_configuration)

    configs, logs = tuple(module.load_configurations(('test.yaml', 'other.yaml')))

    assert configs == {'test.yaml': configuration, 'other.yaml': other_configuration}
    assert logs == []


def test_load_configurations_logs_critical_for_parse_error():
    flexmock(module.validate).should_receive('parse_configuration').and_raise(ValueError)

    configs, logs = tuple(module.load_configurations(('test.yaml',)))

    assert configs == {}
    assert {log.levelno for log in logs} == {logging.CRITICAL}


def test_make_error_log_records_generates_output_logs_for_message_only():
    logs = tuple(module.make_error_log_records('Error'))

    assert {log.levelno for log in logs} == {logging.CRITICAL}


def test_make_error_log_records_generates_output_logs_for_called_process_error():
    logs = tuple(
        module.make_error_log_records(
            'Error', subprocess.CalledProcessError(1, 'ls', 'error output')
        )
    )

    assert {log.levelno for log in logs} == {logging.CRITICAL}
    assert any(log for log in logs if 'error output' in str(log))


def test_make_error_log_records_generates_logs_for_value_error():
    logs = tuple(module.make_error_log_records('Error', ValueError()))

    assert {log.levelno for log in logs} == {logging.CRITICAL}


def test_make_error_log_records_generates_logs_for_os_error():
    logs = tuple(module.make_error_log_records('Error', OSError()))

    assert {log.levelno for log in logs} == {logging.CRITICAL}


def test_make_error_log_records_generates_nothing_for_other_error():
    logs = tuple(module.make_error_log_records('Error', KeyError()))

    assert logs == ()


def test_collect_configuration_run_summary_logs_info_for_success():
    flexmock(module.command).should_receive('execute_hook').never()
    flexmock(module).should_receive('run_configuration').and_return([])
    arguments = {}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert {log.levelno for log in logs} == {logging.INFO}


def test_collect_configuration_run_summary_executes_hooks_for_create():
    flexmock(module).should_receive('run_configuration').and_return([])
    arguments = {'create': flexmock(), 'global': flexmock(dry_run=False)}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert {log.levelno for log in logs} == {logging.INFO}


def test_collect_configuration_run_summary_logs_info_for_success_with_extract():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module).should_receive('run_configuration').and_return([])
    arguments = {'extract': flexmock(repository='repo')}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert {log.levelno for log in logs} == {logging.INFO}


def test_collect_configuration_run_summary_logs_extract_with_repository_error():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository').and_raise(
        ValueError
    )
    expected_logs = (flexmock(),)
    flexmock(module).should_receive('make_error_log_records').and_return(expected_logs)
    arguments = {'extract': flexmock(repository='repo')}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert logs == expected_logs


def test_collect_configuration_run_summary_logs_missing_configs_error():
    arguments = {'global': flexmock(config_paths=[])}
    expected_logs = (flexmock(),)
    flexmock(module).should_receive('make_error_log_records').and_return(expected_logs)

    logs = tuple(module.collect_configuration_run_summary_logs({}, arguments=arguments))

    assert logs == expected_logs


def test_collect_configuration_run_summary_logs_pre_hook_error():
    flexmock(module.command).should_receive('execute_hook').and_raise(ValueError)
    expected_logs = (flexmock(),)
    flexmock(module).should_receive('make_error_log_records').and_return(expected_logs)
    arguments = {'create': flexmock(), 'global': flexmock(dry_run=False)}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert logs == expected_logs


def test_collect_configuration_run_summary_logs_post_hook_error():
    flexmock(module.command).should_receive('execute_hook').and_return(None).and_raise(ValueError)
    flexmock(module).should_receive('run_configuration').and_return([])
    expected_logs = (flexmock(),)
    flexmock(module).should_receive('make_error_log_records').and_return(expected_logs)
    arguments = {'create': flexmock(), 'global': flexmock(dry_run=False)}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert expected_logs[0] in logs


def test_collect_configuration_run_summary_logs_for_list_with_archive_and_repository_error():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository').and_raise(
        ValueError
    )
    expected_logs = (flexmock(),)
    flexmock(module).should_receive('make_error_log_records').and_return(expected_logs)
    arguments = {'list': flexmock(repository='repo', archive='test')}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert logs == expected_logs


def test_collect_configuration_run_summary_logs_info_for_success_with_list():
    flexmock(module).should_receive('run_configuration').and_return([])
    arguments = {'list': flexmock(repository='repo', archive=None)}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert {log.levelno for log in logs} == {logging.INFO}


def test_collect_configuration_run_summary_logs_run_configuration_error():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module).should_receive('run_configuration').and_return(
        [logging.makeLogRecord(dict(levelno=logging.CRITICAL, levelname='CRITICAL', msg='Error'))]
    )
    arguments = {}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert {log.levelno for log in logs} == {logging.CRITICAL}


def test_collect_configuration_run_summary_logs_outputs_merged_json_results():
    flexmock(module).should_receive('run_configuration').and_return(['foo', 'bar']).and_return(
        ['baz']
    )
    flexmock(module.sys.stdout).should_receive('write').with_args('["foo", "bar", "baz"]').once()
    arguments = {}

    tuple(
        module.collect_configuration_run_summary_logs(
            {'test.yaml': {}, 'test2.yaml': {}}, arguments=arguments
        )
    )
