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
    assert any(log for log in logs if log.levelno == module.logging.CRITICAL)


def test_collect_configuration_run_summary_logs_info_for_success():
    flexmock(module).should_receive('run_configuration').and_return([])
    args = flexmock(extract=False, list=False)

    logs = tuple(module.collect_configuration_run_summary_logs({'test.yaml': {}}, args=args))

    assert all(log for log in logs if log.levelno == module.logging.INFO)


def test_collect_configuration_run_summary_logs_info_for_success_with_extract():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module).should_receive('run_configuration').and_return([])
    args = flexmock(extract=True, list=False, repository='repo')

    logs = tuple(module.collect_configuration_run_summary_logs({'test.yaml': {}}, args=args))

    assert all(log for log in logs if log.levelno == module.logging.INFO)


def test_collect_configuration_run_summary_logs_critical_for_extract_with_repository_error():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository').and_raise(
        ValueError
    )
    args = flexmock(extract=True, list=False, repository='repo')

    logs = tuple(module.collect_configuration_run_summary_logs({'test.yaml': {}}, args=args))

    assert any(log for log in logs if log.levelno == module.logging.CRITICAL)


def test_collect_configuration_run_summary_logs_critical_for_list_with_archive_and_repository_error():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository').and_raise(
        ValueError
    )
    args = flexmock(extract=False, list=True, repository='repo', archive='test')

    logs = tuple(module.collect_configuration_run_summary_logs({'test.yaml': {}}, args=args))

    assert any(log for log in logs if log.levelno == module.logging.CRITICAL)


def test_collect_configuration_run_summary_logs_info_for_success_with_list():
    flexmock(module).should_receive('run_configuration').and_return([])
    args = flexmock(extract=False, list=True, repository='repo', archive=None)

    logs = tuple(module.collect_configuration_run_summary_logs({'test.yaml': {}}, args=args))

    assert all(log for log in logs if log.levelno == module.logging.INFO)


def test_collect_configuration_run_summary_logs_critical_for_run_error():
    flexmock(module.validate).should_receive('guard_configuration_contains_repository')
    flexmock(module).should_receive('run_configuration').and_raise(ValueError)
    args = flexmock(extract=False, list=False)

    logs = tuple(module.collect_configuration_run_summary_logs({'test.yaml': {}}, args=args))

    assert any(log for log in logs if log.levelno == module.logging.CRITICAL)


def test_collect_configuration_run_summary_logs_outputs_merged_json_results():
    flexmock(module).should_receive('run_configuration').and_return(['foo', 'bar']).and_return(
        ['baz']
    )
    flexmock(module.sys.stdout).should_receive('write').with_args('["foo", "bar", "baz"]').once()
    args = flexmock(extract=False, list=False)

    tuple(
        module.collect_configuration_run_summary_logs(
            {'test.yaml': {}, 'test2.yaml': {}}, args=args
        )
    )


def test_collect_configuration_run_summary_logs_critical_for_missing_configs():
    flexmock(module).should_receive('run_configuration').and_return([])
    args = flexmock(extract=False, list=False, config_paths=[])

    logs = tuple(module.collect_configuration_run_summary_logs({}, args=args))

    assert any(log for log in logs if log.levelno == module.logging.CRITICAL)
