import subprocess

from flexmock import flexmock

from borgmatic.commands import borgmatic as module


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
    assert {log.levelno for log in logs} == {module.logging.CRITICAL}


def test_make_error_log_records_generates_output_logs_for_called_process_error():
    logs = tuple(
        module.make_error_log_records(
            subprocess.CalledProcessError(1, 'ls', 'error output'), 'Error'
        )
    )

    assert {log.levelno for log in logs} == {module.logging.CRITICAL}
    assert any(log for log in logs if 'error output' in str(log))


def test_make_error_log_records_generates_logs_for_value_error():
    logs = tuple(module.make_error_log_records(ValueError(), 'Error'))

    assert {log.levelno for log in logs} == {module.logging.CRITICAL}


def test_make_error_log_records_generates_logs_for_os_error():
    logs = tuple(module.make_error_log_records(OSError(), 'Error'))

    assert {log.levelno for log in logs} == {module.logging.CRITICAL}


def test_make_error_log_records_generates_nothing_for_other_error():
    logs = tuple(module.make_error_log_records(KeyError(), 'Error'))

    assert logs == ()


def test_collect_configuration_run_summary_logs_info_for_success():
    flexmock(module.hook).should_receive('execute_hook').never()
    flexmock(module).should_receive('run_configuration').and_return([])
    arguments = {}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert {log.levelno for log in logs} == {module.logging.INFO}


def test_collect_configuration_run_summary_executes_hooks_for_create():
    flexmock(module).should_receive('run_configuration').and_return([])
    arguments = {'create': flexmock(), 'global': flexmock(dry_run=False)}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert {log.levelno for log in logs} == {module.logging.INFO}


def test_collect_configuration_run_summary_logs_info_for_success_with_extract():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module).should_receive('run_configuration').and_return([])
    arguments = {'extract': flexmock(repository='repo')}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert {log.levelno for log in logs} == {module.logging.INFO}


def test_collect_configuration_run_summary_logs_critical_for_extract_with_repository_error():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository').and_raise(
        ValueError
    )
    arguments = {'extract': flexmock(repository='repo')}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert {log.levelno for log in logs} == {module.logging.CRITICAL}


def test_collect_configuration_run_summary_logs_critical_for_pre_hook_error():
    flexmock(module.hook).should_receive('execute_hook').and_raise(ValueError)
    arguments = {'create': flexmock(), 'global': flexmock(dry_run=False)}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert {log.levelno for log in logs} == {module.logging.CRITICAL}


def test_collect_configuration_run_summary_logs_critical_for_post_hook_error():
    flexmock(module.hook).should_receive('execute_hook').and_return(None).and_raise(ValueError)
    flexmock(module).should_receive('run_configuration').and_return([])
    arguments = {'create': flexmock(), 'global': flexmock(dry_run=False)}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert {log.levelno for log in logs} == {module.logging.INFO, module.logging.CRITICAL}


def test_collect_configuration_run_summary_logs_critical_for_list_with_archive_and_repository_error():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository').and_raise(
        ValueError
    )
    arguments = {'list': flexmock(repository='repo', archive='test')}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert {log.levelno for log in logs} == {module.logging.CRITICAL}


def test_collect_configuration_run_summary_logs_info_for_success_with_list():
    flexmock(module).should_receive('run_configuration').and_return([])
    arguments = {'list': flexmock(repository='repo', archive=None)}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert {log.levelno for log in logs} == {module.logging.INFO}


def test_collect_configuration_run_summary_logs_critical_for_run_value_error():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module).should_receive('run_configuration').and_raise(ValueError)
    arguments = {}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert {log.levelno for log in logs} == {module.logging.CRITICAL}


def test_collect_configuration_run_summary_logs_critical_including_output_for_run_process_error():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module).should_receive('run_configuration').and_raise(
        subprocess.CalledProcessError(1, 'command', 'error output')
    )
    arguments = {}

    logs = tuple(
        module.collect_configuration_run_summary_logs({'test.yaml': {}}, arguments=arguments)
    )

    assert {log.levelno for log in logs} == {module.logging.CRITICAL}
    assert any(log for log in logs if 'error output' in str(log))


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


def test_collect_configuration_run_summary_logs_critical_for_missing_configs():
    flexmock(module).should_receive('run_configuration').and_return([])
    arguments = {'global': flexmock(config_paths=[])}

    logs = tuple(module.collect_configuration_run_summary_logs({}, arguments=arguments))

    assert {log.levelno for log in logs} == {module.logging.CRITICAL}
