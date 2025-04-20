import logging
import subprocess

import pytest
from flexmock import flexmock

from borgmatic.hooks import command as module


def test_interpolate_context_passes_through_command_without_variable():
    assert module.interpolate_context('pre-backup', 'ls', {'foo': 'bar'}) == 'ls'


def test_interpolate_context_warns_and_passes_through_command_with_unknown_variable():
    command = 'ls {baz}'  # noqa: FS003
    flexmock(module.logger).should_receive('warning').once()

    assert module.interpolate_context('pre-backup', command, {'foo': 'bar'}) == command


def test_interpolate_context_does_not_warn_and_passes_through_command_with_unknown_variable_matching_borg_placeholder():
    command = 'ls {hostname}'  # noqa: FS003
    flexmock(module.logger).should_receive('warning').never()

    assert module.interpolate_context('pre-backup', command, {'foo': 'bar'}) == command


def test_interpolate_context_interpolates_variables():
    command = 'ls {foo}{baz} {baz}'  # noqa: FS003
    context = {'foo': 'bar', 'baz': 'quux'}

    assert module.interpolate_context('pre-backup', command, context) == 'ls barquux quux'


def test_interpolate_context_escapes_interpolated_variables():
    command = 'ls {foo} {inject}'  # noqa: FS003
    context = {'foo': 'bar', 'inject': 'hi; naughty-command'}

    assert (
        module.interpolate_context('pre-backup', command, context) == "ls bar 'hi; naughty-command'"
    )


def test_make_environment_without_pyinstaller_does_not_touch_environment():
    assert module.make_environment({}, sys_module=flexmock()) == {}


def test_make_environment_with_pyinstaller_clears_LD_LIBRARY_PATH():
    assert module.make_environment({}, sys_module=flexmock(frozen=True, _MEIPASS='yup')) == {
        'LD_LIBRARY_PATH': ''
    }


def test_make_environment_with_pyinstaller_and_LD_LIBRARY_PATH_ORIG_copies_it_into_LD_LIBRARY_PATH():
    assert module.make_environment(
        {'LD_LIBRARY_PATH_ORIG': '/lib/lib/lib'}, sys_module=flexmock(frozen=True, _MEIPASS='yup')
    ) == {'LD_LIBRARY_PATH_ORIG': '/lib/lib/lib', 'LD_LIBRARY_PATH': '/lib/lib/lib'}


@pytest.mark.parametrize(
    'hooks,filters,expected_hooks',
    (
        (
            (
                {
                    'before': 'action',
                    'run': ['foo'],
                },
                {
                    'after': 'action',
                    'run': ['bar'],
                },
                {
                    'before': 'repository',
                    'run': ['baz'],
                },
            ),
            {},
            (
                {
                    'before': 'action',
                    'run': ['foo'],
                },
                {
                    'after': 'action',
                    'run': ['bar'],
                },
                {
                    'before': 'repository',
                    'run': ['baz'],
                },
            ),
        ),
        (
            (
                {
                    'before': 'action',
                    'run': ['foo'],
                },
                {
                    'after': 'action',
                    'run': ['bar'],
                },
                {
                    'before': 'repository',
                    'run': ['baz'],
                },
            ),
            {
                'before': 'action',
            },
            (
                {
                    'before': 'action',
                    'run': ['foo'],
                },
            ),
        ),
        (
            (
                {
                    'after': 'action',
                    'run': ['foo'],
                },
                {
                    'before': 'action',
                    'run': ['bar'],
                },
                {
                    'after': 'repository',
                    'run': ['baz'],
                },
            ),
            {
                'after': 'action',
            },
            (
                {
                    'after': 'action',
                    'run': ['foo'],
                },
            ),
        ),
        (
            (
                {
                    'before': 'action',
                    'run': ['foo'],
                },
                {
                    'before': 'action',
                    'run': ['bar'],
                },
                {
                    'before': 'action',
                    'run': ['baz'],
                },
            ),
            {
                'before': 'action',
                'action_names': ['create', 'compact', 'extract'],
            },
            (
                {
                    'before': 'action',
                    'run': ['foo'],
                },
                {
                    'before': 'action',
                    'run': ['bar'],
                },
                {
                    'before': 'action',
                    'run': ['baz'],
                },
            ),
        ),
        (
            (
                {
                    'before': 'action',
                    'states': ['finish'],  # Not actually valid; only valid for "after".
                    'run': ['foo'],
                },
                {
                    'after': 'action',
                    'run': ['bar'],
                },
                {
                    'after': 'action',
                    'states': ['finish'],
                    'run': ['baz'],
                },
                {
                    'after': 'action',
                    'states': ['fail'],
                    'run': ['quux'],
                },
            ),
            {
                'after': 'action',
                'state_names': ['finish'],
            },
            (
                {
                    'after': 'action',
                    'run': ['bar'],
                },
                {
                    'after': 'action',
                    'states': ['finish'],
                    'run': ['baz'],
                },
            ),
        ),
    ),
)
def test_filter_hooks(hooks, filters, expected_hooks):
    assert module.filter_hooks(hooks, **filters) == expected_hooks


