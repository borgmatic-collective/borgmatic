from flexmock import flexmock

from borgmatic import signals as module


def test_handle_signal_forwards_to_subprocesses():
    signal_number = 100
    frame = flexmock(f_back=flexmock(f_code=flexmock(co_name='something')))
    process_group = flexmock()
    flexmock(module.os).should_receive('getpgrp').and_return(process_group)
    flexmock(module.os).should_receive('killpg').with_args(process_group, signal_number).once()

    module.handle_signal(signal_number, frame)


def test_handle_signal_bails_on_recursion():
    signal_number = 100
    frame = flexmock(f_back=flexmock(f_code=flexmock(co_name='handle_signal')))
    flexmock(module.os).should_receive('getpgrp').never()
    flexmock(module.os).should_receive('killpg').never()

    module.handle_signal(signal_number, frame)


def test_handle_signal_exits_on_sigterm():
    signal_number = module.signal.SIGTERM
    frame = flexmock(f_back=flexmock(f_code=flexmock(co_name='something')))
    flexmock(module.os).should_receive('getpgrp').and_return(flexmock)
    flexmock(module.os).should_receive('killpg')
    flexmock(module.sys).should_receive('exit').with_args(
        module.EXIT_CODE_FROM_SIGNAL + signal_number
    ).once()

    module.handle_signal(signal_number, frame)


def test_configure_signals_installs_signal_handlers():
    flexmock(module.signal).should_receive('signal').at_least().once()

    module.configure_signals()
