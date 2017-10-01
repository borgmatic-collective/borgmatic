from flexmock import flexmock

from borgmatic.commands import hook as module


def test_exec_cmd():
    subprocess = flexmock(module.subprocess)
    subprocess.should_receive('check_call').with_args(':', shell=True).once()

    module.exec_cmd({'enable_hook': True, 'exec_hook': [':']})