LOGGING_ANSWER = flexmock()


def test_execute_hooks_invokes_each_hook_and_command():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module).should_receive('interpolate_context').replace_with(
        lambda hook_description, command, context: command
    )
    flexmock(module).should_receive('make_environment').and_return({})

    for command in ('foo', 'bar', 'baz'):
        flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
            [command],
            output_log_level=LOGGING_ANSWER,
            shell=True,
            environment={},
            working_directory=None,
        ).once()

    module.execute_hooks(
        [{'before': 'create', 'run': ['foo']}, {'before': 'create', 'run': ['bar', 'baz']}],
        umask=None,
        working_directory=None,
        dry_run=False,
    )


def test_execute_hooks_with_umask_sets_that_umask():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module).should_receive('interpolate_context').replace_with(
        lambda hook_description, command, context: command
    )
    flexmock(module.os).should_receive('umask').with_args(0o77).and_return(0o22).once()
    flexmock(module.os).should_receive('umask').with_args(0o22).once()
    flexmock(module).should_receive('make_environment').and_return({})
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        ['foo'],
        output_log_level=logging.ANSWER,
        shell=True,
        environment={},
        working_directory=None,
    )

    module.execute_hooks(
        [{'before': 'create', 'run': ['foo']}], umask=77, working_directory=None, dry_run=False
    )


def test_execute_hooks_with_working_directory_executes_command_with_it():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module).should_receive('interpolate_context').replace_with(
        lambda hook_description, command, context: command
    )
    flexmock(module).should_receive('make_environment').and_return({})
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        ['foo'],
        output_log_level=logging.ANSWER,
        shell=True,
        environment={},
        working_directory='/working',
    )

    module.execute_hooks(
        [{'before': 'create', 'run': ['foo']}],
        umask=None,
        working_directory='/working',
        dry_run=False,
    )


def test_execute_hooks_with_dry_run_skips_commands():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module).should_receive('interpolate_context').replace_with(
        lambda hook_description, command, context: command
    )
    flexmock(module).should_receive('make_environment').and_return({})
    flexmock(module.borgmatic.execute).should_receive('execute_command').never()

    module.execute_hooks(
        [{'before': 'create', 'run': ['foo']}], umask=None, working_directory=None, dry_run=True
    )


def test_execute_hooks_with_empty_commands_does_not_raise():
    module.execute_hooks([], umask=None, working_directory=None, dry_run=True)


def test_execute_hooks_with_error_logs_as_error():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module).should_receive('interpolate_context').replace_with(
        lambda hook_description, command, context: command
    )
    flexmock(module).should_receive('make_environment').and_return({})
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        ['foo'],
        output_log_level=logging.ERROR,
        shell=True,
        environment={},
        working_directory=None,
    ).once()

    module.execute_hooks(
        [{'after': 'error', 'run': ['foo']}], umask=None, working_directory=None, dry_run=False
    )


