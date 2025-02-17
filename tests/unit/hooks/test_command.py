import logging
import subprocess

from flexmock import flexmock

from borgmatic.hooks import command as module


def test_interpolate_context_passes_through_command_without_variable():
    assert module.interpolate_context('pre-backup', 'ls', {'foo': 'bar'}) == 'ls'


def test_interpolate_context_passes_through_command_with_unknown_variable():
    command = 'ls {baz}'  # noqa: FS003

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


def test_execute_hook_invokes_each_command():
    flexmock(module).should_receive('interpolate_context').replace_with(
        lambda hook_description, command, context: command
    )
    flexmock(module).should_receive('make_environment').and_return({})
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        [':'],
        output_log_level=logging.WARNING,
        shell=True,
        environment={},
    ).once()

    module.execute_hook([':'], None, 'config.yaml', 'pre-backup', dry_run=False)


def test_execute_hook_with_multiple_commands_invokes_each_command():
    flexmock(module).should_receive('interpolate_context').replace_with(
        lambda hook_description, command, context: command
    )
    flexmock(module).should_receive('make_environment').and_return({})
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        [':'],
        output_log_level=logging.WARNING,
        shell=True,
        environment={},
    ).once()
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        ['true'],
        output_log_level=logging.WARNING,
        shell=True,
        environment={},
    ).once()

    module.execute_hook([':', 'true'], None, 'config.yaml', 'pre-backup', dry_run=False)


def test_execute_hook_with_umask_sets_that_umask():
    flexmock(module).should_receive('interpolate_context').replace_with(
        lambda hook_description, command, context: command
    )
    flexmock(module.os).should_receive('umask').with_args(0o77).and_return(0o22).once()
    flexmock(module.os).should_receive('umask').with_args(0o22).once()
    flexmock(module).should_receive('make_environment').and_return({})
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        [':'],
        output_log_level=logging.WARNING,
        shell=True,
        environment={},
    )

    module.execute_hook([':'], 77, 'config.yaml', 'pre-backup', dry_run=False)


def test_execute_hook_with_dry_run_skips_commands():
    flexmock(module).should_receive('interpolate_context').replace_with(
        lambda hook_description, command, context: command
    )
    flexmock(module).should_receive('make_environment').and_return({})
    flexmock(module.borgmatic.execute).should_receive('execute_command').never()

    module.execute_hook([':', 'true'], None, 'config.yaml', 'pre-backup', dry_run=True)


def test_execute_hook_with_empty_commands_does_not_raise():
    module.execute_hook([], None, 'config.yaml', 'post-backup', dry_run=False)


def test_execute_hook_on_error_logs_as_error():
    flexmock(module).should_receive('interpolate_context').replace_with(
        lambda hook_description, command, context: command
    )
    flexmock(module).should_receive('make_environment').and_return({})
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        [':'],
        output_log_level=logging.ERROR,
        shell=True,
        environment={},
    ).once()

    module.execute_hook([':'], None, 'config.yaml', 'on-error', dry_run=False)


def test_considered_soft_failure_treats_soft_fail_exit_code_as_soft_fail():
    error = subprocess.CalledProcessError(module.SOFT_FAIL_EXIT_CODE, 'try again')

    assert module.considered_soft_failure(error)


def test_considered_soft_failure_does_not_treat_other_exit_code_as_soft_fail():
    error = subprocess.CalledProcessError(1, 'error')

    assert not module.considered_soft_failure(error)


def test_considered_soft_failure_does_not_treat_other_exception_type_as_soft_fail():
    assert not module.considered_soft_failure(Exception())
