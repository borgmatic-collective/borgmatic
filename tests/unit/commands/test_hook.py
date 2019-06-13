import logging

from flexmock import flexmock

from borgmatic import hook as module


def test_execute_hook_invokes_each_command():
    flexmock(module.execute).should_receive('execute_command').with_args(
        [':'], output_log_level=logging.WARNING, shell=True
    ).once()

    module.execute_hook([':'], 'config.yaml', 'pre-backup', dry_run=False)


def test_execute_hook_with_multiple_commands_invokes_each_command():
    flexmock(module.execute).should_receive('execute_command').with_args(
        [':'], output_log_level=logging.WARNING, shell=True
    ).once()
    flexmock(module.execute).should_receive('execute_command').with_args(
        ['true'], output_log_level=logging.WARNING, shell=True
    ).once()

    module.execute_hook([':', 'true'], 'config.yaml', 'pre-backup', dry_run=False)


def test_execute_hook_with_dry_run_skips_commands():
    flexmock(module.execute).should_receive('execute_command').never()

    module.execute_hook([':', 'true'], 'config.yaml', 'pre-backup', dry_run=True)


def test_execute_hook_with_empty_commands_does_not_raise():
    module.execute_hook([], 'config.yaml', 'post-backup', dry_run=False)


def test_execute_hook_on_error_logs_as_error():
    flexmock(module.execute).should_receive('execute_command').with_args(
        [':'], output_log_level=logging.ERROR, shell=True
    ).once()

    module.execute_hook([':'], 'config.yaml', 'on-error', dry_run=False)