def test_execute_hooks_with_before_or_after_raises():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module).should_receive('interpolate_context').never()
    flexmock(module).should_receive('make_environment').never()
    flexmock(module.borgmatic.execute).should_receive('execute_command').never()

    with pytest.raises(ValueError):
        module.execute_hooks(
            [
                {'erstwhile': 'create', 'run': ['foo']},
                {'erstwhile': 'create', 'run': ['bar', 'baz']},
            ],
            umask=None,
            working_directory=None,
            dry_run=False,
        )


def test_execute_hooks_without_commands_to_run_does_not_raise():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module).should_receive('interpolate_context').replace_with(
        lambda hook_description, command, context: command
    )
    flexmock(module).should_receive('make_environment').and_return({})

    for command in ('foo', 'bar'):
        flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
            [command],
            output_log_level=LOGGING_ANSWER,
            shell=True,
            environment={},
            working_directory=None,
        ).once()

    module.execute_hooks(
        [{'before': 'create', 'run': []}, {'before': 'create', 'run': ['foo', 'bar']}],
        umask=None,
        working_directory=None,
        dry_run=False,
    )


def test_before_after_hooks_calls_command_hooks():
    commands = [
        {'before': 'repository', 'run': ['foo', 'bar']},
        {'after': 'repository', 'run': ['baz']},
    ]
    flexmock(module).should_receive('filter_hooks').with_args(
        commands,
        before='action',
        action_names=['create'],
    ).and_return(flexmock()).once()
    flexmock(module).should_receive('filter_hooks').with_args(
        commands,
        after='action',
        action_names=['create'],
        state_names=['finish'],
    ).and_return(flexmock()).once()
    flexmock(module).should_receive('execute_hooks').twice()

    with module.Before_after_hooks(
        command_hooks=commands,
        before_after='action',
        umask=1234,
        working_directory='/working',
        dry_run=False,
        action_names=['create'],
        context1='stuff',
        context2='such',
    ):
        pass


def test_before_after_hooks_with_before_error_runs_after_hook_and_raises():
    commands = [
        {'before': 'repository', 'run': ['foo', 'bar']},
        {'after': 'repository', 'run': ['baz']},
    ]
    flexmock(module).should_receive('filter_hooks').with_args(
        commands,
        before='action',
        action_names=['create'],
    ).and_return(flexmock()).once()
    flexmock(module).should_receive('filter_hooks').with_args(
        commands,
        after='action',
        action_names=['create'],
        state_names=['fail'],
    ).and_return(flexmock()).once()
    flexmock(module).should_receive('execute_hooks').and_raise(OSError).and_return(None)
    flexmock(module).should_receive('considered_soft_failure').and_return(False)

    with pytest.raises(ValueError):
        with module.Before_after_hooks(
            command_hooks=commands,
            before_after='action',
            umask=1234,
            working_directory='/working',
            dry_run=False,
            action_names=['create'],
            context1='stuff',
            context2='such',
        ):
            assert False  # This should never get called.


def test_before_after_hooks_with_before_soft_failure_raises():
    commands = [
        {'before': 'repository', 'run': ['foo', 'bar']},
        {'after': 'repository', 'run': ['baz']},
    ]
    flexmock(module).should_receive('filter_hooks').with_args(
        commands,
        before='action',
        action_names=['create'],
    ).and_return(flexmock()).once()
    flexmock(module).should_receive('filter_hooks').with_args(
        commands,
        after='action',
        action_names=['create'],
        state_names=['finish'],
    ).never()
    flexmock(module).should_receive('execute_hooks').and_raise(OSError)
    flexmock(module).should_receive('considered_soft_failure').and_return(True)

    with pytest.raises(OSError):
        with module.Before_after_hooks(
            command_hooks=commands,
            before_after='action',
            umask=1234,
            working_directory='/working',
            dry_run=False,
            action_names=['create'],
            context1='stuff',
            context2='such',
        ):
            pass


