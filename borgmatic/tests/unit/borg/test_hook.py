from flexmock import flexmock

from borgmatic.commands import hook as module


def test_execute_hook_invokes_each_command():
    subprocess = flexmock(module.subprocess)
    subprocess.should_receive('check_call').with_args(':', shell=True).once()

    module.execute_hook([':'])
