import json
import sys

from flexmock import flexmock
import pytest

from borgmatic.commands import borgmatic


def test__run_commands_handles_multiple_json_outputs_in_array():
    (
        flexmock(borgmatic)
        .should_receive('_run_commands_on_repository')
        .times(3)
        .replace_with(
            lambda args, consistency, json_results, local_path, location, remote_path, retention,
            storage,
            unexpanded_repository: json_results.append({"whatever": unexpanded_repository})
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
                    ''',
                )
            )
        )
    )

    borgmatic._run_commands(
        args=flexmock(json=True),
        consistency=None,
        local_path=None,
        location={'repositories': [
            'fake_repo1',
            'fake_repo2',
            'fake_repo3'
        ]},
        remote_path=None,
        retention=None,
        storage=None,
    )
