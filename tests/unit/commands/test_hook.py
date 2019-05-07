from flexmock import flexmock

from borgmatic.commands import hook as module


def test_execute_hook_invokes_each_command():
    subprocess = flexmock(module.subprocess)
    subprocess.should_receive('check_call').with_args(':', shell=True).once()

    module.execute_hook([':'], 'config.yaml', 'pre-backup', dry_run=False)


def test_execute_hook_with_multiple_commands_invokes_each_command():
    subprocess = flexmock(module.subprocess)
    subprocess.should_receive('check_call').with_args(':', shell=True).once()
    subprocess.should_receive('check_call').with_args('true', shell=True).once()

    module.execute_hook([':', 'true'], 'config.yaml', 'pre-backup', dry_run=False)


def test_execute_hook_with_dry_run_skips_commands():
    subprocess = flexmock(module.subprocess)
    subprocess.should_receive('check_call').never()

    module.execute_hook([':', 'true'], 'config.yaml', 'pre-backup', dry_run=True)


def test_execute_hook_with_empty_commands_does_not_raise():
    module.execute_hook([], 'config.yaml', 'post-backup', dry_run=False)
