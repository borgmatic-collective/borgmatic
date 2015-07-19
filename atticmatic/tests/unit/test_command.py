from flexmock import flexmock

from atticmatic import command as module


def test_load_backend_with_atticmatic_command_should_return_attic_backend():
    backend = flexmock()
    (
        flexmock(module).should_receive('import_module').with_args('atticmatic.backends.attic')
        .and_return(backend).once()
    )

    assert module.load_backend('atticmatic') == backend


def test_load_backend_with_unknown_command_should_return_attic_backend():
    backend = flexmock()
    (
        flexmock(module).should_receive('import_module').with_args('atticmatic.backends.attic')
        .and_return(backend).once()
    )

    assert module.load_backend('unknownmatic') == backend


def test_load_backend_with_borgmatic_command_should_return_borg_backend():
    backend = flexmock()
    (
        flexmock(module).should_receive('import_module').with_args('atticmatic.backends.borg')
        .and_return(backend).once()
    )

    assert module.load_backend('borgmatic') == backend