def test_before_after_hooks_with_wrapped_code_error_runs_after_hook_and_raises():
    commands = [
        {'before': 'repository', 'run': ['foo', 'bar']},
        {'after': 'repository', 'run': ['baz']},
    ]
    flexmock(module).should_receive('filter_hooks').with_args(
        commands,
        before='action',
        action_names=['create'],
    ).and_return(flexmock()).once()
    flexmock(module).should_receive('filter_hooks').with_args(
        commands,
        after='action',
        action_names=['create'],
        state_names=['fail'],
    ).and_return(flexmock()).once()
    flexmock(module).should_receive('execute_hooks').twice()

    with pytest.raises(ValueError):
        with module.Before_after_hooks(
            command_hooks=commands,
            before_after='action',
            umask=1234,
            working_directory='/working',
            dry_run=False,
            action_names=['create'],
            context1='stuff',
            context2='such',
        ):
            raise ValueError()


def test_before_after_hooks_with_after_error_raises():
    commands = [
        {'before': 'repository', 'run': ['foo', 'bar']},
        {'after': 'repository', 'run': ['baz']},
    ]
    flexmock(module).should_receive('filter_hooks').with_args(
        commands,
        before='action',
        action_names=['create'],
    ).and_return(flexmock()).once()
    flexmock(module).should_receive('filter_hooks').with_args(
        commands,
        after='action',
        action_names=['create'],
        state_names=['finish'],
    ).and_return(flexmock()).once()
    flexmock(module).should_receive('execute_hooks').and_return(None).and_raise(OSError)
    flexmock(module).should_receive('considered_soft_failure').and_return(False)

    with pytest.raises(ValueError):
        with module.Before_after_hooks(
            command_hooks=commands,
            before_after='action',
            umask=1234,
            working_directory='/working',
            dry_run=False,
            action_names=['create'],
            context1='stuff',
            context2='such',
        ):
            pass


def test_before_after_hooks_with_after_soft_failure_raises():
    commands = [
        {'before': 'repository', 'run': ['foo', 'bar']},
        {'after': 'repository', 'run': ['baz']},
    ]
    flexmock(module).should_receive('filter_hooks').with_args(
        commands,
        before='action',
        action_names=['create'],
    ).and_return(flexmock()).once()
    flexmock(module).should_receive('filter_hooks').with_args(
        commands,
        after='action',
        action_names=['create'],
        state_names=['finish'],
    ).and_return(flexmock()).once()
    flexmock(module).should_receive('execute_hooks').and_return(None).and_raise(OSError)
    flexmock(module).should_receive('considered_soft_failure').and_return(True)

    with pytest.raises(OSError):
        with module.Before_after_hooks(
            command_hooks=commands,
            before_after='action',
            umask=1234,
            working_directory='/working',
            dry_run=False,
            action_names=['create'],
            context1='stuff',
            context2='such',
        ):
            pass


def test_considered_soft_failure_treats_soft_fail_exit_code_as_soft_fail():
    error = subprocess.CalledProcessError(module.SOFT_FAIL_EXIT_CODE, 'try again')

    assert module.considered_soft_failure(error)


def test_considered_soft_failure_does_not_treat_other_exit_code_as_soft_fail():
    error = subprocess.CalledProcessError(1, 'error')

    assert not module.considered_soft_failure(error)


def test_considered_soft_failure_does_not_treat_other_exception_type_as_soft_fail():
    assert not module.considered_soft_failure(Exception())


def test_considered_soft_failure_caches_results_and_only_logs_once():
    error = subprocess.CalledProcessError(module.SOFT_FAIL_EXIT_CODE, 'try again')
    flexmock(module.logger).should_receive('info').once()

    assert module.considered_soft_failure(error)
    assert module.considered_soft_failure(error)
