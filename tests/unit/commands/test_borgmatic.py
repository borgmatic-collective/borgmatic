import json
import sys

from flexmock import flexmock

from borgmatic.commands import borgmatic as module


def test_run_commands_handles_multiple_json_outputs_in_array():
    (
        flexmock(module)
        .should_receive('_run_commands_on_repository')
        .times(3)
        .replace_with(
            lambda args, consistency, json_results, local_path, location, remote_path, retention, storage, unexpanded_repository: json_results.append(
                {"whatever": unexpanded_repository}
            )
        )
    )

    (
        flexmock(sys.stdout)
        .should_call("write")
        .with_args(
            json.dumps(
                json.loads(
                    '''
                        [
                            {"whatever": "fake_repo1"},
                            {"whatever": "fake_repo2"},
                            {"whatever": "fake_repo3"}
                        ]
                    '''
                )
            )
        )
    )

    module._run_commands(
        args=flexmock(json=True),
        consistency=None,
        local_path=None,
        location={'repositories': ['fake_repo1', 'fake_repo2', 'fake_repo3']},
        remote_path=None,
        retention=None,
        storage=None,
    )


def test_collect_configuration_run_summary_logs_info_for_success():
    flexmock(module).should_receive('run_configuration')

    logs = tuple(module.collect_configuration_run_summary_logs(('test.yaml',), args=()))

    assert any(log for log in logs if log.levelno == module.logging.INFO)


def test_collect_configuration_run_summary_logs_critical_for_error():
    flexmock(module).should_receive('run_configuration').and_raise(ValueError)

    logs = tuple(module.collect_configuration_run_summary_logs(('test.yaml',), args=()))

    assert any(log for log in logs if log.levelno == module.logging.CRITICAL)


def test_collect_configuration_run_summary_logs_critical_for_missing_configs():
    logs = tuple(
        module.collect_configuration_run_summary_logs(
            config_filenames=(), args=flexmock(config_paths=())
        )
    )

    assert any(log for log in logs if log.levelno == module.logging.CRITICAL)
